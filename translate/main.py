import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

import utils.aws as aws


def get_translation(text, src_lang, dst_lang):
    translate_client = boto3.client(
        service_name='translate',
        region_name=aws.Region.EU_IRELAND.value,
        use_ssl=True,
        config=Config(retries={'max_attempts': 10})
    )

    while True:
        try:
            translation = translate_client.translate_text(
                Text=text,
                SourceLanguageCode=src_lang.value,
                TargetLanguageCode=dst_lang.value
            )
            break
        except ClientError as e:
            print(f'Client error while attempting to translate (AWS)')
            print('Sleeping...')
            time.sleep(5)
        except Exception as e:
            raise e

    return translation
