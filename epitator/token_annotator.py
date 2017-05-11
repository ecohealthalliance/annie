#!/usr/bin/env python
"""Token Annotator"""
from annotator import Annotator, AnnoSpan, AnnoTier
from spacy_annotator import SpacyAnnotator


class TokenAnnotator(Annotator):
    def annotate(self, doc):
        if 'spacy.tokens' not in doc.tiers:
            doc.add_tier(SpacyAnnotator())
        doc.tiers['tokens'] = doc.tiers['spacy.tokens']
        return doc
