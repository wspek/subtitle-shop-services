from download import download_audio
from transcribe import transcribe
import subtitle
import utils.aws as aws


YOUTUBE_VIDEO_URL = 'https://youtu.be/xTY3kPmDrOM?si=RLB3PIaQl6pFSIFA'
FOLDER = '/home/wspek/dev/subtitle_shop_services/var'


def run_sample():
    audio_file = download_audio(
        url=YOUTUBE_VIDEO_URL,
        folder=FOLDER,
    )

    transcript_file = transcribe(
        file_path=audio_file,
        language=aws.Language.ENGLISH_US,
        out_folder=FOLDER,
    )

    source_srt_file = subtitle.write_transcript_to_srt_file(
        transcript_file=transcript_file,
        src_language=subtitle.Language.ENGLISH,
        out_folder=FOLDER,
    )

    subtitle.translate_srt_file(
        src_file=source_srt_file,
        dst_file=source_srt_file.replace(subtitle.Language.ENGLISH.value, subtitle.Language.SPANISH.value),
        src_lang=subtitle.Language.ENGLISH,
        dst_lang=subtitle.Language.SPANISH,
    )


if __name__ == '__main__':
    run_sample()
