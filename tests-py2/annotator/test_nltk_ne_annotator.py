#!/usr/bin/env python
"""Tests for the NLTKNEAnnotator that annotates a sentence with named entities."""

import sys
import unittest

sys.path = ['./'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.nltk_ne_annotator import NLTKNEAnnotator


class NLTKNEAnnotatorTest(unittest.TestCase):

    def setUp(self):
        self.annotator = NLTKNEAnnotator()

    def test_simple_sentence(self):

        self.doc = AnnoDoc("I'm married to Joe.")
        self.doc.add_tier(self.annotator)

        self.assertEqual(len(self.doc.tiers['nes'].spans), 1)

        self.assertEqual(self.doc.tiers['nes'].spans[0].label, 'PERSON')
        self.assertEqual(self.doc.tiers['nes'].spans[0].start, 15)
        self.assertEqual(self.doc.tiers['nes'].spans[0].stop, 18)

    def test_complex_text(self):

        self.doc = AnnoDoc(
        "I'm married to Joe from New York City. "
        "That is in the United States who works for the Raytheon Corporation."
        )
        self.doc.add_tier(self.annotator)

        self.assertEqual(len(self.doc.tiers['nes'].spans), 4)

        self.assertEqual(self.doc.tiers['nes'].spans[0].label, 'PERSON')
        self.assertEqual(self.doc.tiers['nes'].spans[0].text, 'Joe')
        self.assertEqual(self.doc.tiers['nes'].spans[0].start, 15)
        self.assertEqual(self.doc.tiers['nes'].spans[0].stop, 18)

        self.assertEqual(self.doc.tiers['nes'].spans[1].label, 'GPE')
        self.assertEqual(self.doc.tiers['nes'].spans[1].text, 'New York City')
        self.assertEqual(self.doc.tiers['nes'].spans[1].start, 24)
        self.assertEqual(self.doc.tiers['nes'].spans[1].stop, 37)

        self.assertEqual(self.doc.tiers['nes'].spans[2].label, 'GPE')
        self.assertEqual(self.doc.tiers['nes'].spans[2].text, 'United States')
        self.assertEqual(self.doc.tiers['nes'].spans[2].start, 54)
        self.assertEqual(self.doc.tiers['nes'].spans[2].stop, 67)

        self.assertEqual(self.doc.tiers['nes'].spans[3].label, 'ORGANIZATION')
        self.assertEqual(self.doc.tiers['nes'].spans[3].text, 'Raytheon Corporation')
        self.assertEqual(self.doc.tiers['nes'].spans[3].start, 86)
        self.assertEqual(self.doc.tiers['nes'].spans[3].stop, 106)


if __name__ == '__main__':
    unittest.main()