#!/usr/bin/env python
# coding=utf8
"""Annotator"""
import json
import re
from lazy import lazy
from collections import defaultdict

from nltk import sent_tokenize

from . import maximum_weight_interval_set as mwis

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
        if type(text) is str:
            self.text = text
        elif type(text) is str:
            self.text = str(text, 'utf8')
        else:
            raise TypeError("text must be string or unicode")
        # Replacing the unicode dashes is done to avoid this pattern bug:
        # https://github.com/clips/pattern/issues/104
        self.text = self.text.replace("—", "-")
        self.tiers = {}
        self.properties = {}
        self.date = date

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
        for name, tier in self.tiers.items():
            json_obj['tiers'][name] = tier.to_json()

        return json.dumps(json_obj)

    def filter_overlapping_spans(self, tier_names=None):
        """Remove the smaller of any overlapping spans."""
        if not tier_names:
            tiers = list(self.tiers.keys())
        for tier_name in tier_names:
            if tier_name not in self.tiers: continue
            tier = self.tiers[tier_name]
            my_mwis = mwis.find_maximum_weight_interval_set([
                mwis.Interval(
                    start=span.start,
                    end=span.end,
                    weight=(span.end - span.start),
                    corresponding_object=span
                )
                for span in tier.spans
            ])
            tier.spans =  [
                interval.corresponding_object
                for interval in my_mwis
            ]

class AnnoTier(object):

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

        # This is to allow us to serialize set() objects.
        def set_default(obj):
            if isinstance(obj, set):
                return list(obj)
            raise TypeError

        docless_spans = []
        for span in self.spans:
            span_dict = span.__dict__.copy()
            del span_dict['doc']
            docless_spans.append(span_dict)

        return json.dumps(docless_spans, default=set_default)

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
        return [span for span in self.spans if len(set(range(span.start, span.end)).
                                       intersection(list(range(start, end)))) > 0]

    def spans_in(self, start, end):
        """Get all spans which are contained in a range"""
        return [span for span in self.spans if span.start >= start and span.end <= end]

    def spans_at(self, start, end):
        """Get all spans with certain start and end positions"""
        return [span for span in self.spans if start == span.start and end == span.end]

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
        return [span for span in self.spans if span.label == label]

    def labels(self):
        """Get a list of all labels in this tier"""
        return [span.label for span in self.spans]

    def sort_spans(self):
        """Sort spans by order of start"""

        self.spans.sort(key=lambda span: span.start)

    def filter_overlapping_spans(self, score_func=None):
        """Remove the smaller of any overlapping spans."""
        my_mwis = mwis.find_maximum_weight_interval_set([
            mwis.Interval(
                start=span.start,
                end=span.end,
                weight=score_func(span) if score_func else (span.end - span.start),
                corresponding_object=span
            )
            for span in self.spans
        ])
        self.spans =  [
            interval.corresponding_object
            for interval in my_mwis
        ]

class AnnoSpan(object):

    def __repr__(self):
        return '{0}-{1}:{2}'.format(self.start, self.end, self.label)

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
        Create a new span like this one but with it's range extended through
        the range of the other span.
        """
        return AnnoSpan(
            min(self.start, other_span.start),
            max(self.end, other_span.end),
            self.doc,
            self.label
        )

    def size(self): return self.end - self.start

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
