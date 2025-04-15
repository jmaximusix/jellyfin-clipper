from urllib.parse import urlencode
import argparse
import os
import dotenv
import math
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
import ffmpeg

dotenv.load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
DISCORD_LIMIT = 10e6


def download(
    id: str,
    output: Path,
    total_bitrate: int,
    codec: str = "h265",
    interval: Optional[tuple[int, int]] = None,
    size_limit: Optional[int] = None,
    audio_index=1,
) -> None:
    audio_bitrate = 128_000
    params = {
        "maxAudioChannels": 2,
        "TranscodingMaxAudioChannels": 2,
        "AudioBitrate": audio_bitrate,
        "VideoBitrate": total_bitrate - audio_bitrate,
        "VideoCodec": codec,
        "AudioCodec": "aac",
        "AudioStreamIndex": audio_index,
    }
    url = f"{BASE_URL}/Videos/{id}/main.m3u8?{urlencode(params)}"

    print(f"Downloading into: {output}")
    ffmpeg_input_args = {}
    ffmpeg_output_args = {}
    if interval:
        (start, duration) = interval
        ffmpeg_input_args["ss"] = start
        ffmpeg_input_args["t"] = duration
    if size_limit:
        ffmpeg_output_args["fs"] = size_limit
    (
        ffmpeg.input(
            url,
            **ffmpeg_input_args,
            headers=f'Authorization: MediaBrowser Token="{API_KEY}"\r\n',
        )
        .output(str(output), c="copy")
        .run()
    )


def valid_output_path(path) -> Path:
    path = Path(path)
    if not path.parent.exists():
        raise argparse.ArgumentTypeError(f"Invalid path: {path.parent} does not exist")
    return path


def timestamp_to_seconds(timestamp) -> int:
    if len(timestamp) == 2:
        timestamp = "00:00:" + timestamp
    if len(timestamp) == 5:
        timestamp = "00:" + timestamp
    datetime_obj = datetime.strptime(timestamp, "%H:%M:%S")
    seconds = datetime_obj.hour * 3600 + datetime_obj.minute * 60 + datetime_obj.second
    return seconds


def parse_clip_interval(interval) -> tuple[int, int]:
    if "+" in interval:
        startstr, durationstr = interval.split("+")
        start = timestamp_to_seconds(startstr)
        duration = timestamp_to_seconds(durationstr)
    elif "-" in interval:
        startstr, endstr = interval.split("-")
        start = timestamp_to_seconds(startstr)
        end = timestamp_to_seconds(endstr)
        duration = end - start
    else:
        raise argparse.ArgumentTypeError(
            "Invalid clip interval. Must be (HH:)MM:SS-(HH:)MM:SS or (HH:)MM:SS+(MM:)SS"
        )
    return start, duration


def parse_bitrate(bitrate) -> Union[int, str]:
    if bitrate == "discord":
        return "discord"
    if bitrate[-1] in "kK":
        return int(bitrate[:-1]) * 1_000
    elif bitrate[-1] == "M":
        return int(bitrate[:-1]) * 1_000_000
    else:
        return int(bitrate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="The id of the video to download")
    parser.add_argument(
        "--clip",
        type=parse_clip_interval,
        help="Clip the specified interval",
        default=None,
    )
    parser.add_argument("output", type=valid_output_path, help="The output file")
    parser.add_argument(
        "--audio-index",
        help="The index of the audio stream to download",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--bitrate",
        help="The target bitrate of the video in bits per second",
        type=parse_bitrate,
        default=10_000_000,
    )
    parser.add_argument(
        "--codec",
        help="The codec to use for the video",
        choices=["h264", "h265"],
        default="h265",
    )
    args = parser.parse_args()
    if args.bitrate == "discord":
        assert args.clip, "Can only use discord bitrate with clips"
        duration = args.clip[1]
        assert duration + 1 in range(
            120
        ), "Can only use discord bitrate with clips of at most 120 seconds"
        total_bitrate = math.floor(DISCORD_LIMIT / duration * 8 / 1000) * 1000
        size_limit = DISCORD_LIMIT
    else:
        total_bitrate = args.bitrate
        size_limit = None
    download(
        args.id,
        args.output,
        total_bitrate,
        codec=args.codec,
        interval=args.clip,
        size_limit=size_limit,
        audio_index=args.audio_index,
    )
