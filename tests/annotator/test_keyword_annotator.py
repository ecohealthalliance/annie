#!/usr/bin/env python
"""Tests for the KeywordAnnotator that annotates a sentence with tokens and their
offsets."""

import sys
import os
import unittest

sys.path = ['./'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.keyword_annotator import KeywordAnnotator


class KeywordAnnotatorTest(unittest.TestCase):

    def test_diseases(self):

        annotator = KeywordAnnotator()

        text = 'I thought I had a spot of periodontitis but it turned out to be Endometrial Endometrioid Adenocarcinoma with squamous differentiation.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['diseases'].spans), 2)

        self.assertEqual(doc.tiers['diseases'].spans[0].text, "periodontitis")
        self.assertEqual(doc.tiers['diseases'].spans[0].label, "periodontitis")
        self.assertEqual(doc.tiers['diseases'].spans[0].start, 26)
        self.assertEqual(doc.tiers['diseases'].spans[0].end, 39)

        self.assertEqual(doc.tiers['diseases'].spans[1].text, "Endometrial Endometrioid Adenocarcinoma with squamous differentiation")
        self.assertEqual(doc.tiers['diseases'].spans[1].label, "endometrial endometrioid adenocarcinoma with squamous differentiation")
        self.assertEqual(doc.tiers['diseases'].spans[1].start, 64)
        self.assertEqual(doc.tiers['diseases'].spans[1].end, 133)

    def test_hosts(self):

        annotator = KeywordAnnotator()

        text = 'I never should have let that silverfish sell me that FAWN.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['hosts'].spans), 2)

        self.assertEqual(doc.tiers['hosts'].spans[0].text, "silverfish")
        self.assertEqual(doc.tiers['hosts'].spans[0].label, "silverfish")
        self.assertEqual(doc.tiers['hosts'].spans[0].start, 29)
        self.assertEqual(doc.tiers['hosts'].spans[0].end, 39)

        self.assertEqual(doc.tiers['hosts'].spans[1].text, "FAWN")
        self.assertEqual(doc.tiers['hosts'].spans[1].label, "fawn")
        self.assertEqual(doc.tiers['hosts'].spans[1].start, 53)
        self.assertEqual(doc.tiers['hosts'].spans[1].end, 57)

    def test_modes(self):

        annotator = KeywordAnnotator()

        text = 'Indirect physical contact'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(doc.tiers['modes'].spans[0].text, "contact")
        self.assertEqual(doc.tiers['modes'].spans[0].label, "contact")
        self.assertEqual(doc.tiers['modes'].spans[0].start, 18)
        self.assertEqual(doc.tiers['modes'].spans[0].end, 25)

    def test_pathogens(self):

        annotator = KeywordAnnotator()

        text = 'Look out for xanthoMONAD and the hepatitis e virus.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['pathogens'].spans), 2)

        self.assertEqual(doc.tiers['pathogens'].spans[0].text, "xanthoMONAD")
        self.assertEqual(doc.tiers['pathogens'].spans[0].label, "xanthomonad")
        self.assertEqual(doc.tiers['pathogens'].spans[0].start, 13)
        self.assertEqual(doc.tiers['pathogens'].spans[0].end, 24)

        self.assertEqual(doc.tiers['pathogens'].spans[1].text, "hepatitis e virus")
        self.assertEqual(doc.tiers['pathogens'].spans[1].label, "hepatitis e virus")
        self.assertEqual(doc.tiers['pathogens'].spans[1].start, 33)
        self.assertEqual(doc.tiers['pathogens'].spans[1].end, 50)

    def test_symptoms(self):

        annotator = KeywordAnnotator()

        text = 'I feel weak, with some nausea.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['symptoms'].spans), 2)

        self.assertEqual(doc.tiers['symptoms'].spans[0].text, "weak")
        self.assertEqual(doc.tiers['symptoms'].spans[0].label, "weak")
        self.assertEqual(doc.tiers['symptoms'].spans[0].start, 7)
        self.assertEqual(doc.tiers['symptoms'].spans[0].end, 11)

        self.assertEqual(doc.tiers['symptoms'].spans[1].text, "nausea")
        self.assertEqual(doc.tiers['symptoms'].spans[1].label, "nausea")
        self.assertEqual(doc.tiers['symptoms'].spans[1].start, 23)
        self.assertEqual(doc.tiers['symptoms'].spans[1].end, 29)

    def test_case_sensitivity(self):

        annotator = KeywordAnnotator()

        text = 'The word as should not be recognized as a disease.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['diseases'].spans), 0)

        text = 'The word AS should be recognized as a disease.'
        doc = AnnoDoc(text)
        doc.add_tier(annotator)

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['diseases'].spans), 1)
        self.assertEqual(doc.tiers['diseases'].spans[0].text, "AS")
        self.assertEqual(doc.tiers['diseases'].spans[0].label, "AS")
        self.assertEqual(doc.tiers['diseases'].spans[0].start, 9)
        self.assertEqual(doc.tiers['diseases'].spans[0].end, 11)

    def test_array(self):
        annotator = KeywordAnnotator(keywords=["Trisolaris"])

        doc = AnnoDoc("Trisolaris is an unpredictable place.")
        doc.add_tier(annotator)

        self.assertEqual(len(doc.tiers['keywords'].spans), 1)

        self.assertEqual(doc.tiers['keywords'].spans[0].text, "Trisolaris")

if __name__ == '__main__':
    unittest.main()