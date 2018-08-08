# -*- encoding: utf-8 -*-
from accent2bare import accent2bare
from io import open
import utils
from os import path



class detect_acronym:
    def __init__(self, root_dir='.'):
        self.vocab_path = path.join(root_dir, 'resources/vocab_final.dat')
        self.vocab_bin_path = path.join(root_dir, 'model/vocab.pkl')
        self.whitelist_path = path.join(root_dir, 'resources/acronym_whitelist.dat')
        self.whitelist_bin_path = path.join(root_dir, 'model/whitelist.pkl')
        self.vocab = detect_acronym.load_vocab(self)
        self.whitelist = detect_acronym.load_whitelist(self)


    @staticmethod
    def load_vocab(self):
        vocab = utils.load(self.vocab_bin_path)
        if vocab is None:
            vocab = {}
        else:
            return vocab
        utils.mkdir('model')
        print('load vocab...')
        with open(self.vocab_path, 'r', encoding='utf-8') as fp:
            for word in fp:
                word = word.strip().lower()
                list_word = word.split()
                word = word.replace(u' ', u'_') # tokenizer
                # if len(list_word) < 2 or len(list_word) > 4:
                if len(list_word) != 2: # keep words just have 2 syllables
                    continue
                acronym = u''.join([w[0] for w in list_word])
                acronym = accent2bare(acronym)
                try:
                    vocab[acronym].append(word)
                except:
                    vocab.update({acronym: [word]})
        utils.save(vocab, self.vocab_bin_path)
        return vocab


    @staticmethod
    def load_whitelist(self):
        whitelist = utils.load(self.whitelist_bin_path)
        if whitelist is not None:
            return whitelist
        with open(self.whitelist_path, 'r', encoding='utf-8') as fp:
            whitelist = {w.lower().strip():True for w in fp}
        utils.save(whitelist, self.whitelist_bin_path)
        return whitelist


    def is_whitelist(self, word):
        try:
            _ = self.whitelist[word.lower()]
            return True
        except:
            return False


    def is_acronym(self, word):
        if self.is_whitelist(word):
            return False
        if word.isupper():
            return True
        else:
            return False


    def get_candidates(self, word):
        try:
            candidates = self.vocab[word.lower()]
        except:
            candidates = []
        return candidates




if __name__ == '__main__':
    da = detect_acronym()