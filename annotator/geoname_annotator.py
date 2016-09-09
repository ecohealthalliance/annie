#!/usr/bin/env python
"""Geoname Annotator"""
import math
import re
import itertools
from pymongo import MongoClient
import os

from .annotator import *
from .ngram_annotator import NgramAnnotator
from .ne_annotator import NEAnnotator
from geopy.distance import great_circle
from .maximum_weight_interval_set import Interval, find_maximum_weight_interval_set

import datetime
import logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

def geoname_matches_original_ngram(geoname, original_ngrams):
    if (geoname['name'] in original_ngrams):
        return True
    else:
        for original_ngram in original_ngrams:
            if original_ngram in geoname['alternatenames']:
                return True

    return False

# TODO: We might be able to remove some of these names in a more general way
# by adding a feature to the scoring function.
blocklist = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
    'August', 'September', 'October', 'November', 'December',
    'North', 'East', 'West', 'South',
    'Northeast', 'Southeast', 'Northwest', 'Southwest',
    'Eastern', 'Western', 'Southern', 'Northern',
    'About', 'Many', 'See', 'As', 'About', 'Health',
    'International', 'City', 'World', 'Federal', 'Federal District',
    'British', 'Russian',
    'Valley', 'University', 'Center', 'Central',
    # These locations could be legitimate,
    # but they are rarely referred to in a context
    # where its location is relevent.
    'National Institutes of Health',
    'Centers for Disease Control',
    'Ministry of Health and Sanitation',
]

def location_contains(loc_outer, loc_inner):
    """
    Do a comparison to see if one geonames location contains another.
    It returns an integer to indicate how specific the containment is.
    USA contains Texas should be a smaller integer than WA contains Seattle.
    0 indicates no containment. Siblings locations and identical locations
    have 0 containment.
    This is not guarenteed to be correct, it is based on my assumptions
    about the geonames heirarchy.
    """
    # This doesn't work for every feature class
    # ADM... or PPL... features are most likely to work.
    # I'm not sure how to deal with RGN and CONT, the geonames website has
    # a parent heirarchy in the UI but I'm not sure where the data comes from.
    props = [
        'country code',
        'admin1 code',
        'admin2 code',
        'admin3 code',
        'admin4 code'
    ]
    for idx, prop in enumerate(props):
        if len(loc_outer[prop]) == 0:
            if len(loc_inner[prop]) == 0:
                return 0 # locations appear to be siblings/identical
            else:
                return idx
        if loc_outer[prop] != loc_inner[prop]:
            return 0
    return 0 # locations appear to be siblings/identical

class GeoSpan(AnnoSpan):
    def __init__(self, start, end, doc, geoname):
        self.start = start
        self.end = end
        self.doc = doc
        self.geoname = geoname
        self.label = geoname['name']
    def to_dict(self):
        result = super(GeoSpan, self).to_dict()
        result.update(self.geoname)
        return result

class Location(dict):
    """
    This main purpose of this class is to create hashable dictionaries
    that we can use in sets.
    """
    def __hash__(self):
        return id(self)

def feature(fun):
    """
    A decorator for designatic which methods are used to create features.
    """
    fun.is_feature = True
    return fun

