# fitzyracing-pydub

`fitzyracing-pydub` is a drop-in fork of [pydub](https://github.com/jiaaro/pydub) and part of [360 Bench](https://github.com/fitzyracing1/360-bench). It is based on upstream upstream `master` at `103e339` (0.25.1 plus unreleased fixes), and the API is unchanged. All credit for the original library goes to its authors and contributors.

## What the fork fixes (summary of [README.markdown](../README.markdown))

- `from pydub import AudioSegment` works on Python 3.13 and 3.14. It depends on `audioop-lts` on 3.13+, and the bundled `pyaudioop` fallback is fixed.
- No more `SyntaxWarning: invalid escape sequence` on Python 3.12+.
- Unreleased upstream fixes are published.
- Packaging moved to `pyproject.toml`. Requires Python 3.9+.

The full details and links to the upstream issues are in [README.markdown](../README.markdown).

Pages: [Getting started](getting-started.md) · [Architecture](architecture.md)

This repo has no CI workflow.

## License

MIT. The original notice is kept: Copyright (c) 2011 James Robert, http://jiaaro.com.
Modifications: Copyright (c) 2026 Joshua Almeida.
