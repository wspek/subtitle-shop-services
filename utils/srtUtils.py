# ==================================================================================
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ==================================================================================
#
# srtUtils.py
# by: Rob Dachowski
# For questions or feedback, please contact robdac@amazon.com
#
# Purpose: The program provides a number of utility functions for creating SubRip Subtitle files (.SRT)
#
# Change Log:
#          6/29/2018: Initial version
#
# ==================================================================================

from datetime import datetime, timedelta
import json
import boto3
import re
import codecs

# from audioUtils import *


MAX_LINE_LENGTH = 42
MAX_PAUSE_MS = 500


# ==================================================================================
# Function: newPhrase
# Purpose: simply create a phrase tuple
# Parameters:
#                 None
# ==================================================================================
def newPhrase():
    return {'start_time': '', 'end_time': '', 'words': [], 'line_length': 0}


# ==================================================================================
# Function: getTimeCode
# Purpose: Format and return a string that contains the converted number of seconds into SRT format
# Parameters:
#                 seconds - the duration in seconds to convert to HH:MM:SS,mmm
# ==================================================================================
# Format and return a string that contains the converted number of seconds into SRT format
def getTimeCode(seconds):
    t_hund = int(seconds % 1 * 1000)
    t_seconds = int(seconds)

    t_hours = int(t_seconds / 3600)
    t_rest_seconds = t_seconds % 3600
    t_mins = int(t_rest_seconds / 60)
    t_rest_seconds = t_rest_seconds % 60

    return str("%02d:%02d:%02d,%03d" % (t_hours, t_mins, int(t_rest_seconds), t_hund))


# ==================================================================================
# Function: writeTranscriptToSRT
# Purpose: Function to get the phrases from the transcript and write it out to an SRT file
# Parameters:
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 srtFileName - the name of the SRT file (e.g. "mySRT.SRT")
# ==================================================================================
def writeTranscriptToSRTFile(transcript, srtFileName):
    # Write the SRT file for the original language
    print("==> Creating SRT from transcript")
    phrases = getPhrasesFromTranscript(transcript)
    writeSRT(phrases, srtFileName)


# ==================================================================================
# Function: writeTranscriptToSRT
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the phrases from the translation
#          and write it out to an SRT file
# Parameters:
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 targetLangCode - the language code for the translated content (e.g. Spanich = "ES")
#                 srtFileName - the name of the SRT file (e.g. "mySRT.SRT")
# ==================================================================================
def writeTranslationToSRT(transcript, sourceLangCode, targetLangCode, srtFileName, region):
    # First get the translation
    print("\n\n==> Translating from " + sourceLangCode.value + " to " + targetLangCode.value)
    translation = translateTranscript(transcript, sourceLangCode.value, targetLangCode.value, region)
    # print( "\n\n==> Translation: " + str(translation))

    # Now create phrases from the translation
    # textToTranslate = unicode(translation["TranslatedText"])
    textToTranslate = translation["TranslatedText"]
    phrases = getPhrasesFromTranslation(textToTranslate, targetLangCode.value)
    writeSRT(phrases, srtFileName)


# ==================================================================================
# Function: getPhrasesFromTranslation
# Purpose: Based on the JSON translation provided by Amazon Translate, get the phrases from the translation
#          and write it out to an SRT file.  Note that since we are using a block of translated text rather than
#          a JSON structure with the timing for the start and end of each word as in the output of Transcribe,
#          we will need to calculate the start and end-time for each phrase
# Parameters:
#                 translation - the JSON output from Amazon Translate
#                 targetLangCode - the language code for the translated content (e.g. Spanich = "ES")
# ==================================================================================
def getPhrasesFromTranslation(translation, targetLangCode):
    # Now create phrases from the translation
    words = translation.split()

    # print( words ) #debug statement

    # set up some variables for the first pass
    phrase = newPhrase()
    phrases = []
    nPhrase = True
    x = 0
    c = 0
    seconds = 0

    print
    "==> Creating phrases from translation..."

    for word in words:

        # if it is a new phrase, then get the start_time of the first item
        if nPhrase == True:
            phrase["start_time"] = getTimeCode(seconds)
            nPhrase = False
            c += 1

        # Append the word to the phrase...
        phrase["words"].append(word)
        x += 1

        # now add the phrase to the phrases, generate a new phrase, etc.
        if x == 10:
            # For Translations, we now need to calculate the end time for the phrase
            psecs = getSecondsFromTranslation(getPhraseText(phrase), targetLangCode, "phraseAudio" + str(c) + ".mp3")
            seconds += psecs
            phrase["end_time"] = getTimeCode(seconds)

            # print c, phrase
            phrases.append(phrase)
            phrase = newPhrase()
            nPhrase = True
            # seconds += .001
            x = 0

        # This if statement is to address a defect in the SubtitleClip.   If the Subtitles end up being
        # a different duration than the content, MoviePy will sometimes fail with unexpected errors while
        # processing the subclip.   This is limiting it to something less than the total duration for our example
        # however, you may need to modify or eliminate this line depending on your content.
        if c == 30:
            break

    return phrases


