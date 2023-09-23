#!/usr/bin/env python3
import atexit
import glob
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from multiprocessing import cpu_count
from typing import List, Tuple

import appdirs
import ebooklib
import typed_argparse as tap
from bs4 import BeautifulSoup
from ebooklib import epub
from loguru import logger
from mutagen.easyid3 import EasyID3

logger.remove(0)
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green>\t{thread.name}\t{message}",
    level="INFO",
)


@dataclass
class RecordingJob:
    text: str
    title: str
    author: str
    book_title: str
    chapter_number: int

    file_name_prefix: str
    cache_dir: str
    output_folder: str

    voice: str
    speed: str
    pause: str

    wav_filename: str = field(init=False)
    mp3_filename: str = field(init=False)

    def __post_init__(self):
        self.wav_filename = os.path.join(self.cache_dir, self.file_name_prefix + ".wav")
        self.mp3_filename = os.path.join(self.output_folder,
                                         self.file_name_prefix + ".mp3")


def sanitize_title(title: str) -> str:
    sanitized_title = re.sub(r"[^\w\s]", "", title, flags=re.UNICODE)
    sanitized_title = re.sub(r"\s+", "_", sanitized_title.strip())
    return sanitized_title


def extract_chapters(epub_book: epub.EpubBook) -> List[Tuple[str, str]]:
    chapters = []
    for item in epub_book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        content = item.get_content()
        soup = BeautifulSoup(content, features="lxml")
        title = soup.title.string if soup.title else ""
        raw = soup.get_text(strip=False)
        logger.debug(f"Raw text: <{raw[:]}>")

        # Replace excessive whitespaces and newline characters based on the mode
        cleaned_text = re.sub(r"\s+", " ", raw.strip())
        logger.info(f"Cleaned text step 1: <{cleaned_text[:100]}>")

        # fill in the title if it's missing
        if not title:
            title = cleaned_text[:60]
        logger.debug(f"Raw title: <{title}>")
        title = sanitize_title(title)
        logger.info(f"Sanitized title: <{title}>")

        chapters.append((title, cleaned_text))

    return chapters


def epub_to_audiobook(
    input_file: str,
    output_folder: str,
    voice: str,
    speed: str,
    pause: str,
    chapter_start: int,
    chapter_end: int,
    cache_dir: str,
) -> None:
    book = epub.read_epub(input_file)
    chapters = extract_chapters(book)

    os.makedirs(output_folder, exist_ok=True)

    # Get the book title and author from metadata or use fallback values
    book_title = "Untitled"
    author = "Unknown"
    if book.get_metadata("DC", "title"):
        book_title = book.get_metadata("DC", "title")[0][0]
    if book.get_metadata("DC", "creator"):
        author = book.get_metadata("DC", "creator")[0][0]

    # Filter out empty or very short chapters
    chapters = [(title, text) for title, text in chapters if text.strip()]

    logger.info(f"Chapters count: {len(chapters)}.")

    # Check chapter start and end args
    if chapter_start < 1 or chapter_start > len(chapters):
        raise ValueError(
            f"Chapter start index {chapter_start} is out of range. Check your input.")
    if chapter_end < -1 or chapter_end > len(chapters):
        raise ValueError(
            f"Chapter end index {chapter_end} is out of range. Check your input.")
    if chapter_end == -1:
        chapter_end = len(chapters)
    if chapter_start > chapter_end:
        raise ValueError(
            f"Chapter start index {chapter_start} is larger than chapter end index {chapter_end}. Check your input."
        )

    logger.info(f"Converting chapters {chapter_start} to {chapter_end}.")

    # Calculate the number of digits needed for zero padding the file name
    max_digits = int(math.log10(len(chapters))) + 1

    tts_queue = queue.Queue()
    for idx, (title, text) in enumerate(chapters, start=1):
        if idx < chapter_start:
            continue
        if idx > chapter_end:
            break

        padded_chap_number = str(idx).zfill(max_digits)
        file_name = f"{padded_chap_number}_{title}"

        tts_queue.put(
            RecordingJob(
                title=title,
                text=text,
                author=author,
                file_name_prefix=file_name,
                output_folder=output_folder,
                cache_dir=cache_dir,
                book_title=book_title,
                chapter_number=idx,
                voice=voice,
                speed=speed,
                pause=pause,
            ))

    pool = [
        threading.Thread(target=worker,
                         args=(tts_queue, ),
                         daemon=True,
                         name=f"worker-{i}") for i in range(0, cpu_count())
    ]
    for thread in pool:
        thread.start()

    tts_queue.join()


