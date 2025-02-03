# Jellyclipper
*Small python script using ffmpeg to download a transcoded video / clip from a jellyfin server*

Useful to create clips from movies or downloading a transcoded version of an entire movie (since no jellyfin client app properly supports this). Since it uses the HLS stream with `ffmpeg` it should be much less likely to fail compared to the direct download.

## Installation
- clone this repo
- Install dependencies in a python environment of your choice (`pip install -r requirements.txt`)
- create a `.env` file and provide the Jellyfin server URL and API key.
You can copy `.env.example` as a starting point

## Usage

`jellyclipper.py [-h] [--clip CLIP] [--audio-index AUDIO_INDEX] [--bitrate BITRATE] [--codec {h264,h265}] id output`

`--help / -h` provides a short description of the arguments\
`output`: Path to output file. Select container by extension (e.g. mp4, mkv, probably best to stick with those)

#### Finding the 'id'
- open jellyfin in a browser and navigate to the desired Movie/Episode but **don't** play it
- in the URL parameters you'll find the `id` (not `serverId`)

#### Clipping
If you want to download a specific clip instead of an entire movie, you can specify this using the `--clip` commandline argument, followed by timestamps in the format `HH:MM:SS-HH:MM:SS` for ranges or `HH:MM:SS+HH:MM:SS` for start + duration. You can omit the hours/minutes if they're zero, however you must always provide them in two-digit pairs (so `1` hour must be `01`).
**Examples:**
- `01:23:10-01:33:10` is a 10 minute clip starting at `01:23:10`
- `50:00-01:05:00` is a 15 Minute clip starting at `50:00`
- `50:00+15:00` is the same 15 minute clip as above
- `20:44+10` is a 10 second clip starting at `20:44`

#### Bitrate
Specify the bitrate in Bit/sec. You can also use `k` / `M` for kBit / Mbit (e.g `--bitrate 10M` sets the bitrate to 10 Mbit/sec). The default value is 10Mbit / sec.
For convenience, you can also set the bitrate to the special value `discord`, which uses the best bitrate while ensuring the output file has a maximum file size of `25MB`, which is the Discord attachment size limit for users without Nitro. However this is limited to clips of at most 120s in length, to retain resonable quality.

**Note** 
At the moment this uses jellyfins API to request a transcoded stream from the server. The transcoding therefore happens on the server and I noticed that jellyfin sometimes refuses to serve you the exact bitrate or codec requested if it has something similar cached.
Assuming there's no way to configure this behaviour in jellyfin (haven't found anything yet), the only way to fully control this would be to stream the original file and transcode it on the client device, but I don't think it's worth downloading an entire 30+ GB file just to transcode it to a fraction of that size.

#### Audio-Index
This can be used to select the desired audio track if multiple are present. Useful for multilanguage content. By default this is set to 1 (which means using the default one).

#### Codec
Select between h264 and h265 codecs. By default h265 is used because of better image quality at the same bitrate.