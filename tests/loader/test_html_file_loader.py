#!/usr/bin/env python
"""Tests for the HTMLFileLoader"""

import sys
import os
import unittest

sys.path = ['./'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.loader import HTMLFileLoader


class HTMLFileLoaderTest(unittest.TestCase):

    def setUp(self):

        self.loader = HTMLFileLoader()

    def test_html_doc(self):

        filename = os.path.join(os.path.dirname(__file__), 'resources/sample.html')

        doc = self.loader.load(filename, tagset=['b', 'i'])

        text = '\n\n   \n      My first HTML document\n   \n   \n      ' +\
               'Hello world! Italic is interesting but not underline.\n   \n'

        self.assertEqual(doc.text, text)

        self.assertEqual(len(doc.tiers['html'].spans), 2)

        self.assertEqual(doc.tiers['html'].spans[0].label, 'b')
        self.assertEqual(doc.tiers['html'].spans[0].text, 'world')
        self.assertEqual(doc.tiers['html'].spans[0].start, 55)
        self.assertEqual(doc.tiers['html'].spans[0].stop, 60)

        self.assertEqual(doc.tiers['html'].spans[1].label, 'i')
        self.assertEqual(doc.tiers['html'].spans[1].text, 'Italic')
        self.assertEqual(doc.tiers['html'].spans[1].start, 62)
        self.assertEqual(doc.tiers['html'].spans[1].stop, 68)


if __name__ == '__main__':
    unittest.main()