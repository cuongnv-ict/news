from nltk import pos_tag, RegexpParser
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize



blacklist_POS = ['CC', 'DT', 'IN', 'TO', 'PRP']


def process_content(s):
    try:
        new_s = []
        words = word_tokenize(s)

        lemmatizer = WordNetLemmatizer()
        words = map(lambda w: lemmatizer.lemmatize(w), words)

        # stem = PorterStemmer()
        # words = map(lambda w: stem.stem(w), words)

        tagged = pos_tag(words)
        chunkGram = r"""Chunk: {<RB.?>*<VB.?>*<NNP>+<NN>?<DT>?<JJ>*<NN>}"""
        chunkParser = RegexpParser(chunkGram)
        chunked = chunkParser.parse(tagged)

        print(chunked)
        for subtree in chunked.subtrees(filter=lambda t: t.label() == 'Chunk'):
            print(subtree)

        chunked.draw()

        for subtree in chunked:
            pass

    except Exception as e:
        print(str(e))
        return s



s = 'He liked to discuss about the issues.'
process_content(s)