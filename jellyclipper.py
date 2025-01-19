from urllib.parse import urlencode
import argparse
import os
import dotenv
import subprocess
import math
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import ffmpeg

dotenv.load_dotenv()

API_KEY = os.getenv("API_KEY")
print(f"Using API key {API_KEY}")
BASE_URL = os.getenv("BASE_URL")
print(f"Using BASE_URL {BASE_URL}")
DISCORD_LIMIT = 25_000_000


def timestamp_to_seconds(timestamp):
    if timestamp.length == 5:
        timestamp = "00:" + timestamp
    datetime_obj = datetime.strptime(timestamp, "%H:%M:%S")
    seconds = datetime_obj.hour * 3600 + datetime_obj.minute * 60 + datetime_obj.second
    return seconds


def valid_output_path(path):
    path = Path(path)
    if not path.parent.exists():
        raise argparse.ArgumentTypeError(f"Invalid path: {path.parent} does not exist")
    return path


def parse_clip_interval(interval):
    if "+" in interval:
        startstr, durationstr = interval.split("+")
        start = timestamp_to_seconds(startstr)
        duration = timestamp_to_seconds(durationstr)
    elif "-" in interval:
        startstr, endstr = interval.split("-")
        start = timestamp_to_seconds(start)
        end = timestamp_to_seconds(endstr)
        duration = end - start
    else:
        raise argparse.ArgumentTypeError(
            "Invalid clip interval. Must be (HH:)MM:SS-(HH:)MM:SS or (HH:)MM:SS+(MM:)SS"
        )
    if duration < 1 or duration > 120:
        raise argparse.ArgumentTypeError("Clips must be between 1 and 120 seconds")
    return start, duration


# def download_clip(id, start, end, output, audio_index=1):
#     start_seconds = timestamp_to_seconds(start)
#     end_seconds = timestamp_to_seconds(end)
#     duration = end_seconds - start_seconds
#     assert duration > 1 and duration < 120, "Clips must be between 1 and 120 seconds"
#     total_bitrate = (
#         math.floor(DISCORD_LIMIT / duration * 8 / 1000) * 1000
#     )  # round down to nearest 1000
#     audio_bitrate = 128_000
#     params = {
#         "maxAudioChannels": 2,
#         "TranscodingMaxAudioChannels": 2,
#         "AudioBitrate": audio_bitrate,
#         "VideoBitrate": total_bitrate - audio_bitrate,
#         "VideoCodec": "h265",
#         "AudioCodec": "aac",
#         "AudioStreamIndex": audio_index,
#     }
#     url = f"{BASE_URL}/Videos/{id}/main.m3u8?{urlencode(params)}"
#     ffmpeg_args = [
#         "ffmpeg",
#         "-ss",
#         str(start_seconds),
#         "-t",
#         str(duration),
#         "-headers",
#         f'Authorization: MediaBrowser Token="{API_KEY}"\r\n',
#         "-i",
#         url,
#         "-c",
#         "copy",
#         "-fs",
#         str(DISCORD_LIMIT),
#         output,
#     ]
#     subprocess.run("ffmpeg" + ffmpeg_args)


def download(
    id: str,
    output: Path,
    total_bitrate: int,
    interval: Optional[Tuple[int, int]] = None,
    size_limit: Optional[int] = None,
    audio_index=1,
):
    audio_bitrate = 128_000
    params = {
        "maxAudioChannels": 2,
        "TranscodingMaxAudioChannels": 2,
        "AudioBitrate": audio_bitrate,
        "VideoBitrate": total_bitrate - audio_bitrate,
        "VideoCodec": "h265",
        "AudioCodec": "aac",
        "AudioStreamIndex": audio_index,
    }
    url = f"{BASE_URL}/Videos/{id}/main.m3u8?{urlencode(params)}"

    print(f"Downloading into: {output}")

    if interval:
        (start, duration) = interval
        (
            ffmpeg.input(
                url,
                ss=start,
                t=duration,
                headers=f'Authorization: MediaBrowser Token="{API_KEY}"\r\n',
            )
            .output(str(output), c="copy", fs=size_limit)
            .run()
        )
    else:
        (
            ffmpeg.input(
                url,
                headers=f'Authorization: MediaBrowser Token="{API_KEY}"\r\n',
            )
            .output(str(output), c="copy")
            .run()
        )


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
        type=int,
        default=None,
    )
    args = parser.parse_args()
    if args.clip and not args.bitrate:
        duration = args.clip[1]
        total_bitrate = math.floor(DISCORD_LIMIT / duration * 8 / 1000) * 1000
        size_limit = DISCORD_LIMIT
    elif args.bitrate:
        total_bitrate = args.bitrate
        size_limit = None
    else:
        total_bitrate = 10_000_000
        size_limit = None
    download(
        args.id,
        args.output,
        total_bitrate,
        interval=args.clip,
        size_limit=size_limit,
        audio_index=args.audio_index,
    )
    # download_clip(args.id, args.start, args.end, args.output, args.audio_index)
