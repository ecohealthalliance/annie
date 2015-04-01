#!/usr/bin/env python
"""HTML tag annotator that creates a tiers containing the offests of all tags
of interest from the original text.

Note that this annotator must be run before all other annotators! It expects the
AnnoDoc.text to be in HTML. And it will change AnnoDoc.text to plain text with
no HTML tags present after it runs."""

from HTMLParser import HTMLParser

from annotator import *

import re

class HTMLOffsetParser(HTMLParser):
    """Uses Python's HTMLParser to parse HTML for the tag annotator"""

    text = ''
    index = 0

    space_chars = set([' ', '\n', '\t'])

    def __init__(self, tagset=None):
        HTMLParser.__init__(self)
        if tagset is not None:
            self.tagset = [tag.lower() for tag in tagset]
        else:
            self.tagset = []
        self.pending_tags = []
        self.tags = []

    def handle_starttag(self, tag, attrs):
        if tag in self.tagset:
            self.pending_tags.append(
                {'name': tag,
                 'start': self.index,
                 'attrs': attrs
                 })

    def handle_endtag(self, tag):
        if self.pending_tags and self.pending_tags[-1]['name'] == tag:
            pending_tag = self.pending_tags.pop()
            pending_tag['end'] = self.index
            self.tags.append(pending_tag)
        else:
            # Do we want to raise an error or log unexpected end tags?
            pass

    def handle_data(self, data):

        # If we are starting a paragraph and we don't have whitespace after
        # the end of the last paragraph, add a space.
        if (self.pending_tags and
            self.pending_tags[-1]['name'] == 'p' and
            self.text and
            self.text[-1] not in self.space_chars and
            data[0] not in self.space_chars):
            self.text += ' ' + data
            self.index += len(data) + 1
            self.pending_tags[-1]['start'] += 1
        else:
            self.text += data
            self.index += len(data)


class HTMLTagAnnotator:
    """Create a tier that contains the offsets of """

    def __init__(self, tagset=None, tier_name='html'):
        if tagset is not None:
            self.tagset = [tag.lower() for tag in tagset]
        else:
            self.tagset = []
        self.tags = []
        self.tier_name = tier_name

    def annotate(self, doc):
        """Annotate a document by taking the text and removing all HTML tags.
        Add spans for the tags in tagset. Need to run this first before other
        annotators because it transforms doc.text, so other offsets would become
        invalid.
        """

        # If there are any existing tiers, throw an error, because the offests
        # will become invalid after we strip the HTML from the AnnoDoc.text

        if len(doc.tiers) != 0:
            raise Exception('Found pre-existing tiers; their offsets would be' +
                'rendered invalid by stripping the AnnoDoc.text of tags')

        parser = HTMLOffsetParser(self.tagset)

        parser.feed(doc.text)

        spans = []
        for tag in parser.tags:
            span = AnnoSpan(tag['start'],
                            tag['end'],
                            doc,
                            label=tag['name'])
            span.attrs = dict(tag['attrs'])
            spans.append(span)

        doc.tiers[self.tier_name] = AnnoTier(spans)
        doc.text = parser.text

        doc.tiers[self.tier_name].sort_spans()

        return doc