# ==================================================================================
# Function: getPhrasesFromTranscript
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the phrases from the translation
#          and write it out to an SRT file
# Parameters:
#                 transcript - the JSON output from Amazon Transcribe
# ==================================================================================

def getPhrasesFromTranscript(transcript):
    # This function is intended to be called with the JSON structure output from the Transcribe service.  However,
    # if you only have the translation of the transcript, then you should call getPhrasesFromTranslation instead

    # Now create phrases from the translation
    ts = json.loads(transcript)
    items = ts['results']['items']
    # print( items )

    # set up some variables for the first pass
    phrase = newPhrase()
    phrases = []
    nPhrase = True
    x = 0
    c = 0

    print("==> Creating phrases from transcript...")

    for i, item in enumerate(items):
        line_count = phrase["words"].count('\n') + 1

        if line_count > 2:
            phrase["words"] = phrase["words"][:-1]  # Exclude the final newline
            phrase = distribute_line(phrase)
            phrases.append(phrase)
            phrase = newPhrase()
            nPhrase = True
            x = 0

        # now add the phrase to the phrases, generate a new phrase, etc.
        if item['type'] == 'punctuation':
            last_word = phrase["words"][-1]
            phrase["words"][-1] = last_word + item['alternatives'][0]['content']
            # continue
        elif phrase['line_length'] + (len(item[u'alternatives'][0][u'content']) + 1) > MAX_LINE_LENGTH:
            if line_count == 1:
                phrase["words"].append('\n')
            else:
                phrase = distribute_line(phrase)
                phrases.append(phrase)
                phrase = newPhrase()
                nPhrase = True
                x = 0

        # if it is a new phrase, then get the start_time of the first item
        if item["type"] == "pronunciation":
            if nPhrase == True:
                phrase["start_time"] = getTimeCode(float(item["start_time"]))
                start_time = datetime.strptime(phrase["start_time"], '%H:%M:%S,%f')
                end_time = start_time + timedelta(milliseconds=500)
                phrase["end_time"] = datetime.strftime(end_time, '%H:%M:%S,%f')[:-3]
                nPhrase = False
                c += 1
            else:
                # get the end_time if the item is a pronuciation and store it
                # We need to determine if this pronunciation or puncuation here
                # Punctuation doesn't contain timing information, so we'll want
                # to set the end_time to whatever the last word in the phrase is.
                phrase["end_time"] = getTimeCode(float(item["end_time"]))

            # in either case, append the word to the phrase...
            phrase["words"].append(item['alternatives'][0]["content"])

        # DELETE?
        if item['alternatives'][0]['content'] in ('.', '?', '!'):
            try:
                next_time = getTimeCode(float(items[i + 1]["start_time"]))
            except IndexError:
                # Typically would happen at the end of the transcript
                break

            if long_pause(phrase["end_time"], next_time):
                end_time = datetime.strptime(phrase["end_time"], '%H:%M:%S,%f')
                end_time = end_time + timedelta(milliseconds=MAX_PAUSE_MS)
                phrase["end_time"] = datetime.strftime(end_time, '%H:%M:%S,%f')[:-3]

            phrase = distribute_line(phrase)
            phrases.append(phrase)
            phrase = newPhrase()
            nPhrase = True
            x = 0
            continue

            # phrase["end_time"] = next_time
            # phrase["words"].append('\n')

        phrase['line_length'] = len(getPhraseText(phrase).split('\n')[-1])
        x += 1

    if len(phrase["words"]) > 0:
        phrases.append(phrase)

    return phrases


