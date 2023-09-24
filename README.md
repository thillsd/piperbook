# PiperBook

Converts an epub to a directory of mp3s using [piper-tts](https://pypi.org/project/piper-tts/).

```bash
$ piperbook -s 1.0 -p 0.5 -v "en_US-ryan-high" test.epub author/test
19:55:27	MainThread	Chapters count: 5.
19:55:27	MainThread	Converting chapters 1 to 5.
19:55:35	worker-0	[✓] Wrote file 1_test_epub.mp3
19:55:39	worker-1	[✓] Wrote file 2_test_epub.mp3
19:58:12	worker-1	[✓] Wrote file 3_test_epub.mp3
19:59:27	worker-0	[✓] Wrote file 4_test_epub.mp3
20:00:54	worker-1	[✓] Wrote file 5_test_epub.mp3
20:00:56	MainThread	Cleaned up 0 from cache.
```

Supports voices models as listed on the [piper Readme](https://github.com/rhasspy/piper)


## Usage

```
usage: piperbook [-h] [--start START] [--end END] [-s SPEED] [-v VOICE] [-p PAUSE] [-c] [-j PROCESSES] epub audiobook-folder

Convert epub file to audiobook directory of mp3s

positional arguments:
  epub                  Epub file
  audiobook-folder      Destination folder for the mp3 files

options:
  -h, --help            show this help message and exit
  --start START         chapter to start from [default: 1]
  --end END             chapter to finish at [default: -1]
  -s SPEED, --speed SPEED
                        speed of the generated audio (lower is faster!) [default: 1.0]
  -v VOICE, --voice VOICE
                        voice to use for the generated audio. To see valid options, see the docs for piper [default: en_US-ryan-high]
  -p PAUSE, --pause PAUSE
                        length of pauses between sentences [default: 0.5]
  -c, --clobber         overwrite existing files [default: False]
  -j PROCESSES, --processes PROCESSES
                        number of piper processes to use. Keep this value low--piper is threaded already. [default: 2]
```

## Installation

Tested on Debian 12.

```bash
$ apt install python python-pip ffmpeg
$ pip install piperbook
$ piperbook --help
```

## Bugs

Chapter detection and naming is very imperfect. Patches welcome.


## FAQ

> I want m4b support

Either use [m4btool](https://github.com/sandreas/m4b-tool) or submit a patch.


## Credit

Epub chapterising logic stolen from [epub_to_audiobook](https://github.com/p0n1/epub_to_audiobook).