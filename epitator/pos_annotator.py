#!/usr/bin/env python
"""Part of speech tag annotator"""
from annotator import Annotator, AnnoSpan, AnnoTier
from spacy_annotator import SpacyAnnotator


class POSAnnotator(Annotator):

    def annotate(self, doc):
        if 'spacy.tokens' not in doc.tiers:
            doc.add_tier(SpacyAnnotator())
        pos_spans = [AnnoSpan(span.start, span.end, doc, label=span.token.tag_)
                     for span in doc.tiers['spacy.tokens'].spans]
        doc.tiers['pos'] = AnnoTier(pos_spans)
        return doc
