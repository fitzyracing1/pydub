# fitzyracing-pydub

> Part of **[360 Bench](https://github.com/fitzyracing1/360-bench)**, tested fixes for abandoned PyPI packages.

Pydub lets you do stuff to audio in a way that isn't stupid.

[![PyPI](https://img.shields.io/pypi/v/fitzyracing-pydub.svg)](https://pypi.org/project/fitzyracing-pydub/)

> **This is a fork of [pydub](https://github.com/jiaaro/pydub)
> by [James Robert (jiaaro)](https://github.com/jiaaro)** and its contributors, published as a
> drop-in replacement that works on Python 3.13 and newer. The upstream package has not been
> released since 0.25.1 (March 2021); on Python 3.13+ `from pydub import AudioSegment`
> crashes, and the pull requests that fix it have not been merged. The import name is still
> `pydub`, so no code changes are needed. All credit for the original library goes to its
> author and contributors; it remains available under the same MIT license.
>
> Upstream is not completely dormant (a typo fix was merged in March 2026), so if a fixed
> `pydub` release appears on PyPI, prefer it and switch back.


## What's fixed in this fork

Based on upstream `master` at [`103e339`](https://github.com/jiaaro/pydub/commit/103e339d3bc7a9a58a9f1de65f7d8074659b5f5a)
(0.25.1 plus the small fixes the maintainer merged after that release, which were never published).
The API is unchanged.

- **`from pydub import AudioSegment` works on Python 3.13 and 3.14.** Python 3.13 removed the
  `audioop` module from the standard library, so pydub fell back to its bundled pure-Python
  copy, but did so with `import pyaudioop`, an absolute import that can never find a module
  living inside the `pydub` package. The result was
  `ModuleNotFoundError: No module named 'pyaudioop'`. This fork:
  - depends on [`audioop-lts`](https://pypi.org/project/audioop-lts/) (the same C module,
    packaged separately) on Python 3.13+ only, via `audioop-lts; python_version>='3.13'`.
    Nothing extra is installed on 3.12 and older, where `audioop` is still in the stdlib;
  - fixes the fallback import (`from . import pyaudioop as audioop`);
  - makes the fallback actually usable. `pydub/pyaudioop.py` was Python 2 code (`buffer()`,
    `.next()`, float indexes) and failed on the first call. It is replaced by the Python 3
    rewrite from unmerged upstream PR [#881](https://github.com/jiaaro/pydub/pull/881) by
    [@iammcoding](https://github.com/iammcoding). The fork's tests check that it gives
    byte-for-byte the same output as the C module for every `audioop` function pydub uses
    (`add`, `avg`, `bias`, `lin2lin`, `max`, `mul`, `ratecv`, `reverse`, `rms`, `tomono`,
    `tostereo`) at sample widths 1 to 4. It is only used if no C `audioop` can be imported,
    and it is much slower (the full test suite takes about 9 minutes with it, against about
    25 seconds with `audioop-lts`).

  Upstream issues: [#725](https://github.com/jiaaro/pydub/issues/725),
  [#839](https://github.com/jiaaro/pydub/issues/839),
  [#863](https://github.com/jiaaro/pydub/issues/863),
  [#867](https://github.com/jiaaro/pydub/issues/867);
  unmerged PRs: [#881](https://github.com/jiaaro/pydub/pull/881),
  [#883](https://github.com/jiaaro/pydub/pull/883).
- **No more `SyntaxWarning: invalid escape sequence '\('`** on Python 3.12+ from the regexes in
  `pydub/utils.py` (they are raw strings now). Upstream fixed this on `master` in
  [`5658398`](https://github.com/jiaaro/pydub/commit/5658398) but never released it; the fork's
  tests compile every module with warnings turned into errors so it can't come back.
  Upstream issue: [#801](https://github.com/jiaaro/pydub/issues/801).
- **Unreleased upstream fixes are now published**, because the fork is built from `master`:
  temporary files are deleted when `export()` fails
  ([#665](https://github.com/jiaaro/pydub/pull/665)), `mediainfo_json()` no longer crashes on
  empty ffprobe output ([#652](https://github.com/jiaaro/pydub/pull/652)), file handles opened
  passed in as `BufferedReader` objects are closed after reading ([#687](https://github.com/jiaaro/pydub/pull/687)), and `append()` with
  a crossfade builds its result in memory instead of a temp file
  ([#686](https://github.com/jiaaro/pydub/pull/686)).
- **Packaging:** `pyproject.toml` replaces `setup.py`; Python 3.9+ (Python 2 and 3.8 are no longer
  supported. If you are stuck on those, keep upstream `pydub==0.25.1`, which works there).
  The upstream test suite's two `assertEquals` calls (removed in Python 3.12) were changed to
  `assertEqual`.

PR [#883](https://github.com/jiaaro/pydub/pull/883) (a much larger "revival" of pydub) was
reviewed too. This fork deliberately takes only the Python 3.13 fix and leaves out #883's
behaviour changes (new exceptions, ffmpeg piping, encoder fallbacks), so upgrading is low-risk.


## Install

```bash
pip install fitzyracing-pydub
```

You still need ffmpeg or libav for anything other than WAV (see [Dependencies](#dependencies)).

### Switching from `pydub`

This distribution installs the same `pydub` import package as the original, so your code keeps
doing `from pydub import AudioSegment`. **Uninstall the original first**, then install the fork:

```bash
pip uninstall -y pydub
pip install fitzyracing-pydub
```

The order matters. Both distributions own the same files, so if you install the fork first and
uninstall `pydub` afterwards, pip deletes the shared `pydub/` files and the import breaks. If
that happens, run `pip install --force-reinstall --no-deps fitzyracing-pydub`.

In `requirements.txt` / `pyproject.toml`, replace `pydub` with `fitzyracing-pydub`.

### If you get pydub through another package

pip has no equivalent of npm's `overrides`: it cannot replace a dependency with a differently
named package. If one of your dependencies requires `pydub`, pip will keep installing the
original. So you install the fork alongside it, and since both provide the same `pydub` import
name you then have to remove the original:

```bash
pip install fitzyracing-pydub
pip uninstall -y pydub
pip install --force-reinstall --no-deps fitzyracing-pydub   # restore the files the uninstall removed
```

Afterwards `pip check` reports `<package> requires pydub, which is not installed`; that is
expected. Any later `pip install`/`--upgrade` that pulls `pydub` back in will overwrite the fork's
files, so repeat the steps above after upgrading the package that depends on it.

**uv users** can do this properly with an override that drops the original:

```toml
# pyproject.toml
[project]
dependencies = ["fitzyracing-pydub", "...the package that depends on pydub..."]

[tool.uv]
override-dependencies = ["pydub; sys_platform == 'never'"]
```

(or `uv pip install --override overrides.txt ...` with that same line in `overrides.txt`).



**Stuff you might be looking for**:
 - [Installing Pydub](https://github.com/jiaaro/pydub#installation)
 - [API Documentation](https://github.com/jiaaro/pydub/blob/master/API.markdown)
 - [Dependencies](https://github.com/jiaaro/pydub#dependencies)
 - [Playback](https://github.com/jiaaro/pydub#playback)
 - [Setting up ffmpeg](https://github.com/jiaaro/pydub#getting-ffmpeg-set-up)
 - [Questions/Bugs](https://github.com/jiaaro/pydub#bugs--questions)
 

##  Quickstart

Open a WAV file

```python
from pydub import AudioSegment

song = AudioSegment.from_wav("never_gonna_give_you_up.wav")
```

...or a mp3

```python
song = AudioSegment.from_mp3("never_gonna_give_you_up.mp3")
```

... or an ogg, or flv, or [anything else ffmpeg supports](http://www.ffmpeg.org/general.html#File-Formats)

```python
ogg_version = AudioSegment.from_ogg("never_gonna_give_you_up.ogg")
flv_version = AudioSegment.from_flv("never_gonna_give_you_up.flv")

mp4_version = AudioSegment.from_file("never_gonna_give_you_up.mp4", "mp4")
wma_version = AudioSegment.from_file("never_gonna_give_you_up.wma", "wma")
aac_version = AudioSegment.from_file("never_gonna_give_you_up.aiff", "aac")
```

Slice audio:

```python
# pydub does things in milliseconds
ten_seconds = 10 * 1000

first_10_seconds = song[:ten_seconds]

last_5_seconds = song[-5000:]
```

Make the beginning louder and the end quieter

```python
# boost volume by 6dB
beginning = first_10_seconds + 6

# reduce volume by 3dB
end = last_5_seconds - 3
```

Concatenate audio (add one file to the end of another)

```python
without_the_middle = beginning + end
```

How long is it?

```python
without_the_middle.duration_seconds == 15.0
```

AudioSegments are immutable

```python
# song is not modified
backwards = song.reverse()
```

Crossfade (again, beginning and end are not modified)

```python
# 1.5 second crossfade
with_style = beginning.append(end, crossfade=1500)
```

Repeat

```python
# repeat the clip twice
do_it_over = with_style * 2
```

Fade (note that you can chain operations because everything returns
an AudioSegment)

```python
# 2 sec fade in, 3 sec fade out
awesome = do_it_over.fade_in(2000).fade_out(3000)
```

Save the results (again whatever ffmpeg supports)

```python
awesome.export("mashup.mp3", format="mp3")
```

Save the results with tags (metadata)

```python
awesome.export("mashup.mp3", format="mp3", tags={'artist': 'Various artists', 'album': 'Best of 2011', 'comments': 'This album is awesome!'})
```

You can pass an optional bitrate argument to export using any syntax ffmpeg 
supports.

```python
awesome.export("mashup.mp3", format="mp3", bitrate="192k")
```

Any further arguments supported by ffmpeg can be passed as a list in a 
'parameters' argument, with switch first, argument second. Note that no 
validation takes place on these parameters, and you may be limited by what 
your particular build of ffmpeg/avlib supports.

```python
# Use preset mp3 quality 0 (equivalent to lame V0)
awesome.export("mashup.mp3", format="mp3", parameters=["-q:a", "0"])

# Mix down to two channels and set hard output volume
awesome.export("mashup.mp3", format="mp3", parameters=["-ac", "2", "-vol", "150"])
```

## Debugging

Most issues people run into are related to converting between formats using
ffmpeg/avlib. Pydub provides a logger that outputs the subprocess calls to 
help you track down issues:

```python
>>> import logging

>>> l = logging.getLogger("pydub.converter")
>>> l.setLevel(logging.DEBUG)
>>> l.addHandler(logging.StreamHandler())

>>> AudioSegment.from_file("./test/data/test1.mp3")
subprocess.call(['ffmpeg', '-y', '-i', '/var/folders/71/42k8g72x4pq09tfp920d033r0000gn/T/tmpeZTgMy', '-vn', '-f', 'wav', '/var/folders/71/42k8g72x4pq09tfp920d033r0000gn/T/tmpK5aLcZ'])
<pydub.audio_segment.AudioSegment object at 0x101b43e10>
```

Don't worry about the temporary files used in the conversion. They're cleaned up 
automatically.

## Bugs & Questions

Problems specific to this fork (installation, Python 3.13+): please use the
[fork's issue tracker](https://github.com/fitzyracing1/pydub/issues).
For everything else, the upstream project's notes below still apply.

You can file bugs in our [github issues tracker](https://github.com/jiaaro/pydub/issues), 
and ask any technical questions on 
[Stack Overflow using the pydub tag](http://stackoverflow.com/questions/ask?tags=pydub). 
We keep an eye on both.

## Installation

Installing pydub is easy, but don't forget to install ffmpeg/avlib (the next section in this doc)

    pip install fitzyracing-pydub

See [Switching from `pydub`](#switching-from-pydub) above if the original is already installed.

## Dependencies

You can open and save WAV files with pure python. For opening and saving non-wav 
files – like mp3 – you'll need [ffmpeg](http://www.ffmpeg.org/) or 
[libav](http://libav.org/).

### Playback

You can play audio if you have one of these installed (simpleaudio _strongly_ recommended, even if you are installing ffmpeg/libav):

 - [simpleaudio](https://simpleaudio.readthedocs.io/en/latest/)
 - [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/docs/#)
 - ffplay (usually bundled with ffmpeg, see the next section)
 - avplay (usually bundled with libav, see the next section)
 
```python
from pydub import AudioSegment
from pydub.playback import play

sound = AudioSegment.from_file("mysound.wav", format="wav")
play(sound)
```

## Getting ffmpeg set up

You may use **libav or ffmpeg**.

Mac (using [homebrew](http://brew.sh)):

```bash
# libav
brew install libav

####    OR    #####

# ffmpeg
brew install ffmpeg
```

Linux (using aptitude):

```bash
# libav
apt-get install libav-tools libavcodec-extra

####    OR    #####

# ffmpeg
apt-get install ffmpeg libavcodec-extra
```

Windows:

1. Download and extract libav from [Windows binaries provided here](http://builds.libav.org/windows/).
2. Add the libav `/bin` folder to your PATH envvar
3. `pip install fitzyracing-pydub`

## Important Notes

`AudioSegment` objects are [immutable](http://www.devshed.com/c/a/Python/String-and-List-Python-Object-Types/1/)


### Ogg exporting and default codecs

The Ogg specification ([http://tools.ietf.org/html/rfc5334](rfc5334)) does not specify
the codec to use, this choice is left up to the user. Vorbis and Theora are just
some of a number of potential codecs (see page 3 of the rfc) that can be used for the
encapsulated data.

When no codec is specified exporting to `ogg` will _default_ to using `vorbis`
as a convenience. That is:

```python
from pydub import AudioSegment
song = AudioSegment.from_mp3("test/data/test1.mp3")
song.export("out.ogg", format="ogg")  # Is the same as:
song.export("out.ogg", format="ogg", codec="libvorbis")
```

## Example Use

Suppose you have a directory filled with *mp4* and *flv* videos and you want to convert all of them to *mp3* so you can listen to  them on your mp3 player.

```python
import os
import glob
from pydub import AudioSegment

video_dir = '/home/johndoe/downloaded_videos/'  # Path where the videos are located
extension_list = ('*.mp4', '*.flv')

os.chdir(video_dir)
for extension in extension_list:
    for video in glob.glob(extension):
        mp3_filename = os.path.splitext(os.path.basename(video))[0] + '.mp3'
        AudioSegment.from_file(video).export(mp3_filename, format='mp3')
```

### How about another example?

```python
from glob import glob
from pydub import AudioSegment

playlist_songs = [AudioSegment.from_mp3(mp3_file) for mp3_file in glob("*.mp3")]

first_song = playlist_songs.pop(0)

# let's just include the first 30 seconds of the first song (slicing
# is done by milliseconds)
beginning_of_song = first_song[:30*1000]

playlist = beginning_of_song
for song in playlist_songs:

    # We don't want an abrupt stop at the end, so let's do a 10 second crossfades
    playlist = playlist.append(song, crossfade=(10 * 1000))

# let's fade out the end of the last song
playlist = playlist.fade_out(30)

# hmm I wonder how long it is... ( len(audio_segment) returns milliseconds )
playlist_length = len(playlist) / (1000*60)

# lets save it!
with open("%s_minute_playlist.mp3" % playlist_length, 'wb') as out_f:
    playlist.export(out_f, format='mp3')
```

## Security contact

To report a security vulnerability in this fork, please use
[GitHub private vulnerability reporting](https://github.com/fitzyracing1/pydub/security/advisories/new)
rather than a public issue.

## Credits

pydub was created by [James Robert](https://github.com/jiaaro); see [AUTHORS](./AUTHORS) for the
many contributors. The pure-Python `audioop` rewrite in this fork comes from
[@iammcoding](https://github.com/iammcoding)'s upstream PR
[#881](https://github.com/jiaaro/pydub/pull/881), and the packaging approach (an `audioop-lts`
dependency with a Python-version marker) follows [@keithadler](https://github.com/keithadler)'s
PR [#883](https://github.com/jiaaro/pydub/pull/883) and the community workaround in
[#725](https://github.com/jiaaro/pydub/issues/725). Fork maintained by
[Joshua Almeida](https://github.com/fitzyracing1).

## License ([MIT License](http://opensource.org/licenses/mit-license.php))

[MIT](./LICENSE). The original license and copyright notice are retained unchanged; fork
changes are released under the same license.

Original project: https://github.com/jiaaro/pydub

Copyright © 2011 James Robert, http://jiaaro.com

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


## Documentation

- In-repo docs: [docs/](docs/index.md)
- Wiki: [https://github.com/fitzyracing1/pydub/wiki](https://github.com/fitzyracing1/pydub/wiki)
