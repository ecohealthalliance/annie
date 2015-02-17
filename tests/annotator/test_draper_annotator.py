#!/usr/bin/env python
"""Test the Draper annotator on the initially provided dataset"""

import sys
import unittest
import test_utils

sys.path = ['./'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.draper.draper_csv_reader import DraperReader
from annotator.draper.draper_annotator import DraperAnnotator

class DraperAnnotatorTest(unittest.TestCase):

    def setUp(self):
        self.annotator = DraperAnnotator()
        reader = DraperReader()
        self.articles = {
            article['id']: article
            for article in reader.articles()
        }

    def test_hospital(self):

        doc = AnnoDoc('There were five people in the hospitals here.')
        doc.add_tier(self.annotator)

        self.assertEqual(len(doc.tiers['leftterms'].spans), 1)
        self.assertEqual(doc.tiers['leftterms'].spans[0].label, "the hospitals")
        self.assertEqual(doc.tiers['leftterms'].spans[0].text, "the hospitals")

    def test_overflow(self):

        doc = AnnoDoc('The place was overflowing with patients.')
        doc.add_tier(self.annotator)

        self.assertEqual(len(doc.tiers['rightterms'].spans), 1)
        self.assertEqual(doc.tiers['rightterms'].spans[0].label, "was overflowing")
        self.assertEqual(doc.tiers['rightterms'].spans[0].text, "was overflowing")

    def test_189605(self):
        doc = AnnoDoc(self.articles['189605']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 2)
        self.assertEqual(doc.tiers['draper'].spans[0].label, 'hospitals were particularly swamped')

    def test_17602(self):
        doc = AnnoDoc(self.articles['17602']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 4)

    def test_3089538(self):
        doc = AnnoDoc(self.articles['3089538']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 0)

    def test_2847076(self):
        doc = AnnoDoc(self.articles['2847076']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 2)

    def test_154987(self):
        doc = AnnoDoc(self.articles['154987']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 1)

    def test_146490(self):
        doc = AnnoDoc(self.articles['146490']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 1)

    def test_142322(self):
        doc = AnnoDoc(self.articles['142322']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 1)

    def test_133782(self):
        doc = AnnoDoc(self.articles['133782']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 1)

    def test_482304(self):
        doc = AnnoDoc(self.articles['482304']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 2)
        self.assertEqual(doc.tiers['draper'].spans[0].label, 'emergency departments are struggling')

    def test_178631(self):
        doc = AnnoDoc(self.articles['178631']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 0)

    def test_2709588(self):
        doc = AnnoDoc(self.articles['2709588']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 0)

    def test_2915988(self):
        doc = AnnoDoc(self.articles['2915988']['text'])
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['draper'].spans), 0)

if __name__ == '__main__':
    unittest.main()
