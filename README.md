# PiperBook

Converts an epub to a directory of mp3s using [piper-tts](https://pypi.org/project/piper-tts/).

```bash
$ piperbook "Brandon, Sanderson - The Emperor's Soul.epub" "Sanderson, Brandon/The Emperor's Soul"
$ tree "Sanderson, Brandon/The Emperor's Soul"
.
├── 01_by_Brandon_Sanderson_Ebook_edition_note_If_you_purchased_a.mp3
├── 02_For_Lucie_Tuan_and_Sherry_Wang_who_provided_inspiration.mp3
├── 03_Prologue.mp3
├── 04_Gaotona_ran_his_fingers_across_the_thick_canvas_inspecting.mp3
├── 05_Day_Two_Shai_pressed_her_fingernail_into_one_of_the_stone_bl.mp3
├── 06_Day_Three_The_next_daybathed_well_fed_and_well_rested_for.mp3
├── 07_Day_Five_Work_she_did_Shai_began_digging_through_accounts_o.mp3
├── 08_Day_Twelve_Shai_pressed_her_stamp_down_on_the_tabletop_As_a.mp3
├── 09_Day_Seventeen_A_cool_breeze_laden_with_unfamiliar_spices_cre.mp3
...
```

Supports voices models as listed on the [piper Readme](https://github.com/rhasspy/piper)


## Usage

```
usage: piperbook [-h] [--start START] [--end END] [--speed SPEED] [--voice VOICE] [--pause PAUSE] epub audiobook-folder

Convert epub file to audiobook directory of mp3s

positional arguments:
  epub              Epub file
  audiobook-folder  Destination folder for the mp3 files

options:
  -h, --help        show this help message and exit
  --start START     chapter to start from [default: 1]
  --end END         chapter to finish at [default: -1]
  --speed SPEED     speed of the generated audio (lower is faster!) [default: 1]
  --voice VOICE     voice to use for the generated audio. To see valid options, see the docs for piper [default: en_US-joe-medium]
  --pause PAUSE     length of pauses between sentences [default: 0.5]
```

## Installation

```bash
$ apt install python python-pip ffmpeg
$ git clone https://github.com/thillsd/piperbook && cd piperbook
$ pip install .
$ piperbook --help
```

## Bugs

Chapter detection and naming is very imperfect. Patches welcome.


## TODO

- m4b format support.
- Use piper more intelligently


## Credit

Epub chapterising logic stolen from [epub_to_audiobook](https://github.com/p0n1/epub_to_audiobook).