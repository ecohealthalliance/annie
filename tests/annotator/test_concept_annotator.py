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


    def test_chicago(self):

        annotator = ConceptAnnotator()

        text = 'I went to Maine.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['concepts'].spans), 1)
        self.assertEqual(doc.tiers['concepts'].spans[0].text, "Maine")
        self.assertEqual(doc.tiers['concepts'].spans[0].label, "Maine")
        self.assertEqual(doc.tiers['concepts'].spans[0].start, 10)
        self.assertEqual(doc.tiers['concepts'].spans[0].end, 15)


if __name__ == '__main__':
    unittest.main()