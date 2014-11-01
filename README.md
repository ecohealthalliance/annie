# Annie: Simple annotation for text

Annie is a Apache2 Licensed text annotation library, written in Python, with a focus on linguistic annotations and simplicity.

Annotations, such as part-of-speech tags, lemmata, named entity references etc, are stored with their byte offsets into the original text. Annotators are provided to perform common NLP functions such as identifying tokens, sentences, n-grams, tagging part of speech, etc. Most linguistic functions in the annotators included with Annie are provided by [NLTK](http://www.nltk.org/), but the core of Annie itself is agnostic as to the source of annotations and NLTK is required only if you wish to use the annotators that rely on it.

Annie is designed to provide a simple solution to a common need: add layers of linguistic or other kinds of annotation to a document. The approach we use is to store the data as standoff annotation that references the relevant span in the text by its byte offsets. Annotations of a given kind are stored in a tier, and we can look across tiers to find overlapping spans in different kinds of annotations.

## Annotation structures

The container for an entire annotated document is the `AnnoDoc`. It can be created by simple instantion, with or without its text as an argument to the constructor:

    from annotator import annotator
    doc = annotator.AnnoDoc()
    doc.text = 'It was the epoch of belief, it was the epoch of incredulity.'
    # or
    doc = annotator.AnnoDoc('It was the epoch of belief, it was the epoch of incredulity')

The `AnnoDoc` stores the text of the document in the `text` property. Annotations are organized in tiers according to their kind and source. Tiers are stored by name in a dict in the `tiers` property of the doc. Tiers are created by `Annotator` instances, which create annotations on the basis of the `text` and / or the information already present in other tiers. For example, a token annotator works from the text, while an n-gram annotator works on the token tier already created by the token annotator. Most of the included NLP annotators use NLTK methods by default, but can be changed to use other methods.

    from annotator.token_annotator import TokenAnnotator
    from annotator.ngram_annotator import NgramAnnotator
    token_annotator = TokenAnnotator()
    token_annotator.annotate(doc)
    ngram_annotator = NgramAnnotator()
    ngram_annotator.annotate(doc)

The contents of an `AnnoTier` is stored in the `spans` property, which is a list of `AnnoSpans` in the order encountered in the document. Every `AnnoSpan` has at least six properties:
    * `start`: the byte offset where the span begins
    * `stop`: the byte offset where the span ends
    * `text`: the exact text of the document from `start` to `stop`.
    * `label`: the value of the annotation, often just the `text` of the span in the document, as for a token annotation. For a part-of-speech annotation, for example, the label would be "NN", "VB" or another part-of-speech label.
    * `doc`: a reference to the `AnnoDoc` to which the span belongs

    print doc.tiers['tokens'].spans[0].start
    print doc.tiers['tokens'].spans[0].stop
    print doc.tiers['tokens'].spans[0].text
    print doc.tiers['3grams'].spans[3].start
    print doc.tiers['3grams'].spans[3].stop
    print doc.tiers['3grams'].spans[3].text

## Implementing a new annotator

To create your own annotator, inherit from `Annotator` and implement `annotate` such that you add a new annotation tier to `doc`. Here's an example of a trivial annotator that creates an annotation tier whose span labels are the length of the corresponding tokens in the text.

    class TokenLengthAnnotator(Annotator):

        def annotate(self, doc, tier_name='token_length'):

            length_spans = []

            for token_span in doc.tiers['tokens'].spans:
                length_spans.append(
                    AnnoSpan(token_span.start,
                                token_span.stop,
                                token_span.doc,
                                label=len(token_span.text)
                            )
                )

            doc.tiers['token_length'] = AnnoTier(length_spans)

    tl_annotator = TokenLengthAnnotator()
    tl_annotator.annotate(doc)
