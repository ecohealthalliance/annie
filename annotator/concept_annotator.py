#!/usr/bin/env python
"""Concept Annotator"""
import math
import re
from collections import defaultdict
import random
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

import pymongo

from annotator import *
from ngram_annotator import NgramAnnotator
from pos_annotator import POSAnnotator
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
        self.min_key_span_score = 0.90
        self.min_vector_score = 0.2

        self.distances = {}

    def annotate(self, doc):

        if 'ngrams' not in doc.tiers:
            logger.info('add ngrams tier')
            ngram_annotator = NgramAnnotator()
            doc.add_tier(ngram_annotator)
            logger.info('added ngrams tier')

        if 'nes' not in doc.tiers:
            logger.info('adding ne tier')
            ne_annotator = NEAnnotator()
            doc.add_tier(ne_annotator)
            logger.info('added ne tier')

        if 'pos' not in doc.tiers:
            logger.info('adding pos tier')
            pos_annotator = POSAnnotator()
            doc.add_tier(pos_annotator)
            logger.info('added pos tier')

        all_ngrams = set([span.text for span in doc.tiers['ngrams'].spans])
        logger.debug("all_ngrams", all_ngrams)
        ngrams_by_lc = defaultdict(list)
        for ngram in all_ngrams:
            ngrams_by_lc[ngram.lower()] += ngram

        forms_cursor = self.forms_collection.find(
                { '_id' : { '$in' : list(all_ngrams) } } )
                # Add back once we have lp data for forms
                # 'lp': { '$gte': self.min_link_probability } } )
        forms = list(forms_cursor)
        logger.info('got forms')
        form_ids = [ form['_id'] for form in forms ]
        concepts = [ concept
                     for  form in forms
                     for concept in form['concepts'] ]
        logger.info('got concepts')
        for concept in concepts:
            logger.debug(concept)
        print
        print
        print 'forms', forms
        print
        print 'form_ids', form_ids
        print

        form_concept_ids = set(
            [ concept['id']
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

        # self.get_all_concept_distances(concepts)

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

        spans_candidate_vectors = self.get_spans_candidates_vectors(spans_candidates)

        print "spans_candidate_vectors", spans_candidate_vectors
        print

        key_spans, coy_spans = self.get_key_spans(spans_candidate_vectors)

        self.compare_vectors(key_spans, coy_spans)

        resolved_spans, unresolved_spans = self.vector_score_resolver(coy_spans)

        retained_spans = [ (span, candidate_vectors)
                           for span, candidate_vectors in resolved_spans
                           if self.retain_resolution(candidate_vectors[0]) ]

        print "resolved_spans", resolved_spans
        print

        concept_spans = [ AnnoSpan(span.start, span.end, doc, label=candidate_vectors[0]['concept']['_id'])
                          for span, candidate_vectors in retained_spans ]

        for key_span, candidate_vectors in key_spans:
            concept_spans.append(
                AnnoSpan(key_span.start, key_span.end, doc, label=candidate_vectors[0]['concept']['_id']))

        doc.tiers['concepts'] = AnnoTier(concept_spans)
        doc.tiers['concepts'].filter_overlapping_spans()
        doc.tiers['concepts'].sort_spans()


    ## CANDIDATES ##
    def get_spans_candidates(self, doc, forms_candidates):
        """Returns a list of tuples consisting of a span and a list of
        (prob, candidate) tuples for that span
        """

        return [ (span, forms_candidates[span.text])
                 for span in doc.tiers['ngrams'].spans
                 if span.text in forms_candidates ]

    def get_forms_candidates(self, forms, concepts):
        """Returns a dict with keys of form ids and values of lists of tuples
         of probabilities and concept candidates for that form
        """

        forms_candidates = defaultdict(list)

        for form in forms:
            print "form", form
            for concept in form['concepts']:
                print 'concept', concept
                if concept['id'] in concepts:
                    forms_candidates[form['_id']].append(
                        (concept['prob'], concepts[concept['id']]))

        return forms_candidates


    ## DISTANCE ##
    def get_concept_pair_key(self, concept_a, concept_b):
        sorted_ids = sorted((concept_a['_id'], concept_b['_id']))
        return (sorted_ids[0], sorted_ids[1])

    def get_distance(self, concept_a, concept_b):

        return great_circle( (concept_a['lat'], concept_a['lon']),
                             (concept_b['lat'], concept_b['lon']) ).kilometers

    def get_all_concept_distances(self, concepts):
        """Pre-calculate the distances between each candidate concept pair"""

        for concept_id_a, concept_a in concepts.iteritems():
            for concept_id_b, concept_b in concepts.iteritems():
                if concept_id_a != concept_id_b:
                    if 'lat' in concept_a and 'lat' in concept_b:
                        key = self.get_concept_pair_key(concept_a, concept_b)
                        if key not in self.distances:
                            self.distances[key] = \
                                self.get_concepts_distance(concept_a, concept_b)

    def get_concepts_distance(self, concept_a, concept_b):
        """Get the pre-calculated distance between a concept pair, or calculate
        and cache it if not found."""


        if 'lat' in concept_a and 'lat' in concept_b:
            key = self.get_concept_pair_key(concept_a, concept_b)
            if key in self.distances:
                return self.distances[key]
            else:
                distance = self.get_distance(concept_a, concept_b)
                self.distances[key] = distance
                return distance

    def score_distances(self, vector, key_spans, coy_spans):
        """Assign a score to a concept candidate based on its distance from the
        resolved spans and other candidate spans"""

        key_distances = [
            self.get_concepts_distance(vector['concept'], candidate_vectors[0]['concept'])
            for key_span, candidate_vectors in key_spans
        ]

        key_distance_score = sum([
            self.score_distance(key_distance)
            for key_distance in key_distances
        ])

        # Weight the non-key distance scores by the form_concept_prob of the
        # candidate concept for that form.
        coy_distances = [
            (candidate_vector['form_concept_prob'] *
             self.get_concepts_distance(vector['concept'], candidate_vector['concept']))
            for coy_span, candidate_vectors in coy_spans
            for candidate_vector in candidate_vectors
            if vector['concept'] != candidate_vector['concept']
        ]

        coy_distance_score = sum([
            self.score_distance(coy_distance)
            for coy_distance in coy_distances
        ])

        return (key_distance_score, coy_distance_score)

    def score_distance(self, distance):
        """Assign and integer score to a distance. Work in progress"""

        if distance < 10:
            return 100
        elif distance < 50:
            return 50
        elif distance < 100:
            return 20
        elif distance < 200:
            return 10
        elif distance < 500:
            return 5
        elif distance < 1000:
            return 1
        else:
            return 0


    ## VECTORS ##
    def get_spans_candidates_vectors(self, spans_candidates):

        spans_candidate_vectors = []
        for span, candidates in spans_candidates:

            sorted_candidates = sorted(candidates, reverse=True)

            print "sorted_candidates:", sorted_candidates
            print

            span_candidates_vectors = []
            for prob, candidate in candidates:
                vector = {}
                vector['form'] = span.text
                vector['concept'] = candidate
                vector['form_concept_prob'] = prob
                key_span_score = self.get_key_span_score(vector)
                vector['key_span_score'] = key_span_score

                pos_span = span.overlap_in_tier(span.doc.tiers['pos'])
                if pos_span:
                    vector['pos'] = pos_span.label
                else:
                    vector['pos'] = None

                nes_span = span.overlap_in_tier(span.doc.tiers['nes'])
                if nes_span:
                    vector['named_entity'] = nes_span.label
                else:
                    vector['named_entity'] = None

                span_candidates_vectors.append(vector)
            spans_candidate_vectors.append((span, span_candidates_vectors))

        return spans_candidate_vectors

    def compare_vectors(self, key_spans, coy_spans):
        """Take the key_span and coy_span candidate_vectors and populate
        the coy_span candidate_vectors with attributes derived from their
        similarity to the key_span candidate_vectors."""

        for coy_span, candidate_vectors in coy_spans:
            for candidate_vector in candidate_vectors:
                key_distance_score, coy_distance_score = \
                    self.score_distances(candidate_vector, key_spans, coy_spans)
                candidate_vector['key_distance_score'] = key_distance_score
                candidate_vector['coy_distance_score'] = coy_distance_score

    def pos_is_nounish(self, pos):
        """Is the pos tag a noun-like one?
        NN, NNS, NNP, NNPS are noun-like.
        """
        print "ne_is_location_like", pos
        if pos in set(['NN', 'NNS', 'NNP', 'NNPS']):
            print "TRUE"
            return True
        else:
            return False

    def ne_is_location_like(self, named_entity):
        """Is the named entity tag a location-like one?
        ORGANIZATION, LOCATION, FACILITY and GPE are likely to be locations."""

        if named_entity and named_entity in ['ORGANIZATION', 'LOCATION', 'FACILITY', 'GPE']:
            return True
        else:
            return False

    ## KEY SPANS ##
    def get_key_spans(self, spans_candidate_vectors):
        """Find high-probability spans to use as keys for resolving the other
        spans."""

        key_spans = []
        coy_spans = []

        for span, candidate_vectors in spans_candidate_vectors:
            sorted_vectors = sorted(candidate_vectors,
                                    key=lambda vector: vector['key_span_score'],
                                    reverse=True)

            if sorted_vectors[0]['key_span_score'] > self.min_key_span_score:
                key_spans.append((span, sorted_vectors))
            else:
                coy_spans.append((span, sorted_vectors))

        return (key_spans, coy_spans)

    def get_key_span_score(self, vector):
        return vector['form_concept_prob']


    ## RESOLVERS ##
    def random_resolver(self, spans_candidates):
        """Chooses the resolution concept for a form randomly out of all possible
        candidates. Returns a list of tuples of spans and a concept.
        """
        return [ (span, random.choice(candidates))
                 for span, candidates in spans_candidates ]

    def retain_resolution(self, vector):

        print '\n\n\nretain:', vector['form'], vector['concept'], vector['vector_score'], vector['pos'], vector['named_entity']

        location_like = self.ne_is_location_like(vector['named_entity'])
        noun_like = self.pos_is_nounish(vector['pos'])

        print 'location_like', location_like
        print 'noun_like', noun_like

        if location_like:
            print "is location-like"
            if noun_like:
                print "is nounlike"
                if vector['vector_score'] >= 0.2:
                    print "True"
                    return True
            else:
                if vector['vector_score'] >= 0.4:
                    print "True"
                    return True
        else:
            if noun_like:
                if vector['vector_score'] >= 0.4:
                    print "True"
                    return True
            else:
                if vector['vector_score'] >= 0.95:
                    print "True"
                    return True

        return False

    def get_vector_score(self, vector):
        """Get a single overall score for a candidate vector"""

        vector['vector_score'] = vector['form_concept_prob']

        print "vector['form']", vector['form']
        print "vector['concept']", vector['concept']
        print "vector['pos']", vector['pos']
        print "vector['named_entity']", vector['named_entity']
        print "vector['form_concept_prob']", vector['form_concept_prob']
        print "vector['vector_score']", vector['vector_score']
        print "vector['key_distance_score']", vector['key_distance_score']
        print "vector['coy_distance_score']", vector['coy_distance_score']
        print

        return vector['vector_score']

    def vector_score_resolver(self, spans):
        """Chooses the resolution concept for a span based on an overall score
        computed from the candidate vectors.
        """

        resolved_spans = []
        unresolved_spans = []

        for span, candidate_vectors in spans:
            sorted_vectors = sorted(candidate_vectors,
                                    key=lambda vector: self.get_vector_score(vector),
                                    reverse=True)

            if sorted_vectors[0]['vector_score'] > self.min_vector_score:
                resolved_spans.append((span, sorted_vectors))
            else:
                unresolved_spans.append((span, sorted_vectors))

        return (resolved_spans, unresolved_spans)

    def iterative_resolver():
        """Chooses the resolution concept for a span by iteratively resolving the
        most promising candidates at each pass.
        """
        pass
