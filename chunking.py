from nltk import pos_tag, RegexpParser
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize



blacklist_POS = ['CC', 'DT', 'IN', 'TO', 'PRP', 'MD']


def process_content(s):
    try:
        new_s = []
        words = word_tokenize(s)

        lemmatizer = WordNetLemmatizer()
        words = map(lambda w: lemmatizer.lemmatize(w), words)

        tagged = pos_tag(words)
        chunkGram = r"""Chunk: {<RB.?>*<VB.?>*<NNP>+<NN>?}
                               {<DT>?<JJ>*<NN>}"""
        chunkParser = RegexpParser(chunkGram)
        chunked = chunkParser.parse(tagged)

        # print(chunked)
        # for subtree in chunked.subtrees(filter=lambda t: t.label() == 'Chunk'):
        #     print(subtree)
        #
        # chunked.draw()

        stem = PorterStemmer()

        for subtree in chunked:
            if type(subtree) is type(chunked):
                new_s.append(u'_'.join([stem.stem(x[0]) for x in subtree]))
                continue
            if subtree[1] in blacklist_POS:
                continue
            new_s.append(stem.stem(subtree[0]))

        new_s = u' '.join(new_s)
        return new_s


    except Exception as e:
        print(str(e))
        return s



s = 'British Prime Minister Theresa May will firmly reject a second Brexit referendum in an address to Parliament Monday, as pressure for a new vote grows both inside and outside a bitterly divided Westminster.'
process_content(s)