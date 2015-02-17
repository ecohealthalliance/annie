#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the DraperAnnotator that annotates a sentence with locations from
the Geonames dataset."""

import sys
import os
import unittest

sys.path = ['./'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.draper_annotator import DraperAnnotator
from annotator.draper_csv_reader import DraperReader
import logging
logging.getLogger('annotator.draper_annotator').setLevel(logging.ERROR)

class DraperAnnotatorEval():

    def __init__(self):

        self.annotator = DraperAnnotator()
        self.reader = DraperReader()

    def run(self):

        tps = []
        fps = []
        tns = []
        fns = []

        i = 0

        for article in self.reader.articles():

            i += 1
            if i > 20000:
                break

            doc = AnnoDoc(article['text'])
            doc.add_tier(self.annotator)

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





if __name__ == '__main__':
    evaler = DraperAnnotatorEval()
    evaler.run()
