#!/usr/bin/env python
"""Annotate items of interest to Draper from their ontology"""
import sys
sys.path = ['./', '../'] + sys.path
import re
import copy
from collections import defaultdict

import pattern.en, pattern.search

from annotator.annotator import *
from annotator.token_annotator import TokenAnnotator
from annotator.sentence_annotator import SentenceAnnotator
import draper_ontology
import annotator.utils

class DraperAnnotator(Annotator):

    def __init__(self):

        self.build_taxonomy(draper_ontology.ontology)
        self.standalones = draper_ontology.standalones

    def build_taxonomy(self, ontology):
        self.taxonomy = pattern.search.Taxonomy()
        self.inflected_lemmata = {}

        for term_type in ontology.keys():
            for term in ontology[term_type]:
                for lex in pattern.en.lexeme(term):
                    self.inflected_lemmata[lex] = term
                    self.taxonomy.append(lex, type=term_type)

        self.leftterms = self.get_all_taxonomy_children('leftterms')
        self.rightterms = self.get_all_taxonomy_children('rightterms')

        self.leftterms_patt = re.compile(r'\b(' + '|'.join(self.leftterms) + r')\b')
        self.rightterms_patt = re.compile(r'\b(' + '|'.join(self.rightterms) + r')\b')

    def get_all_taxonomy_children(self, parent):
        children = self.taxonomy.children(parent)
        res = copy.copy(children)
        for child in children:
            res += self.get_all_taxonomy_children(child)
        return res


    def annotate(self, doc):

        if not 'tokens' in doc.tiers:
            token_annotator = TokenAnnotator()
            doc.add_tier(token_annotator)

        if not 'sentences' in doc.tiers:
            sentence_annotator = SentenceAnnotator()
            doc.add_tier(sentence_annotator)

        matches = {}

        tree = pattern.en.parsetree(doc.text, lemmata=True)

        matches['leftterms'] = pattern.search.search('LEFTTERMS', tree, taxonomy=self.taxonomy)
        matches['rightterms'] = pattern.search.search('RIGHTTERMS', tree, taxonomy=self.taxonomy)

        matches['standalone'] = []
        for standalone in self.standalones:
            matches['standalone'] += pattern.search.search(standalone, tree)

        retained_matches = []

        seen_matches = set()

        spans = {}
        spans['leftterms'] = []
        spans['rightterms'] = []
        spans['standalone'] = []

        for match_type, patt in [('leftterms', self.leftterms_patt), ('rightterms', self.rightterms_patt)]:
            for match in re.finditer(patt, doc.text):
                span = AnnoSpan(match.start(), match.end(), doc)
                spans[match_type].append(span)

        for match_type in matches.keys():
            for match in matches[match_type]:
                offsets_tuples = utils.find_all_match_offsets(doc.text, match)
                for offsets_tuple in offsets_tuples:
                    start_offset = offsets_tuple['fullMatch'][0]
                    stop_offset = offsets_tuple['fullMatch'][1]

                    if (match.string, start_offset, stop_offset) not in seen_matches:

                        span = AnnoSpan(
                            start_offset,
                            stop_offset,
                            doc)
                            # label=self.inflected_lemmata[match.string])
                        spans[match_type].append(span)
                        seen_matches.add((match.string, start_offset, stop_offset))

            doc.tiers[match_type] = AnnoTier(spans[match_type])
            doc.tiers[match_type].filter_overlapping_spans()

        spans = []

        for left_span in doc.tiers['leftterms'].spans:

            sentence_span = left_span.containing_span_in_tier('sentences')
            left_spans = sentence_span.contained_spans_in_tier('leftterms')
            right_spans = sentence_span.contained_spans_in_tier('rightterms')
            standalone_spans = sentence_span.contained_spans_in_tier('standalone')
            if len(right_spans) > 0:

                min_distance = 1000

                for right_span in right_spans:
                    distance = left_span.token_distance(right_span)
                    if distance < min_distance:
                        min_distance = distance

                if min_distance <= 10:
                    first_span = sorted( left_spans + right_spans + standalone_spans,
                                         key = lambda x: x.start )[0]
                    last_span = sorted( left_spans + right_spans + standalone_spans,
                                         key = lambda x: x.end )[-1]
                    span = AnnoSpan(first_span.start, last_span.end, doc)
                    spans.append(span)

        for standalone_span in doc.tiers['standalone'].spans:
            sentence_span = standalone_span.containing_span_in_tier('sentences')
            left_spans = sentence_span.contained_spans_in_tier('leftterms')
            right_spans = sentence_span.contained_spans_in_tier('rightterms')
            standalone_spans = sentence_span.contained_spans_in_tier('standalone')
            first_span = sorted( left_spans + right_spans + standalone_spans,
                                 key = lambda x: x.start )[0]
            last_span = sorted( left_spans + right_spans + standalone_spans,
                                 key = lambda x: x.end )[-1]
            span = AnnoSpan(first_span.start, last_span.end, doc)
            spans.append(span)

        doc.tiers['draper'] = AnnoTier(spans)
        doc.tiers['draper'].filter_overlapping_spans()

        return doc

if __name__ == '__main__':
    run_case_count_patterns()
