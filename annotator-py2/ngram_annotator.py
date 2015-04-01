#!/usr/bin/env python
"""NgramAnnotator creates annotation tiers for n-grams, in the specified range
of values for n. Separate tiers are created for each value of n. The annotator
expects a tier named 'tokens' to exist and to contain spans labeled with tokens
in the order encountered in the text. If the 'tokens' tier is absent, the
default TokenAnnotator will be used to create one."""

from annotator import *
from token_annotator import TokenAnnotator

class NgramAnnotator(Annotator):

    def __init__(self, tokenizer=None):
        pass

    def annotate(self, doc, n_min=1, n_max=7, tier_prefix=''):

        if not 'tokens' in doc.tiers:
            token_annotator = TokenAnnotator()
            doc.add_tier(token_annotator)

        doc.tiers['ngrams'] = AnnoTier()
        for n in range(n_min, n_max + 1):
            doc.tiers[str(n) + 'grams'] = AnnoTier()

        token_spans = doc.tiers['tokens'].spans

        for n in range(n_min, n_max + 1):
            for i in range(len(token_spans)):
                if i + n > len(token_spans):
                    break
                span = AnnoSpan(token_spans[i].start,
                                token_spans[i + n - 1].stop,
                                doc)
                doc.tiers[tier_prefix + 'ngrams'].spans.append(span)
                doc.tiers[tier_prefix + str(n) + 'grams'].spans.append(span)

        # Remove any ngram tiers for which there are no ngrams
        for n in range(n_min, n_max + 1):
            if len(doc.tiers[tier_prefix + str(n) + 'grams'].spans) == 0:
                del(doc.tiers[tier_prefix + str(n) + 'grams'])

        return doc
