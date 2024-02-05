from pathlib import Path
import time
import uuid

import boto3
import requests

import utils.aws as aws

REGION = aws.Region.SA_SAO_PAOLO
S3_BUCKET = 'subtitle-shop'


def transcribe(file_path, language, out_folder):
    path = Path(file_path)
    file_format = path.suffix.lstrip('.')

    s3 = aws.S3(region=REGION, bucket=S3_BUCKET)

    key = path.name
    if not s3.exists(key=key):
        uri = s3.upload(file_path, key=key)
    else:
        uri = s3.get_object_uri(key=key)

    transcribe_client = boto3.client('transcribe')

    # Use the uuid functionality to generate a unique job name.
    # Otherwise, the Transcribe service will return an error.
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName="transcribe_" + uuid.uuid4().hex,
        LanguageCode=language.value,
        MediaFormat=file_format,
        Media={"MediaFileUri": uri},
        # Settings = { "VocabularyName" : "MyVocabulary" }
    )
    job_name = response["TranscriptionJob"]['TranscriptionJobName']

    def job_in_progress():
        r = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        return r["TranscriptionJob"]["TranscriptionJobStatus"] == "IN_PROGRESS"

    while job_in_progress():
        print('.')
        time.sleep(5)

    job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    transcript_uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    transcript = requests.get(transcript_uri).text

    transcript_file = f'{out_folder}/{path.stem}.txt'
    with open(transcript_file, 'w') as f:
        f.write(transcript)

    s3.delete(key=key)

    return transcript_file


if __name__ == '__main__':
    transcribe(
        file_path='/home/wspek/dev/subtitle-shop-services/var/AUDIO_128kbps_GMR Transcription Services Inc_How to Pass a Transcription Test | Explainer Video_xTY3kPmDrOM.mp4',     # noqa
        language=aws.Language.ENGLISH_US,
        out_folder='/home/wspek/dev/subtitle-shop-services/var',
    )
