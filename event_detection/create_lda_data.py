# -*- encoding: utf-8 -*-

from io import open
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
import utils
import os



def build_vocab(dataset, output_vocab, root_dir):
    vectorizer = TfidfVectorizer(ngram_range=(1, 1), max_df=0.6, min_df=2,
                                 stop_words=utils.load_data_from_list(os.path.join(root_dir, 'stopwords.txt')))
    stack = os.listdir(dataset)
    contents = []
    while (len(stack) > 0):
        file_name = stack.pop()
        file_path = os.path.join(dataset, file_name)
        if (os.path.isdir(file_path)):  # neu la thu muc thi day vao strong stack
            utils.push_data_to_stack(stack, file_path, file_name)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                contents.append(f.read().lower())
    # change vectorizer to ensure length of document greater than 0
    if len(contents) < 100:
        vectorizer.min_df = 1
    if len(contents) < 50:
        vectorizer.max_df = 1
    vectorizer.fit(contents)
    with open(output_vocab, 'w', encoding='utf-8') as f:
        vocab = {w:i for i, w in enumerate(vectorizer.vocabulary_.keys())}
        f.write(u'\n'.join(vocab.keys()))
    return contents


def get_title(dataset, output_dir, output_file):
    stack = os.listdir(dataset)
    utils.mkdir(output_dir)
    titles = []
    while (len(stack) > 0):
        file_name = stack.pop()
        file_path = os.path.join(dataset, file_name)
        if (os.path.isdir(file_path)):  # neu la thu muc thi day vao strong stack
            utils.push_data_to_stack(stack, file_path, file_name)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = unicodedata.normalize('NFKC', f.read().strip())
                title = data.lower().split(u'\n')[0]
                titles.append(title)
    exist = False
    if os.path.isfile(output_file):
        exist = True
    with open(output_file, 'a', encoding='utf-8') as f:
        if exist:
            f.write(u'\n')
        f.write(u'\n'.join(titles))


def load_vocab(vocab_file):
    vocab = {}
    with open(vocab_file, 'r', encoding='utf-8') as f:
        for i, w in enumerate(f):
            vocab.update({w.strip(u'\n'):i})
    return vocab


def get_lda_data(contents, vocab, output_dir, output_file):
    result = []
    utils.mkdir(output_dir)
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, content in enumerate(contents):
            lda_data = {}
            for w in content.split():
                try:
                    index = vocab[w]
                    try:
                        lda_data[index] += 1
                    except:
                        lda_data.update({index : 1})
                except:
                    continue
            x = [unicode(len(lda_data))]
            x.extend([unicode(i) + u':' + unicode(j) for i, j in lda_data.items()])
            result.append(u' '.join(x))
        f.write(u'\n'.join(result))





if __name__ == '__main__':
    contents = build_vocab('clean_dataset')
    vocab = load_vocab('vocab.dat')
    get_lda_data(contents, vocab)
    get_title('dataset')