def worker(tts_queue: queue.Queue) -> None:
    while True:
        try:
            job: RecordingJob = tts_queue.get(block=False)
        except queue.Empty:
            return
        try:
            convert_chapter(job)
        except Exception as e:
            logger.error(
                f"Failed to convert chapter {job.chapter_number} to speech. Error: {e}")
        else:
            logger.info(f"[✓] Wrote file {job.mp3_filename}")
        finally:
            tts_queue.task_done()


def convert_chapter(job: RecordingJob) -> None:
    subprocess.run(
        [
            "piper",
            "--output_file",
            job.wav_filename,
            "--model",
            os.path.join(job.cache_dir, job.voice + ".onnx"),
            "--length-scale",
            job.speed,
            "--sentence-silence",
            job.pause,
        ],
        input=job.text.encode("utf-8"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.call(
        [
            "ffmpeg",
            "-i",
            job.wav_filename,
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "64k",
            job.mp3_filename,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    os.remove(job.wav_filename)

    tag_file(job)


def tag_file(job: RecordingJob) -> None:
    tag = EasyID3(job.mp3_filename)
    tag["artist"] = job.author
    tag["title"] = job.title
    tag["album"] = job.book_title
    tag["tracknumber"] = str(job.chapter_number)
    tag.save(v2_version=3)


class Args(tap.TypedArgs):
    epub: str = tap.arg(
        positional=True,
        help="Epub file",
    )
    audiobook_folder: str = tap.arg(
        positional=True,
        help="Destination folder for the mp3 files",
    )
    start: int = tap.arg(
        default=1,
        help="chapter to start from",
    )
    end: int = tap.arg(
        default=-1,
        help="chapter to finish at",
    )
    speed: str = tap.arg(
        default="1",
        help="speed of the generated audio (lower is faster!)",
    )
    voice: str = tap.arg(
        default="en_US-joe-medium",
        help=
        "voice to use for the generated audio. To see valid options, see the docs for piper",
    )
    pause: str = tap.arg(
        default="0.5",
        help="length of pauses between sentences",
    )


def main(args: Args) -> None:
    for executable in ("piper", "ffmpeg"):
        if not shutil.which(executable):
            logger.error(
                f"{executable} not found in PATH. Please install {executable} and try again."
            )
            sys.exit(1)

    # make cache directory if it doesn't exist
    cache_dir = appdirs.user_cache_dir("piperbook")
    os.makedirs(cache_dir, exist_ok=True)

    # set hook to clean up wav files on fatal error
    def cleanup():
        temp_files = glob.glob(os.path.join(cache_dir, "*wav"))
        logger.info(f"Cleaning up {len(temp_files)} temporary wav files.")
        for f in temp_files:
            os.remove(f)

    atexit.register(cleanup)

    # check piper has downloaded the model
    onnx_model = os.path.join(cache_dir, args.voice + ".onnx")
    onnx_model_json = os.path.join(cache_dir, args.voice + ".onnx.json")
    if not os.path.exists(onnx_model) or not os.path.exists(onnx_model_json):
        logger.error(f"Model {args.voice} not found. Downloading.")
        subprocess.run(
            [
                "piper", "-m", args.voice, "--data-dir", cache_dir, "--download-dir",
                cache_dir
            ],
            input=b"y",
            stdout=subprocess.DEVNULL,
        )  # Piper will download on first run. Bad Things happen if 8 processes try to download at once.

    epub_to_audiobook(
        input_file=args.epub,
        output_folder=args.audiobook_folder,
        chapter_start=args.start,
        chapter_end=args.end,
        voice=args.voice,
        speed=args.speed,
        pause=args.pause,
        cache_dir=cache_dir,
    )


app = tap.Parser(
    Args, description="Convert epub file to audiobook directory of mp3s").bind(main)
