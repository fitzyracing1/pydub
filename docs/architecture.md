# Architecture

| Path | Role |
|---|---|
| `pydub/audio_segment.py` | `AudioSegment` |
| `pydub/effects.py, scipy_effects.py, silence.py, generators.py` | effects and generators |
| `pydub/utils.py, playback.py` | ffmpeg discovery, playback |
| `pydub/pyaudioop.py` | pure-Python audioop fallback |
| `test/` | test.py, test_fork_fixes.py, data/ |


