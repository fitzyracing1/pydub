"""Regression tests for the fixes in the fitzyracing-pydub fork (360 Bench).

Run with:  python -m unittest test.test_fork_fixes -v
"""
import glob
import os
import random
import subprocess
import sys
import textwrap
import unittest
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "test", "data")


def _c_audioop():
    """Return the C audioop module (stdlib <= 3.12, audioop-lts on 3.13+) or None."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            import audioop
        except ImportError:
            return None
    if getattr(audioop, "__name__", "") != "audioop":
        return None
    return audioop


def _run(code):
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True,
    )


# The pydub operations below exercise every audioop function pydub calls:
# add, avg, bias, lin2lin, max, mul, ratecv, reverse, rms, tomono, tostereo.
PIPELINE = r"""
import hashlib, sys, warnings
warnings.simplefilter("ignore", DeprecationWarning)
from pydub import AudioSegment
import pydub.utils
seg = AudioSegment.from_wav(%(wav)r)[:1500]
out = []
for s in (seg, seg.set_sample_width(1), seg.set_sample_width(4)):
    mono = s.set_channels(1)
    stereo = mono.set_channels(2)
    work = (stereo.apply_gain(-3.5).overlay(stereo.reverse(), gain_during_overlay=-6)
                  .set_frame_rate(22050).fade_in(200).fade_out(300)
                  .pan(-0.4).remove_dc_offset())
    out.append(hashlib.sha1(work.raw_data).hexdigest())
    out.append("%%d %%d %%d" %% (work.rms, work.max, work.sample_width))
