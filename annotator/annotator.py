#!/usr/bin/env python
"""Annotator"""
import json
import re
from lazy import lazy

from nltk import sent_tokenize

import pattern
import utils

def tokenize(text):
    return sent_tokenize(text)

class Annotator(object):

    def annotate():
        """Take an AnnoDoc and produce a new annotation tier"""
        raise NotImplementedError("annotate method must be implemented in child")

class AnnoDoc(object):

    # TODO what if the original text needs to be later transformed, e.g.
    # stripped of tags? This will ruin offsets.

    def __init__(self, text=None, date=None):
        if type(text) is unicode or text:
            self.text = text
        elif type(text) is str:
            self.text = unicode(text, 'utf8')
        else:
            raise TypeError("text must be string or unicode")
        self.tiers = {}
        self.properties = {}
        self.pattern_tree = None
        self.date = date

    def find_match_offsets(self, match):
        """
        Returns the byte offsets of a pattern lib match object.
        """
        return (
            match.words[0].byte_offsets[0],
            match.words[-1].byte_offsets[-1]
        )

    def byte_offsets_to_pattern_match(self, offsets):
        """
        Create a pattern lib match object from the given byte offsets.
        """
        class ExtrnalMatch(pattern.search.Match):
            """
            A sequence of words that implements the pattern match interface.
            """
            def __init__(self, words):
                self.words = words
        start_word = self.__offset_to_word[offsets[0]]
        end_word = self.__offset_to_word[offsets[-1] - 1]
        return ExtrnalMatch(
            self.pattern_tree.all_words[
                start_word.abs_index:end_word.abs_index + 1
            ]
        )

    def setup_pattern(self):
        """
        Parse the doc with pattern so we can use the pattern.search module on it
        """
        if self.pattern_tree:
            # Document is already parsed.
            return
        self.taxonomy = pattern.search.Taxonomy()
        self.taxonomy.append(pattern.search.WordNetClassifier())
        self.pattern_tree = pattern.en.parsetree(
            utils.dehyphenate_numbers_and_ages(self.text),
            lemmata=True,
            relations=True
        )
        # The pattern tree parser doesn't tag some numbers, such as 2, as CD (Cardinal number).
        # see: https://github.com/clips/pattern/issues/84
        # This code tags all the arabic numerals as CDs. It is a temporairy fix
        # that should be discarded when issue is resulted in the pattern lib.
        for sent in self.pattern_tree:
            for word in sent.words:
                if utils.parse_number(word.string) is not None:
                    word.tag = 'CD'
        # Annotate the words in the parse tree with their absolute index and
        # and create an array with all the words.
        abs_index = 0
        self.pattern_tree.all_words = []
        for sent in self.pattern_tree:
            for word in sent.words:
                self.pattern_tree.all_words.append(word)
                word.abs_index = abs_index
                abs_index += 1
        # Create __offset_to_word array and add byte offsets to all the
        # words in the parse tree.
        text_offset = 0
        word_offset = 0
        self.__offset_to_word = [None] * len(self.text)
        while(
            text_offset < len(self.text) and
            word_offset < len(self.pattern_tree.all_words)
        ):
            word = self.pattern_tree.all_words[word_offset]
            # Sometimes words remove spaces that were present in the original
            # e.g. :3 so we need to ignore spaces inside the original
            match_offset = 0
            for word_char in word.string:
                if self.text[text_offset + match_offset] == word_char:
                    match_offset += 1
                else:
                    while self.text[text_offset + match_offset] == ' ':
                        match_offset += 1
                    if self.text[text_offset + match_offset] == word_char:
                        match_offset += 1
                    else:
                        match_offset = -1
                        break
            if (
                word.string[0] == self.text[text_offset] and
                match_offset > 0 and
                word.string[-1] == self.text[text_offset + match_offset - 1]
            ):
                word.byte_offsets = (text_offset, text_offset + match_offset)
                self.__offset_to_word[text_offset] = word
                text_offset += match_offset
                word_offset += 1
            elif (
                # Hyphens may be removed from the pattern text
                # so they are treated as spaces and can be skipped when aligning
                # the text.
                re.match(r"\s|-$", self.text[text_offset])
            ):
                text_offset += 1
            else:
                raise Exception(
                    "Cannot match word [" + word.string +
                    "] with text [" + self.text[text_offset:text_offset + 10] + "]"
                )
        # Fill the empty offsets with their previous value
        prev_val = None
        for idx, value in enumerate(self.__offset_to_word):
            if value is not None:
                prev_val = value
            else:
                self.__offset_to_word[idx] = prev_val

        def p_search(query):
            # Add offsets:
            results = pattern.search.search(
                query,
                self.pattern_tree,
                taxonomy=self.taxonomy
            )
            # for r in results:
            #     r.sentence_idx = self.pattern_tree.sentences.index(r.words[0].sentence)
            return results


        self.p_search = p_search

    def add_tier(self, annotator, **kwargs):
        annotator.annotate(self, **kwargs)

    def to_json(self):
        json_obj = {'text': self.text,
                    'properties': self.properties}

        if self.date:
            json_obj['date'] = self.date.strftime("%Y-%m-%dT%H:%M:%S") + 'Z'

        if self.properties:
            json_obj['properties'] = self.properties

        json_obj['tiers'] = {}
        for name, tier in self.tiers.iteritems():
            json_obj['tiers'][name] = tier.to_json()

        return json.dumps(json_obj)

