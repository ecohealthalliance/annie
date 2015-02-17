#!/usr/bin/env python
"""Write JSON outputs for test run for Draper"""

import sys
import json
import pickle

sys.path = ['./', '../'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.draper.draper_annotator import DraperAnnotator
from annotator.draper.draper_csv_reader import DraperReader
from annotator.geoname_annotator import GeonameAnnotator
from annotator.patient_info_annotator import PatientInfoAnnotator
from annotator.jvm_nlp_annotator import JVMNLPAnnotator
from annotator.keyword_annotator import KeywordAnnotator

class DraperAnnotatorReport():

    def __init__(self, keyword_array_file):

        self.draper_annotator = DraperAnnotator()
        self.geoname_annotator = GeonameAnnotator()
        # self.patient_info_annotator = PatientInfoAnnotator()
        self.jvm_nlp_annotator = JVMNLPAnnotator(['times'])
        self.keyword_annotator = KeywordAnnotator()

        with open(keyword_array_file) as f:
            self.keyword_array = pickle.load(f)

        self.reader = DraperReader()

    def run(self, simple_filename, full_filename):

        tps = []
        fps = []
        tns = []
        fns = []

        i = 0


        simple_results = []
        full_results = []


        for article in self.reader.articles():

            print 'article', article['id']

            i += 1
            if i > 2:
                break

            full_result = {
                'id': article['id']
            }
            simple_result = {
                'id': article['id']
            }

            doc = AnnoDoc(article['text'])

            # Signals (Draper-specific)
            doc.add_tier(self.draper_annotator)
            signals = [
                { 'text': span.text, 'start': span.start, 'stop': span.end }
                for span in doc.tiers['draper'].spans
            ]
            simple_result['signals'] = signals
            full_result['signals'] = signals

            # Datetimes
            doc.add_tier(self.jvm_nlp_annotator)
            datetimes = [
                { 'text': span.text, 'label': span.label,
                  'start': span.start, 'stop': span.end }
                for span in doc.tiers['times'].spans
            ]
            full_result['datetimes'] = datetimes

            # Geonames
            doc.add_tier(self.geoname_annotator)
            geonames = [
                { 'text': span.text, 'label': span.label,
                  'longitude': span.geoname['longitude'], 'latitude': span.geoname['latitude'],
                  'start': span.start, 'stop': span.end }
                for span in doc.tiers['geonames'].spans
            ]
            full_result['geonames'] = geonames

            # Keywords
            doc.add_tier(self.keyword_annotator)
            keyword_types = ['diseases', 'hosts', 'modes', 'pathogens', 'symptoms']
            for keyword_type in keyword_types:
                hits = [ { 'text': span.text, 'label': span.label,
                           'start': span.start, 'stop': span.end }
                    for span in doc.tiers[keyword_type].spans
                ]
                full_result[keyword_type] = hits

            # # Patient info
            # doc.add_tier(self.patient_info_annotator, keyword_categories={
            #     'occupation' : [
            #         kw['keyword'] for kw in self.keyword_array
            #         if 'occupation' in kw['category']
            #     ],
            #     'host' : [
            #         kw['keyword'] for kw in self.keyword_array
            #         if 'host' in kw['category']
            #     ],
            #     'risk' : [
            #         kw['keyword'] for kw in self.keyword_array
            #         if 'risk' in kw['category']
            #     ],
            #     'symptom' : [
            #         kw['keyword'] for kw in self.keyword_array
            #         if 'symptom' in kw['category']
            #     ],
            #     'location' : doc.tiers['geonames'].spans,
            #     'time' : doc.tiers['times'].spans if 'times' in doc.tiers else [],
            # })
            # keypoints = [
            #     { 'text': span.text, 'label': span.label, 'metadata': span.metadata,
            #       'start': span.start, 'stop': span.end }
            #     for span in doc.tiers['patientInfo'].spans
            # ]
            # full_result['keypoints'] = keypoints

            simple_results.append(simple_result)
            full_results.append(full_result)

            print "full_result"
            print full_result
            print
            print "simple_result"
            print simple_result

            if (article['label'] == '1'):
                if (len(doc.tiers['draper'].spans) > 0):
                    print 'tp', article['id']
                    tps.append(article['id'])
                else:
                    fns.append(article['id'])
                    print 'fn', article['id']
            else:
                if (len(doc.tiers['draper'].spans) > 0):
                    fps.append(article['id'])
                    print 'fp', article['id']
                else:
                    tns.append(article['id'])
                    print 'tn', article['id']

        print
        print
        print 'tps', tps
        print 'fps', fps
        print 'tns', tns
        print 'fns', fns

        with open(simple_filename, 'w') as fh:
            fh.write(json.dumps(simple_results, indent=4))

        with open(full_filename, 'w') as fh:
            fh.write(json.dumps(full_results, indent=4))


if __name__ == '__main__':
    reporter = DraperAnnotatorReport(keyword_array_file='../grits-api/keyword_array.p')
    reporter.run('/tmp/s.json', '/tmp/f.json')