print(pydub.utils.audioop.__name__)
print("\n".join(out))
""" % {"wav": os.path.join(DATA, "test1.wav")}


class ImportOnPython313Tests(unittest.TestCase):
    """Upstream #725 / #863: `from pydub import AudioSegment` failed with
    ModuleNotFoundError: No module named 'pyaudioop' whenever the C audioop
    module was missing (always the case on Python 3.13+ without audioop-lts)."""

    def test_import_works_without_c_audioop(self):
        # Setting sys.modules["audioop"] = None makes `import audioop` raise
        # ImportError, i.e. Python 3.13+ without the audioop-lts wheel. This
        # simulates that situation on every Python version.
        r = _run("""
            import sys, wave  # stdlib wave imports audioop itself on 3.9/3.10
            sys.modules["audioop"] = None
            from pydub import AudioSegment
            import pydub.utils
            print(pydub.utils.audioop.__name__)
        """)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(r.stdout.strip().splitlines()[-1], "pydub.pyaudioop")

    def test_fallback_matches_c_audioop_end_to_end(self):
        if _c_audioop() is None:
            self.skipTest("no C audioop available to compare against")
        native = _run(PIPELINE)
        fallback = _run('import sys, wave; sys.modules["audioop"] = None\n' + PIPELINE)
        self.assertEqual(native.returncode, 0, native.stdout)
        self.assertEqual(fallback.returncode, 0, fallback.stdout)
        native_lines = native.stdout.strip().splitlines()
        fallback_lines = fallback.stdout.strip().splitlines()
        self.assertEqual(native_lines[0], "audioop")
        self.assertEqual(fallback_lines[0], "pydub.pyaudioop")
        self.assertEqual(native_lines[1:], fallback_lines[1:])

    @unittest.skipUnless(sys.version_info >= (3, 13), "audioop is in the stdlib before 3.13")
    def test_c_audioop_is_used_on_313_when_installed(self):
        # With the package installed, the audioop-lts dependency provides a C
        # `audioop` on 3.13+, so the slow pure-Python fallback is not used.
        if _c_audioop() is None:
            self.skipTest("audioop-lts not installed in this environment")
        r = _run("import pydub.utils; print(pydub.utils.audioop.__name__)")
        self.assertEqual(r.stdout.strip(), "audioop", r.stdout)


class PyAudioopDifferentialTests(unittest.TestCase):
    """The bundled pure-Python audioop must give the same bytes as the C one
    for every function pydub uses (it was Python 2 code and unusable before)."""

    @classmethod
    def setUpClass(cls):
        cls.c = _c_audioop()
        if cls.c is None:
            raise unittest.SkipTest("no C audioop available to compare against")
        from pydub import pyaudioop
        cls.py = pyaudioop
        rnd = random.Random(360)
        cls.frags = {}
        for size in (1, 2, 3, 4):
            n = 2 * 257  # even number of samples, so it is valid stereo too
            lo, hi = -(1 << (8 * size - 1)), (1 << (8 * size - 1)) - 1
            vals = [rnd.randint(lo, hi) for _ in range(n)] + [lo, hi, 0, -1]
            cls.frags[size] = b"".join(
                v.to_bytes(size, "little", signed=True) for v in vals)
            cls.frags[(size, "b")] = b"".join(
                rnd.randint(lo, hi).to_bytes(size, "little", signed=True)
                for _ in range(len(vals)))

    def same(self, name, *args):
        expected = getattr(self.c, name)(*args)
        actual = getattr(self.py, name)(*args)
        self.assertEqual(actual, expected, "%s%r" % (name, tuple(
            a if not isinstance(a, bytes) else "<%d bytes>" % len(a) for a in args)))

    def test_functions_used_by_pydub(self):
        for size in (1, 2, 3, 4):
            a, b = self.frags[size], self.frags[(size, "b")]
            self.same("add", a, b, size)
            self.same("avg", a, size)
            self.same("max", a, size)
            self.same("rms", a, size)
            self.same("reverse", a, size)
            self.same("minmax", a, size)
            for bias in (0, 1, -7, 1 << (8 * size - 2), -(1 << (8 * size - 1))):
                self.same("bias", a, size, bias)
            for factor in (0.0, 0.5, 1.0, 1.7, -1.3, 3.98):
                self.same("mul", a, size, factor)
            for f1, f2 in ((0.5, 0.5), (1.0, 0.0), (0.3, 1.2), (1, 1)):
                self.same("tomono", a, size, f1, f2)
                self.same("tostereo", a, size, f1, f2)
            for size2 in (1, 2, 3, 4):
                self.same("lin2lin", a, size, size2)

    def test_ratecv(self):
        for size in (1, 2, 3, 4):
            a = self.frags[size]
            for nch in (1, 2):
                for inrate, outrate in ((44100, 22050), (8000, 44100), (44100, 48000), (16000, 16000)):
                    for wA, wB in ((1, 0), (3, 1)):
                        self.same("ratecv", a, size, nch, inrate, outrate, None, wA, wB)
                        # streaming: state from the first chunk feeds the second
                        half = len(a) // 2 // (size * nch) * (size * nch)
                        _, st_c = self.c.ratecv(a[:half], size, nch, inrate, outrate, None, wA, wB)
                        _, st_p = self.py.ratecv(a[:half], size, nch, inrate, outrate, None, wA, wB)
                        self.assertEqual(st_p, st_c)
                        self.same("ratecv", a[half:], size, nch, inrate, outrate, st_c, wA, wB)


class NoInvalidEscapeSequenceTests(unittest.TestCase):
    """Upstream #801: regexes in pydub/utils.py used non-raw strings such as
    '\\(', which emit SyntaxWarning: invalid escape sequence on Python 3.12+."""

    def test_package_compiles_with_warnings_as_errors(self):
        files = sorted(glob.glob(os.path.join(ROOT, "pydub", "*.py")))
        self.assertTrue(files)
        for path in files:
            with open(path, "rb") as f:
                source = f.read()
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                try:
                    compile(source, path, "exec")
                except (SyntaxError, SyntaxWarning, DeprecationWarning) as e:
                    self.fail("%s: %s" % (os.path.relpath(path, ROOT), e))


if __name__ == "__main__":
    unittest.main()
