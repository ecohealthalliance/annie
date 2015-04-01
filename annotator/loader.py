#!/usr/bin/env python
"""An annie loader creates an AnnoDoc from a source such as a file or database.
The loader should perform as much annotation as is necessary to preserve parts
of document structure that would otherwise be lost. For example, if there is a
document header, it might be parsed and metadata stored in the AnnoDoc.properties.
If HTML tags are removed, certain tags might be transferred to an AnnoTier.
"""

import yaml
# import BeautifulSoup
# BeautifulSoup doesn't seem to be loaded.
# And anyway, isn't it `from bs4 import BeautifulSoup`?

from .annotator import AnnoDoc
from .html_tag_annotator import HTMLTagAnnotator


class Loader():
    def load():
        """Create an AnnoDoc from a data source"""
        raise NotImplementedError("load method must be implemented in child")

class HTMLFileLoader(Loader):
    """Loader for an HTML file"""

    def load(self, filename, tagset=None):
        """Create an AnnoDoc from an HTML file, with a tier for tags in tagset"""

        if tagset is None:
            tagset = []

        with open(filename, 'r') as f:
            text = f.read()

        doc = AnnoDoc(text)
        html_tag_annotator = HTMLTagAnnotator(tagset=tagset)
        doc.add_tier(html_tag_annotator)

        return doc
