# Getting started

## Install

```
pip uninstall -y pydub && pip install fitzyracing-pydub
```

The import name is still `pydub`. ffmpeg is needed for non-WAV formats (see README "Getting ffmpeg set up").

## Usage

`from pydub import AudioSegment`. The full API is in `API.markdown`, with examples in the README "Quickstart" and "Example Use" sections.

## Develop and test

```
pip install -e .
python -m unittest discover -s test   # or: pytest test/
```