class GeonameFeatures(object):
    def __init__(self, geoname):
        self.geoname = geoname
        self.feature_dict = {
            feature_name: feature_fun(self)
            for feature_name, feature_fun in GeonameFeatures.__dict__.items()
            if hasattr(feature_fun, "is_feature") }
    @feature
    def population_score(self):
        geoname = self.geoname
        if geoname['population'] > 1000000:
            return 100
        elif geoname['population'] > 500000:
            return 60
        elif geoname['population'] > 300000:
            return 40
        elif geoname['population'] > 200000:
            return 30
        elif geoname['population'] > 100000:
            return 20
        elif geoname['population'] > 10000:
            return 5
        else:
            return 0
    @feature
    def synonymity(self):
        geoname = self.geoname
        # Geonames with lots of alternate names
        # tend to be the ones most commonly referred to.
        # For example, coutries have lots of alternate names.
        if len(geoname['alternatenames']) > 8:
            return 100
        elif len(geoname['alternatenames']) > 4:
            return 50
        elif len(geoname['alternatenames']) > 0:
            return 10
        else:
            return 0
    @feature
    def num_spans_score(self):
        geoname = self.geoname
        return min(len(geoname['spans']), 4) * 25
    @feature
    def short_span_score(self):
        geoname = self.geoname
        max_span_length = max([
            len(span.text) for span in geoname['spans']
        ])
        if max_span_length < 4:
            return 100
        elif max_span_length < 5:
            return 10
        else:
            return 0
    @feature
    def cannonical_name_used(self):
        geoname = self.geoname
        return 100 if any([
            span.text == geoname['name'] for span in geoname['spans']
        ]) else 0
    @feature
    def NEs_contained(self):
        geoname = self.geoname
        NE_overlap = 0
        total_len = 0
        for span in geoname['spans']:
            ne_spans = span.doc.tiers['nes'].spans_in_span(span)
            total_len += len(span.text)
            for ne_span in ne_spans:
                if ne_span.label == 'GPE':
                    NE_overlap += len(ne_span.text)
        return float(100 * NE_overlap) / total_len
    @feature
    def distinctness(self):
        geoname = self.geoname
        return 100 / float(len(geoname['alternateLocations']) + 1)
    @feature
    def max_span_score(self):
        geoname = self.geoname
        max_span = max([
            len(span.text) for span in geoname['spans']
        ])
        if max_span < 5: return 0
        elif max_span < 8: return 40
        elif max_span < 10: return 60
        elif max_span < 15: return 80
        else: return 100
    # def close_locations(self):
    #     geoname = self.geoname
    #     if len(resolved_locations) == 0: return 0
    #     count = 0
    #     for location in resolved_locations:
    #         distance = great_circle(
    #             (geoname['latitude'], geoname['longitude']),
    #             (location['latitude'], location['longitude'])
    #         ).kilometers
    #         if distance < 500:
    #             count += 1
    #     return 100 * float(count) / len(resolved_locations)
    # def closest_location(self):
    #     geoname = self.geoname
    #     if len(resolved_locations) == 0: return 0
    #     closest = min([
    #         great_circle(
    #             (geoname['latitude'], geoname['longitude']),
    #             (location['latitude'], location['longitude'])
    #         ).kilometers
    #         for location in resolved_locations
    #     ])
    #     if closest < 10:
    #         return 100
    #     elif closest < 100:
    #         return 60
    #     elif closest < 1000:
    #         return 40
    #     else:
    #         return 0
    # def containment_level(self):
    #     geoname = self.geoname
    #     max_containment_level = max([
    #         max(
    #             location_contains(location, geoname),
    #             location_contains(geoname, location)
    #         )
    #         for location in resolved_locations
    #     ] + [0])
    #     if max_containment_level == 0:
    #         return 0
    #     else:
    #         return 40 + max_containment_level * 10
    @feature
    def feature_code_score(self):
        geoname = self.geoname
        for code, score in list({
            # Continent (need this bc Africa has 0 population)
            'CONT' : 100,
            'ADM' : 80,
            'PPL' : 65,
        }.items()):
            if geoname['feature code'].startswith(code):
                return score
        return 0
    def to_dict(self):
        return self.feature_dict
    def score(self, feature_weights):
        """
        Return a score between 0 and 100
        """
        total_score = sum([
            self.feature_dict[feature_name] * float(weight)
            for feature_name, weight in list(feature_weights.items())
        ]) / math.sqrt(sum([x**2 for x in list(feature_weights.values())]))
        return total_score

