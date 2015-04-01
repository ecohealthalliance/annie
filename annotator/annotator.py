#!/usr/bin/env python
"""The core of Annie: Annotator, AnnoDoc, AnnoTier, and AnnoSpan"""

import json
import re
from lazy import lazy
from collections import defaultdict

import utils

class Annotator(object):
    """Base classe for other annotators to inherit from. An annotator takes an
    AnnoDoc and adds a new AnnoTier of annotations, based on the text or other
    tiers."""

    def annotate():
        """Take an AnnoDoc and produce a new annotation tier"""
        raise NotImplementedError("annotate method must be implemented in child")

class AnnoDoc(object):
    """Container for document text and associated AnnoTiers"""

    def __init__(self, text=None):
        if type(text) is str or text:
            self.text = text
        elif type(text) is str:
            self.text = str(text, 'utf8')
        elif text is not None:
            raise TypeError("text must be string or unicode")
        self.tiers = {}
        self.properties = {}


    def add_tier(self, annotator, **kwargs):
        annotator.annotate(self, **kwargs)

    def to_json(self):
        """Serialize the AnnoDoc to JSON"""

        json_obj = {'text': self.text,
                    'properties': self.properties}

        if self.date:
            json_obj['date'] = self.date.strftime("%Y-%m-%dT%H:%M:%S") + 'Z'

        if self.properties:
            json_obj['properties'] = self.properties

        json_obj['tiers'] = {}
        for name, tier in self.tiers.items():
            json_obj['tiers'][name] = tier.to_json()

        return json.dumps(json_obj)

    # TODO needs extensive testing
    def filter_overlapping_spans(self, tier_names=None, decider=None):
        """Remove any overlapping spans from indicated tiers by taking the
        longest span, or using a decider function if one is provided.

        You almost certainly want to provide a list of tier_namess here, because
        tiers like ngrams and tokens will overlap almost all other tiers.

        TODO: A span could be removed if it fails a comparison with a span that
        itself would later be removed. We should use the maximim weight interval
        set approach to do this instead."""

        if not tier_names:
            tiers = list(self.tiers.keys())

        removed_spans_indexes = defaultdict(list)

        tier_a_index = -1
        for tier_name_a in tier_names:
            tier_a = self.tiers[tier_name_a]
            tier_a_index += 1
            retained_spans = []
            a_index = -1
            for span_a in tier_a.spans:
                a_index += 1
                retain_a = True
                tier_b_index = -1
                for tier_name_b in tier_names:
                    tier_b_index += 1
                    tier_b = self.tiers[tier_name_b]
                    b_index = -1
                    for span_b in tier_b.spans:
                        b_index += 1
                        if ( (not b_index in removed_spans_indexes[tier_b_index]) and
                             (not (tier_a_index == tier_b_index and a_index == b_index)) and
                             ( (span_b.start in range(span_a.start, span_a.stop)) or
                               (span_a.start in range(span_b.start, span_b.stop)) ) and
                             (span_b.size() >= span_a.size())
                            ):

                            if not decider or decider(span_a, span_b) is False:
                                retain_a = False
                                removed_spans_indexes[tier_a_index].append(a_index)

                if retain_a:
                    retained_spans.append(span_a)

            self.tiers[tier_name_a].spans = retained_spans


class AnnoTier(object):
    """Container to hold AnnoSpans. Each tier is the """

    def __init__(self, spans=None):
        if spans is None:
            self.spans = []
        else:
            self.spans = spans

    def __repr__(self):
        return str([str(span) for span in self.spans])

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
        return [span for span in self.spans if len(set(range(span.start, span.stop)).
                                       intersection(list(range(start, end)))) > 0]

    def spans_in(self, start, end):
        """Get all spans which are contained in a range"""
        return [span for span in self.spans if span.start >= start and span.stop <= end]

    def spans_at(self, start, end):
        """Get all spans with certain start and end positions"""
        return [span for span in self.spans if start == span.start and end == span.stop]

    def spans_over_span(self, span):
        """Get all spans which overlap another span"""
        return self.spans_over(span.start, span.stop)

    def spans_in_span(self, span):
        """Get all spans which lie within a span"""
        return self.spans_in(span.start, span.stop)

    def spans_at_span(self, span):
        """Get all spans which have the same start and end as another span"""
        return self.spans_at(span.start, span.stop)

    def spans_with_label(self, label):
        """Get all spans which have a given label"""
        return [span for span in self.spans if span.label == label]

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
                    ((span_b.start in range(span_a.start, span_a.stop)) or
                     (span_a.start in range(span_b.start, span_b.stop))) and
                     span_b.size() >= span_a.size()):

                    if not decider or decider(span_a, span_b) is False:
                        retain_a = False
                        removed_spans_indexes.append(a_index)

            if retain_a:
                retained_spans.append(span_a)

        self.spans = retained_spans

class AnnoSpan(object):

    def __repr__(self):
        return '{0}-{1}:{2}'.format(self.start, self.stop, self.label)

    def __init__(self, start, stop, doc, label=None):
        self.start = start
        self.stop = stop
        self.doc = doc

        if label == None:
            self.label = self.text
        else:
            self.label = label

    def overlaps(self, other_span):
        return (
            (self.start >= other_span.start and self.start <= other_span.stop) or
            (other_span.start >= self.start and other_span.start <= self.stop)
        )

    def adjacent_to(self, other_span, max_dist=0):
        return (
            self.comes_before(other_span, max_dist) or
            other_span.comes_before(self, max_dist)
        )

    def comes_before(self, other_span, max_dist=0):
        # Note that this is a strict version of comes before where the
        # span must stop before the other one starts.
        return (
            self.stop >= other_span.start - max_dist - 1 and
            self.stop < other_span.start
        )

    def extended_through(self, other_span):
        """
        Create a new span like this one but with it's range extended through
        the range of the other span.
        """
        return AnnoSpan(
            min(self.start, other_span.start),
            max(self.stop, other_span.stop),
            self.doc,
            self.label
        )

    def size(self): return self.stop - self.start

    @lazy
    def text(self):
        return self.doc.text[self.start:self.stop]

    def to_dict(self):
        """
        Return a json serializable dictionary.
        """
        return dict(
            label=self.label,
            textOffsets=[[self.start, self.stop]]
        )
