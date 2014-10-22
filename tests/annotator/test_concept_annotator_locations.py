#!/usr/bin/env python
"""Tests for the ConcepAnnotator that annotates a sentence with tokens and their
offsets."""

import sys
import os
import unittest

sys.path = ['./'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.concept_annotator import ConceptAnnotator


class ConceptAnnotatorTest(unittest.TestCase):


    def test_ireland(self):

        annotator = ConceptAnnotator()

        text = 'I went from Bangor, Ireland to Bangor, Maine in America, that is Maine in the United States of America.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)
        print
        print
        for span in doc.tiers['concepts'].spans:
            print span.label, ' :: ', span.text
        print
        print

        self.assertEqual(len(doc.tiers['concepts'].spans), 5)

        self.assertEqual(doc.tiers['concepts'].spans[0].text, "Ireland")
        self.assertEqual(doc.tiers['concepts'].spans[0].label, "Ireland")
        self.assertEqual(doc.tiers['concepts'].spans[0].start, 20)
        self.assertEqual(doc.tiers['concepts'].spans[0].end, 27)

        self.assertEqual(doc.tiers['concepts'].spans[1].text, "Bangor, Maine")
        self.assertEqual(doc.tiers['concepts'].spans[1].label, "Bangor,_Maine")
        self.assertEqual(doc.tiers['concepts'].spans[1].start, 31)
        self.assertEqual(doc.tiers['concepts'].spans[1].end, 44)

        self.assertEqual(doc.tiers['concepts'].spans[2].text, "America")
        self.assertEqual(doc.tiers['concepts'].spans[2].label, "United_States")
        self.assertEqual(doc.tiers['concepts'].spans[2].start, 48)
        self.assertEqual(doc.tiers['concepts'].spans[2].end, 55)

        self.assertEqual(doc.tiers['concepts'].spans[3].text, "Maine")
        self.assertEqual(doc.tiers['concepts'].spans[3].label, "Maine")
        self.assertEqual(doc.tiers['concepts'].spans[3].start, 65)
        self.assertEqual(doc.tiers['concepts'].spans[3].end, 70)

        self.assertEqual(doc.tiers['concepts'].spans[4].text, "the United States of America")
        self.assertEqual(doc.tiers['concepts'].spans[4].label, "United_States")
        self.assertEqual(doc.tiers['concepts'].spans[4].start, 74)
        self.assertEqual(doc.tiers['concepts'].spans[4].end, 102)


    def test_caspian_sea(self):

        annotator = ConceptAnnotator()

        text = 'I went to the Caspian Sea.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)
        print
        print
        for span in doc.tiers['concepts'].spans:
            print span.label, ' :: ', span.text
        print
        print

        self.assertEqual(len(doc.tiers['concepts'].spans), 1)

        self.assertEqual(doc.tiers['concepts'].spans[0].text, "Caspian Sea")
        self.assertEqual(doc.tiers['concepts'].spans[0].label, "Caspian_Sea")
        self.assertEqual(doc.tiers['concepts'].spans[0].start, 14)
        self.assertEqual(doc.tiers['concepts'].spans[0].end, 25)

    def test_asia(self):

        # Interesting one... it prefers the span 'Asia.' with a period at the end.
        # That's not ideal. How do we prefer the shorter span?
        annotator = ConceptAnnotator()

        text = 'I went to Asia.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)
        print
        print
        # for span in doc.tiers['concepts'].spans:
        #     print span.label, ' :: ', span.text
        for span in doc.tiers['ngrams'].spans:
            print span.label, ' :: ', span.text
        print
        print

        self.assertEqual(len(doc.tiers['concepts'].spans), 1)

        self.assertEqual(doc.tiers['concepts'].spans[0].text, "Asia")
        self.assertEqual(doc.tiers['concepts'].spans[0].label, "Asia")
        self.assertEqual(doc.tiers['concepts'].spans[0].start, 10)
        self.assertEqual(doc.tiers['concepts'].spans[0].end, 14)


if __name__ == '__main__':
    unittest.main()