class GeonameAnnotator(Annotator):
    def __init__(self, geonames_collection=None):
        if not geonames_collection:
            if 'MONGO_URL' in os.environ:
                mongo_url = os.environ['MONGO_URL']
            else:
                mongo_url = 'mongodb://localhost:27017'

            client = MongoClient(mongo_url)
            db = client.geonames
            geonames_collection = db.allCountries
        assert geonames_collection.count() > 0
        self.geonames_collection = geonames_collection

    def get_candidate_geonames(self, doc):
        """
        Returns an array of geoname dicts correponding to locations that the document may refer to.
        The dicts are extended with lists of associated AnnoSpans.
        """
        if 'ngrams' not in doc.tiers:
            ngram_annotator = NgramAnnotator()
            doc.add_tier(ngram_annotator)
        if 'nes' not in doc.tiers:
            ne_annotator = NEAnnotator()
            doc.add_tier(ne_annotator)
        logger.info('Named entities annotated')
        all_ngrams = set([span.text
            for span in doc.tiers['ngrams'].spans
            if span.text not in blocklist and
            # We can rule out a few FPs by only looking at capitalized names.
            span.text[0] == span.text[0].upper()
        ])
        logger.info('%s ngrams extracted' % len(all_ngrams))
        geoname_cursor = self.geonames_collection.find({
            '$or' : [
                { 'name' : { '$in' : list(all_ngrams) } },
                # I suspect using multiple indecies slows this
                # query down by a factor of two. It might be worthwhile
                # to add name to alternate names so we can just
                # search on that property.
                { 'alternatenames' : { '$in' : list(all_ngrams) } }
            ]
        })
        geoname_results = list(geoname_cursor)
        logger.info('%s geonames fetched' % len(geoname_results))
        # ObjectId() cannot be JSON serialized so keeping is a nuisance
        for geoname_result in geoname_results:
            del geoname_result['_id']
        # Associate spans with the geonames.
        # This is done up front so span information can be used in the scoring
        # function
        span_text_to_spans = {
            span.text : []
            for span in doc.tiers['ngrams'].spans
        }
        for span in doc.tiers['ngrams'].spans:
            span_text_to_spans[span.text].append(span)
        candidate_locations = []
        for location_dict in geoname_results:
            location = Location(location_dict)
            location['spans'] = set()
            location['alternateLocations'] = set()
            candidate_locations.append(location)
            geoname_results
            names = set([location['name']] + location['alternatenames'])
            for name in names:
                if name not in span_text_to_spans: continue
                for span in span_text_to_spans[name]:
                    location['spans'].add(span)
        # Add combined spans to locations that are adjacent to a span linked to
        # an administrative division. e.g. Seattle, WA
        span_to_locations = {}
        for location in candidate_locations:
            for span in location['spans']:
                span_to_locations[span] =\
                    span_to_locations.get(span, []) + [location]
        for span_a, span_b in itertools.permutations(
            list(span_to_locations.keys()), 2
        ):
            if not span_a.comes_before(span_b, max_dist=4): continue
            if (
                len(
                    set(span_a.doc.text[span_a.end:span_b.start]) - set(", ")
                ) > 1
            ): continue
            combined_span = span_a.extended_through(span_b)
            possible_locations = []
            for loc_a, loc_b in itertools.product(
                span_to_locations[span_a],
                span_to_locations[span_b],
            ):
                # print 'loc:', loc_a['name'], loc_b['name'], loc_b['feature code']
                if(
                    loc_b['feature code'].startswith('ADM') and
                    loc_a['feature code'] != loc_b['feature code']
                ):
                    if location_contains(loc_b, loc_a) > 0:
                        loc_a['spans'].add(combined_span)
                        loc_a['parentLocation'] = loc_b
        # Find locations with overlapping spans
        for idx, location_a in enumerate(candidate_locations):
            a_spans = location_a['spans']
            for idx, location_b in enumerate(candidate_locations[idx + 1:]):
                b_spans = location_b['spans']
                if len(a_spans & b_spans) > 0:
                    # Note that is is possible for two valid locations to have
                    # overlapping names. For example, Harare Province has
                    # Harare as an alternate name, so the city Harare is very
                    # to be an alternate location that competes with it.
                    location_a['alternateLocations'].add(location_b)
                    location_b['alternateLocations'].add(location_a)
        logger.info('%s candidate locations prepared' % len(candidate_locations))
        return candidate_locations
    def extract_features(self, locations):
        return [GeonameFeatures(location) for location in locations]
    def cull_geospans(self, geo_spans):
        mwis = find_maximum_weight_interval_set([
            Interval(
                geo_span.start,
                geo_span.end,
                # If the size is equal the score is used as a tie breaker.
                # This formula makes the score the last digit of the weight.
                (geo_span.size() * 10 + (geo_span.geoname['score'] / 11)),
                geo_span
            )
            for geo_span in geo_spans
        ])
        retained_spans = [interval.corresponding_object for interval in mwis]
        logger.info('overlapping geospans removed')
        return retained_spans
    def annotate(self, doc):
        logger.info('geoannotator started')
        candidate_locations = self.get_candidate_geonames(doc)
        features = self.extract_features(candidate_locations)
        feature_weights = dict(
            population_score=2.0,
            synonymity=1.0,
            num_spans_score=0.4,
            short_span_score=(-5),
            NEs_contained=1.2,
            # Distinctness is probably more effective when combined
            # with other features
            distinctness=1.0,
            max_span_score=1.0,
            # close_locations=0.8,
            # closest_location=0.8,
            # containment_level=0.8,
            cannonical_name_used=0.5,
            feature_code_score=0.6,
        )
        for location, feature in zip(candidate_locations, features):
            location['score'] = feature.score(feature_weights)
        culled_locations = [location
            for location in candidate_locations
            if location['score'] > 50]
        geo_spans = []
        for location in culled_locations:
            # Copy the dict so we don't need to return a custom class.
            location = dict(location)
            for span in location['spans']:
                # TODO: Adjust scores to give geospans that exactly match
                # a corresponding geoname a bonus.
                geo_span = GeoSpan(
                    span.start, span.end, doc, location
                )
                geo_spans.append(geo_span)
        culled_geospans = self.cull_geospans(geo_spans)
        # Remove unneeded properties:
        # Be careful if adding these back in, they might not be serializable
        # data types.
        props_to_omit = ['spans', 'alternatenames']
        for geospan in culled_geospans:
            # The while loop removes the properties from the parentLocations.
            # There will probably only be one parent location.
            cur_location = geospan.geoname
            while True:
                if all([
                    prop not in cur_location
                    for prop in props_to_omit
                ]):
                    break
                for prop in props_to_omit:
                    cur_location.pop(prop)
                if 'parentLocation' in cur_location:
                    cur_location = cur_location['parentLocation']
                else:
                    break
        doc.tiers['geonames'] = AnnoTier(culled_geospans)
        return doc
