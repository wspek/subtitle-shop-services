from enum import Enum
from pathlib import Path
import statistics

import srt

from translate import get_translation
from utils.srtUtils import writeTranscriptToSRTFile
import utils.algorithm as algorithm

MAX_BYTES_IN_TRANSIT = 4500
DEBUG_MODE = True


class Language(Enum):
    ENGLISH = 'en'
    DUTCH = 'nl'
    SPANISH = 'es'
    PORTUGUESE = 'pt'
    HEBREW = 'he'


def write_transcript_to_srt_file(transcript_file, src_language, out_folder):
    with open(transcript_file, 'r') as f:
        transcription = f.read()

    path = Path(transcript_file)
    filename = path.stem
    srt_file_path = Path(out_folder) / f'{filename}_{src_language.value}.srt'

    writeTranscriptToSRTFile(transcription, srt_file_path)

    return str(srt_file_path)


def translate_srt_file(src_file, dst_file, src_lang, dst_lang):
    with open(src_file, 'r') as f:
        srt_content = f.read()

    subtitles_translated_complete = ''

    srt_pages = srt_to_pages(srt_content)

    sub_counter = 1
    for num_page, srt_page in enumerate(srt_pages):
        # Translate the full text.
        full_text_translation = get_translation(srt_page['text'], src_lang, dst_lang)

        # Translate every seperate block of the srt too.
        srt_text = '\n'.join([block['text'] for block in srt_page['blocks']])
        srt_block_translation = get_translation(srt_text, src_lang, dst_lang)
        srt_translated_blocks = srt_block_translation['TranslatedText'].split('\n')

        # Store the block translation
        for i, translated_block in enumerate(srt_translated_blocks):
            srt_page['blocks'][i]['raw_translation'] = translated_block

        # Sync the page to the full text
        synced_srt_page = sync(full_text_translation['TranslatedText'], srt_page, algorithm.jaccard)

        # Add a new translated subtitle page to the total
        subtitles_translated_complete += render_srt_page(synced_srt_page, sub_counter)

        sub_counter += len(synced_srt_page['blocks'])

    with open(dst_file, 'w') as f:
        f.write(subtitles_translated_complete)

    return dst_file


def srt_to_pages(srt_content):
    subs = list(srt.parse(srt_content))

    def add_page(blocks):
        txt_content = ' '.join([block['text'] for block in blocks])
        pages.append({
            'text': txt_content,
            'blocks': blocks
        })

    pages = []
    blocks = []
    total_bytes = 0

    for sub in subs:
        text = sub.content.replace('\n', ' ')
        total_bytes += len(text.encode('utf-8'))

        if total_bytes > MAX_BYTES_IN_TRANSIT:
            add_page(blocks)
            blocks = []
            total_bytes = len(text.encode('utf-8'))

        blocks.append({
            'text': text,
            'start': sub.start,
            'end': sub.end
        })

    add_page(blocks)

    return pages


def sync(translation, page, algo):
    window_size = 10
    length_ratio_threshold = 90.0

    translated_words = translation.split(' ')

    end_of_page = test_end_of_page(translated_words)

    for j, block in enumerate(page['blocks'][:-1]):
        raw_translation = block['raw_translation']

        distances = []
        assembled_sentence = ''
        for i, translated_word in enumerate(translated_words):
            assembled_sentence = ' '.join([assembled_sentence, translated_word]) if assembled_sentence else translated_word
            distance = algo(raw_translation, assembled_sentence)

            if distance == 0.0:     # We found the perfect match
                block['translation'] = wrap_sentence(assembled_sentence)
                translated_words = translated_words[i+1:]
                break

            length_ratio = calc_length_ratio(raw_translation, assembled_sentence)
            print(distance, length_ratio)

            if (len(distances) >= window_size and calc_average_slope(distances, window_size) >= 0) or end_of_page(i):
                # No match whatsoever for window_size
                if statistics.mean(distances) == 1.0:
                    forward_boundary_index = forward_match(translated_words, page['blocks'][j+1], algo)

                    oneliner = ' '.join(translated_words[:forward_boundary_index])
                    translated_words = translated_words[forward_boundary_index:]
                    block['translation'] = wrap_sentence(oneliner)

                    break

                if length_ratio > length_ratio_threshold or end_of_page(i):
                    min_distance = min(distances)
                    lowest_distance_index = max([i for i, x in enumerate(distances) if x == min_distance])

                    oneliner = ' '.join(translated_words[:lowest_distance_index+1])
                    block['translation'] = wrap_sentence(oneliner)
                    translated_words = translated_words[lowest_distance_index+1:]

                    break

            distances.append(distance)

    oneliner = ' '.join(translated_words)  # The remaining translation
    page['blocks'][-1]['translation'] = wrap_sentence(oneliner)

    return page


def test_end_of_page(words):
    return lambda x: len(words) == x + 1


def calc_length_ratio(base_text, sentence):
    return round((len(sentence) / len(base_text)) * 100, 2)


def calc_average_slope(iterable, windows_size):
    data_set = iterable[-windows_size:]

    slopes = []
    zipped = list(zip(data_set, data_set[1:] + [0]))
    for i, (x, y) in enumerate(zipped, start=1):
        if i < len(zipped):
            slopes.append(y-x)

    return statistics.mean(slopes)


def forward_match(translated_words, next_block, algo):
    raw_translation = next_block['raw_translation']

    sentence = ''

    distances = []
    for i, word in enumerate(translated_words):
        sentence = ' '.join([sentence, word]) if sentence else word

        distance = algo(raw_translation, sentence)
        distances.append(distance)

        if statistics.mean(distances) < 1.0:
            return i

    return 0


def wrap_sentence(sentence, max_chars=42):
    full_sentence_length = len(sentence)

    if full_sentence_length <= max_chars:
        return sentence

    midway_point = int(full_sentence_length / 2)
    words = sentence.split(' ')

    subsentence = ''
    for i, word in enumerate(words):
        subsentence += ' ' + word

        if i == 0:
            subsentence = subsentence.strip()

        if len(subsentence) >= midway_point:
            result = ' '.join(words[:i]) + '\n' + ' '.join(words[i:])
            return result


def render_srt_page(page, index):
    subtitles = []
    for block in page['blocks']:
        try:
            subtitles.append(srt.Subtitle(index, block['start'], block['end'], block['translation']))
        except KeyError:
            pass

    return srt.compose(subtitles, reindex=True, start_index=index)


if __name__ == '__main__':
    srt_file = write_transcript_to_srt_file(
        transcript_file='/home/wspek/dev/subtitle-shop-services/var/AUDIO_128kbps_GMR Transcription Services Inc_How to Pass a Transcription Test | Explainer Video_xTY3kPmDrOM.txt',   # noqa
        src_language=Language.ENGLISH,
        out_folder='/home/wspek/dev/subtitle-shop-services/var',
    )

    translate_srt_file(
        src_file=srt_file,
        dst_file='/home/wspek/dev/subtitle-shop-services/var/AUDIO_128kbps_GMR Transcription Services Inc_How to Pass a Transcription Test | Explainer Video_xTY3kPmDrOM_es.srt',    # noqa
        src_lang=Language.ENGLISH,
        dst_lang=Language.SPANISH,
    )
