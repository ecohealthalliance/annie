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
        self.assertEqual(len(doc.tiers['concepts'].spans), 4)
        self.assertEqual(doc.tiers['concepts'].spans[0].text, "Ireland")
        self.assertEqual(doc.tiers['concepts'].spans[0].label, "Ireland")
        self.assertEqual(doc.tiers['concepts'].spans[0].start, 18)
        self.assertEqual(doc.tiers['concepts'].spans[0].end, 25)


if __name__ == '__main__':
    unittest.main()