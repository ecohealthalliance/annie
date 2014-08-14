#!/usr/bin/env python
"""Concept Annotator"""
import math
import re
from collections import defaultdict

import pymongo

from annotator import *
from ngram_annotator import NgramAnnotator
from ne_annotator import NEAnnotator
from geopy.distance import great_circle


class ConceptAnnotator(Annotator):

    def __init__(self, db=None):
        if not db:
            db = pymongo.Connection('localhost', port=27017)['concepts']
        self.concepts_collection = db.concepts
        self.forms_collection = db.forms

        self.min_concept_probability = 0.01
        self.min_link_probability = 0.001

    def annotate(self, doc):

        if 'ngrams' not in doc.tiers:
            ngram_annotator = NgramAnnotator()
            doc.add_tier(ngram_annotator)
            ne_annotator = NEAnnotator()
            doc.add_tier(ne_annotator)

        all_ngrams = set([span.text for span in doc.tiers['ngrams'].spans])

        ngrams_by_lc = defaultdict(list)
        for ngram in all_ngrams:
            ngrams_by_lc[ngram.lower()] += ngram

        forms_cursor = self.forms_collection.find(
                { '_id' : { '$in' : list(all_ngrams) },
                  'lp': { '$gte': self.min_link_probability } } )
        forms = list(forms_cursor)
        print 'forms', forms

        form_concept_ids = set(
            [ concept['id']
              for form in forms
              for concept in form['concepts']
              if concept['prob'] > 0.1]
        )

        print 'form_concept_ids', form_concept_ids

        concepts_cursor = self.concepts_collection.find(
            { '_id' : { '$in' : list(form_concept_ids) } })
        concept_results = list(concepts_cursor)
        concepts = dict([(concept['_id'], concept) for concept in concept_results])
        print "concepts", concepts

        print 'concept_results', concept_results

        forms_candidates = self.get_forms_candidates(forms, concepts)

        print "forms_candidates", forms_candidates

        spans_candidates = self.get_span_candidates(doc, forms_candidates)

        print "spans_candidates", spans_candidates

    def get_forms_candidates(self, forms, concepts):
        """Returns a dict with keys of form ids and values of lists of concept
        candidates for that form
        """

        forms_candidates = defaultdict(list)

        for form in forms:
            print "form", form
            for concept in form['concepts']:
                if concept['id'] in concepts:
                    forms_candidates[form['_id']].append(concepts['concept_id'])

        return forms_candidates

    def get_spans_candidates(self, doc, forms_candidates):
        """Returns a list of tuples consisting of a span and a list of
        candidates for that span
        """

        return [ (span, forms_candidates[span.text])
                 for span in doc.tiers['ngrams'].spans
                 if span.text in forms_candidates ]



    def random_resolver(self, span_candidates):
        """Chooses the resolution concept for a form randomly out of all possible
        candidates. Returns a list of tuples of spans and a concept.
        """
        pass

    def get_seed_concepts():
        """Chooses the resolution concept for a form randomly out of all possible
        candidates.
        """
        pass