class AnnoTier(object):

    def __init__(self, spans=None):
        if spans is None:
            self.spans = []
        else:
            self.spans = spans

    def __repr__(self):
        return unicode([unicode(span) for span in self.spans])

    def __len__(self):
        return len(self.spans)

    def to_json(self):

        docless_spans = []
        for span in self.spans:
            span_dict = span.__dict__.copy()
            del span_dict['doc']
            docless_spans.append(span_dict)

        return json.dumps(docless_spans)

    def next_span(self, span):
        """Get the next span after this one"""
        index = self.spans.index(span)
        if index == len(self.spans) - 1:
            return None
        else:
            return self.spans[index + 1]

    def spans_over(self, start, end=None):
        """Get all spans which overlap a position or range"""
        if not end: end = start + 1
        return filter(lambda span: len(set(range(span.start, span.end)).
                                       intersection(range(start, end))) > 0,
                      self.spans)

    def spans_in(self, start, end):
        """Get all spans which are contained in a range"""
        return filter(lambda span: span.start >= start and span.end <= end,
                      self.spans)

    def spans_at(self, start, end):
        """Get all spans with certain start and end positions"""
        return filter(lambda span: start == span.start and end == span.end,
                      self.spans)

    def spans_over_span(self, span):
        """Get all spans which overlap another span"""
        return self.spans_over(span.start, span.end)

    def spans_in_span(self, span):
        """Get all spans which lie within a span"""
        return self.spans_in(span.start, span.end)

    def spans_at_span(self, span):
        """Get all spans which have the same start and end as another span"""
        return self.spans_at(span.start, span.end)

    def spans_with_label(self, label):
        """Get all spans which have a given label"""
        return filter(lambda span: span.label == label, self.spans)

    def labels(self):
        """Get a list of all labels in this tier"""
        return [span.label for span in self.spans]

    def sort_spans(self):
        """Sort spans by order of start"""

        self.spans.sort(key=lambda span: span.start)

    # TODO needs testing
    def filter_overlapping_spans(self, decider=None):
        """Remove the smaller of any overlapping spans. Takes an optional
           decider function which takes two spans and returns False if span_a
           should not be retained, True if span_a should be retained."""

        retained_spans = []
        removed_spans_indexes = []

        a_index = -1
        for span_a in self.spans:
            a_index += 1
            retain_a = True
            b_index = -1
            for span_b in self.spans:
                b_index += 1
                if (not b_index in removed_spans_indexes and
                    a_index != b_index and
                    ((span_b.start in range(span_a.start, span_a.end)) or
                     (span_a.start in range(span_b.start, span_b.end))) and
                     span_b.size() >= span_a.size()):

                    if not decider or decider(span_a, span_b) is False:
                        retain_a = False
                        removed_spans_indexes.append(a_index)

            if retain_a:
                retained_spans.append(span_a)

        self.spans = retained_spans

class AnnoSpan(object):

    def __repr__(self):
        return u'{0}-{1}:{2}'.format(self.start, self.end, self.label)

    def __init__(self, start, end, doc, label=None):
        self.start = start
        self.end = end
        self.doc = doc

        if label == None:
            self.label = self.text
        else:
            self.label = label

    def overlaps(self, other_span):
        return (
            (self.start >= other_span.start and self.start <= other_span.end) or
            (other_span.start >= self.start and other_span.start <= self.end)
        )

    def adjacent_to(self, other_span, max_dist=0):
        return (
            self.comes_before(other_span, max_dist) or
            other_span.comes_before(self, max_dist)
        )

    def comes_before(self, other_span, max_dist=0):
        # Note that this is a strict version of comes before where the
        # span must end before the other one starts.
        return (
            self.end >= other_span.start - max_dist - 1 and
            self.end < other_span.start
        )

    def extended_through(self, other_span):
        """
        Create a new span like this one but with its range extended through
        the range of the other span.
        """
        return AnnoSpan(
            min(self.start, other_span.start),
            max(self.end, other_span.end),
            self.doc,
            self.label
        )

    def size(self): return self.end - self.start

    def overlap_in_tier(self, tier):
        """Find any exactly overlapping spans in another tier"""

        for span in tier.spans:
            if span.start == self.start and span.end == self.end:
                return span

        return None

    @lazy
    def text(self):
        return self.doc.text[self.start:self.end]

    def to_dict(self):
        """
        Return a json serializable dictionary.
        """
        return dict(
            label=self.label,
            textOffsets=[[self.start, self.end]]
        )
