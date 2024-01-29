from enum import Enum
import os
import shutil
import tempfile

import ffmpeg
from pytube import YouTube


class MediaFormat(Enum):
    MP3 = 'mp3'
    MP4 = 'mp4'


class Resolution(Enum):
    RES_144P = '144p'
    RES_240P = '240p'
    RES_360P = '360p'
    RES_480P = '480p'
    RES_720P_HD = '720p'
    RES_1080P_FULLHD = '1081p'


def download_audio(url, folder, file_format=MediaFormat.MP4):
    yt = YouTube(url)

    filtered_streams = yt.streams.filter(only_audio=True, subtype=file_format.value)

    if filtered_streams:
        # We always want the highest bitrate available to be saved
        streams_sorted_bitrate = sorted(filtered_streams, key=lambda x: int(x.abr.replace('kbps', '')), reverse=True)

        stream = next(stream for stream in streams_sorted_bitrate)
        bitrate = stream.abr

        # For some reason I cannot get the correct title
        filename = f'AUDIO_{bitrate}_{yt.author}_{yt.title}'[:100] + f'_{yt.video_id}.{file_format.value}'
        stream.download(output_path=folder, filename=filename)

        return f'{folder}/{filename}'


def download_video(url, folder, resolution=Resolution.RES_1080P_FULLHD, file_format=MediaFormat.MP4):
    yt = YouTube(url)

    filtered_streams = yt.streams.filter(progressive=True, subtype=file_format.value)
    filtered_streams = sorted(
        filtered_streams,
        key=lambda x: int(x.resolution.replace('p', '') if x.resolution else 0),
        reverse=True
    )
    highest_res_stream = next(iter(filtered_streams))
    video_stream = next(
        (stream for stream in filtered_streams if stream.resolution == resolution.value),   # or else,
        highest_res_stream
    )

    video_filename = f'VIDEO_{video_stream.resolution}_{yt.author}_{yt.title}_{yt.video_id}.{video_stream.subtype}'
    video_stream.download(output_path='/tmp', filename=video_filename)
    audio_filename = download_audio(url, folder='/tmp')

    merge_av_files(f'/tmp/{video_filename}', audio_filename)

    final_filepath = f'{folder}/{video_filename}'
    shutil.move(f'/tmp/{video_filename}', final_filepath)

    return final_filepath


def merge_av_files(video_file, audio_file):
    merged_filename = tempfile.NamedTemporaryFile().name + '.' + video_file.split('.')[-1]

    input_video = ffmpeg.input(video_file)
    input_audio = ffmpeg.input(audio_file)

    ffmpeg.concat(input_video, input_audio, v=1, a=1).output(merged_filename).run(overwrite_output=False)

    os.remove(video_file)
    os.rename(merged_filename, video_file)

    return merged_filename
