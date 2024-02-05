from strsimpy.levenshtein import Levenshtein
from strsimpy.normalized_levenshtein import NormalizedLevenshtein
# from strsimpy.weighted_levenshtein import WeightedLevenshtein, CharacterSubstitutionInterface
from strsimpy.optimal_string_alignment import OptimalStringAlignment
from strsimpy.jaro_winkler import JaroWinkler
from strsimpy.longest_common_subsequence import LongestCommonSubsequence
from strsimpy.metric_lcs import MetricLCS
from strsimpy.ngram import NGram
from strsimpy.cosine import Cosine
from strsimpy.jaccard import Jaccard
from strsimpy.sorensen_dice import SorensenDice
# import spacy
# import wmd


def jaccard(base_txt, txt):
    j = Jaccard(3)
    return j.distance(base_txt, txt)


def cosine(base_txt, txt):
    c = Cosine(1)
    return c.distance(base_txt, txt)


def sorensen_dice(base_txt, txt):
    j = SorensenDice(2)
    return {'sorensen_dice_distance': j.distance(base_txt, txt), 'sorensen_dice_similarity': j.similarity(base_txt, txt)}


def levenshtein(base_txt, txt):
    l = Levenshtein()
    return {'levenshtein_distance': l.distance(s0=base_txt, s1=txt)}


def normalized_levenshtein(base_txt, txt):
    l = NormalizedLevenshtein()
    return {'norm_levenshtein_distance': l.distance(s0=base_txt, s1=txt), 'norm_levenshtein_similarity': l.similarity(s0=base_txt, s1=txt)}


# def weighted_levenshtein(base_txt, txt):
#     class CharSub(CharacterSubstitutionInterface):
#         def cost(self, c0, c1):
#             return 1.0
#
#     l = WeightedLevenshtein(character_substitution=CharSub())
#     return {'weighted_levenshtein_distance': l.distance(s0=base_txt, s1=txt)}


def optimal_string_alignment(base_txt, txt):
    o = OptimalStringAlignment()
    return {'optimal_string_alignment_distance': o.distance(s0=base_txt, s1=txt)}


def jaro_winkler(base_txt, txt):
    l = JaroWinkler()
    return {'jaro_winkler_distance': l.distance(s0=base_txt, s1=txt), 'jaro_winkler_similarity': l.similarity(s0=base_txt, s1=txt)}


def lcs(base_txt, txt):
    lcs = LongestCommonSubsequence()
    return {'lcs_distance': lcs.distance(base_txt, txt)}


def metric_lcs(base_txt, txt):
    l = MetricLCS()
    return {'metric_lcs_distance': l.distance(base_txt, txt)}


def ngram(base_txt, txt):
    l = NGram(2)
    return {'ngram_distance': l.distance(base_txt, txt)}


# def word_movers_distance(translation, srt):
#     translation = translation.split(' ')
#
#     nlp = spacy.load('en_core_web_md')
#     nlp.Defaults.stop_words = set()
#
#     pipe = wmd.WMD.SpacySimilarityHook(nlp, ignore_stops=False)
#     nlp.add_pipe(pipe, last=True)
#
#     for block in srt['blocks']:
#         raw_translation_nlp = nlp(block['raw_translation'])
#
#         distances = []
#         sentence = ''
#         # i = 0
#         for i, word in enumerate(translation):
#             if i == 0:
#                 sentence += word
#                 try:
#                     distance = raw_translation_nlp.similarity(nlp(sentence))
#                 except:
#                     distance = 10.0
#             else:
#                 sentence += str(' ' + word)
#                 distance = raw_translation_nlp.similarity(nlp(sentence))
#
#                 if distance == 0.0:     # We found the perfect match
#                     block['translation'] = sentence
#                     translation = translation[i+1:]
#                     break
#
#                 if distance > distances[i-1]:
#                     block['translation'] = sentence.replace(' {}'.format(word), '')
#                     translation = translation[i:]
#                     break
#
#             distances.append(distance)