def long_pause(start_time, end_time):
    from datetime import datetime, time

    start_time = time.fromisoformat(start_time.replace(',', '.'))
    end_time = time.fromisoformat(end_time.replace(',', '.'))

    start_time_in_ms = start_time.second * 1000 + start_time.microsecond / 1000
    end_time_in_ms = end_time.second * 1000 + end_time.microsecond / 1000

    diff_ms = end_time_in_ms - start_time_in_ms

    return diff_ms > MAX_PAUSE_MS


def distribute_line(phrase):
    new_phrase = phrase.copy()

    text = getPhraseText(phrase)
    first_line = text.split('\n')[0]
    ends_with_punct = True if first_line[-1] in ('.', '?', '!') else False

    if not ends_with_punct:
        new_phrase["words"].remove('\n')
        half_length = len(getPhraseText(new_phrase)) / 2

        for j, _ in enumerate(new_phrase["words"]):
            temp_phrase_prev = new_phrase.copy()
            temp_phrase = new_phrase.copy()
            temp_phrase_prev['words'] = new_phrase["words"][:j]
            temp_phrase['words'] = new_phrase["words"][:j + 1]
            prev_line = getPhraseText(temp_phrase_prev)
            new_line = getPhraseText(temp_phrase)

            if len(new_line) > half_length:
                if abs(MAX_LINE_LENGTH - len(new_line)) < abs(MAX_LINE_LENGTH - len(prev_line)):
                    phrase["words"].insert(j + 1, '\n')
                else:
                    phrase["words"].insert(j, '\n')

                break

    text = getPhraseText(new_phrase)
    first_line = text.split('\n')[0]
    try:
        second_line = text.split('\n')[1]
    except IndexError:
        return phrase

    if len(first_line) <= MAX_LINE_LENGTH and len(second_line) <= MAX_LINE_LENGTH:
        return new_phrase
    else:
        return phrase


# ==================================================================================
# Function: translateTranscript
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the JSON response of translated text
# Parameters:
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 targetLangCode - the language code for the translated content (e.g. Spanich = "ES")
#                 region - the AWS region in which to run the Translation (e.g. "us-east-1")
# ==================================================================================
def translateTranscript(transcript, sourceLangCode, targetLangCode, region):
    # Get the translation in the target language.  We want to do this first so that the translation is in the full context
    # of what is said vs. 1 phrase at a time.  This really matters in some lanaguages

    # stringify the transcript
    ts = json.loads(transcript)

    # pull out the transcript text and put it in the txt variable
    txt = ts["results"]["transcripts"][0]["transcript"]

    # set up the Amazon Translate client
    translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)

    # call Translate  with the text, source language code, and target language code.  The result is a JSON structure containing the
    # translated text
    translation = translate.translate_text(Text=txt, SourceLanguageCode=sourceLangCode,
                                           TargetLanguageCode=targetLangCode)

    return translation


# ==================================================================================
# Function: writeSRT
# Purpose: Iterate through the phrases and write them to the SRT file
# Parameters:
#                 phrases - the array of JSON tuples containing the phrases to show up as subtitles
#                 filename - the name of the SRT output file (e.g. "mySRT.srt")
# ==================================================================================
def writeSRT(phrases, filename):
    print
    "==> Writing phrases to disk..."

    # open the files
    e = codecs.open(filename, "w+", "utf-8")
    x = 1

    for phrase in phrases:
        # determine how many words are in the phrase
        length = len(phrase["words"])

        # write out the phrase number
        e.write(str(x) + "\n")
        x += 1

        # write out the start and end time
        e.write(phrase["start_time"] + " --> " + phrase["end_time"] + "\n")

        # write out the full phase.  Use spacing if it is a word, or punctuation without spacing
        out = getPhraseText(phrase)

        # write out the srt file
        e.write(out + "\n\n")

    # print out

    e.close()


# ==================================================================================
# Function: getPhraseText
# Purpose: For a given phrase, return the string of words including punctuation
# Parameters:
#                 phrase - the array of JSON tuples containing the words to show up as subtitles
# ==================================================================================

def getPhraseText(phrase):
    length = len(phrase["words"])

    out = ""
    for i in range(0, length):
        if re.match('[a-zA-Z0-9]', phrase["words"][i]):
            if i == 0 or phrase["words"][i - 1] == '\n':
                out += phrase["words"][i]
            else:
                out += " " + phrase["words"][i]
        else:
            out += phrase["words"][i]

    return out
