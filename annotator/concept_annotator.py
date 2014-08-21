#!/usr/bin/env python
"""Concept Annotator"""
import math
import re
from collections import defaultdict
import random

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

        self.distances = {}

    def annotate(self, doc):

        if 'ngrams' not in doc.tiers:
            ngram_annotator = NgramAnnotator()
            doc.add_tier(ngram_annotator)
            ne_annotator = NEAnnotator()
            doc.add_tier(ne_annotator)

        all_ngrams = set([span.text for span in doc.tiers['ngrams'].spans])
        print "all_ngrams", all_ngrams
        ngrams_by_lc = defaultdict(list)
        for ngram in all_ngrams:
            ngrams_by_lc[ngram.lower()] += ngram

        forms_cursor = self.forms_collection.find(
                { '_id' : { '$in' : list(all_ngrams) } } )
                # Add back once we have lp data for forms
                # 'lp': { '$gte': self.min_link_probability } } )
        forms = list(forms_cursor)
        print 'forms', forms
        print

        form_concept_ids = set(
            [ concept['concept']
              for form in forms
              for concept in form['concepts']
            ]
        )

        print 'form_concept_ids', form_concept_ids
        print

        concepts_cursor = self.concepts_collection.find(
            { '_id' : { '$in' : list(form_concept_ids) } })
        concept_results = list(concepts_cursor)
        concepts = dict([(concept['_id'], concept) for concept in concept_results])
        print "concepts", concepts
        print

        self.get_all_concept_distances(concepts)

        print "self.distances", self.distances
        print

        print 'concept_results', concept_results
        print

        forms_candidates = self.get_forms_candidates(forms, concepts)

        print "forms_candidates", forms_candidates
        print

        spans_candidates = self.get_spans_candidates(doc, forms_candidates)

        print "spans_candidates", spans_candidates
        print

        spans_vectors = self.get_spans_vectors(spans_candidates)

        print "spans_vectors", spans_vectors
        print

        resolved_spans = self.random_resolver(spans_candidates)

        print "resolved_spans", resolved_spans
        print

        concept_spans = [ AnnoSpan(span.start, span.end, doc, label=concept['_id'])
                          for span, concept in resolved_spans ]

        doc.tiers['concepts'] = AnnoTier(concept_spans)

    def get_forms_candidates(self, forms, concepts):
        """Returns a dict with keys of form ids and values of lists of tuples
         of probabilities and concept candidates for that form
        """

        forms_candidates = defaultdict(list)

        for form in forms:
            print "form", form
            for concept in form['concepts']:
                print 'concept', concept
                if concept['concept'] in concepts:
                    forms_candidates[form['_id']].append((concept['prob'], concepts[concept['concept']]))

        return forms_candidates

    def get_all_concept_distances(self, concepts):
        """Pre-calculate the distances between each candidate concept pair"""

        for concept_id_a, concept_a in concepts.iteritems():
            for concept_id_b, concept_b in concepts.iteritems():
                if concept_id_a != concept_id_b:
                    if 'lat' in concept_a and 'lat' in concept_b:
                        key = self.get_concept_pair_key(concept_a, concept_b)
                        if key not in self.distances:
                            self.distances[key] = \
                                self.distance(concept_a, concept_b)

    def get_concept_distance(self, concept_a, concept_b):
        """Get the pre-calculated distance between a concept pair, or calculate
        and cache it otherwise."""

        key = self.get_concept_pair_key(concept_a, concept_b)


        for concept_id_a, concept_a in concepts.iteritems():
            for concept_id_b, concept_b in concepts.iteritems():
                if concept_id_a != concept_id_b:
                    if 'lat' in concept_a and 'lat' in concept_b:

                        if key not in self.distances:
                            self.distances[key] = \
                                self.distance(concept_a, concept_b)

    def get_spans_vectors(self, spans_candidates):

        spans_vectors = []
        for span, candidates in spans_candidates:
            span_vectors = []
            for prob, candidate in candidates:
                vector = {}
                vector['concept'] = candidate
                vector['form_concept_prob'] = prob
                span_vectors.append(vector)
            spans_vectors.append((span, span_vectors))

        return spans_vectors

    def score_vector(self, vector, resolved_spans):
        resolved_distances = [self.]
        vector['form_concept_prob'] *


    def get_concept_pair_key(self, concept_a, concept_b):
        sorted_ids = sorted((concept_a['_id'], concept_b['_id']))
        return (sorted_ids[0], sorted_ids[1])


    def get_spans_candidates(self, doc, forms_candidates):
        """Returns a list of tuples consisting of a span and a list of
        (prob, candidate) tuples for that span
        """

        return [ (span, forms_candidates[span.text])
                 for span in doc.tiers['ngrams'].spans
                 if span.text in forms_candidates ]



    def random_resolver(self, spans_candidates):
        """Chooses the resolution concept for a form randomly out of all possible
        candidates. Returns a list of tuples of spans and a concept.
        """
        return [ (span, random.choice(candidates))
                 for span, candidates in spans_candidates ]



    def iterative_resolver():
        """Chooses the resolution concept for a span by iteratively resolving the
        most promising candidates at each pass.
        """
        pass


    def distance(self, concept_a, concept_b):

        return great_circle( (concept_a['lat'], concept_a['lon']),
                             (concept_b['lat'], concept_b['lon']) ).kilometers




