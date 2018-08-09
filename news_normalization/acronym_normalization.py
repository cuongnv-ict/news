# -*- encoding: utf-8 -*-
from detect_acronym import detect_acronym
from language_model import language_model
from io import open
from numpy import argmax
import utils
from remove_redundance import is_image_caption
from os import path



class acronym_normalization:
    def __init__(self, root_dir='.'):
        utils.mkdir(path.join(root_dir, 'model'))
        self.hard_rules_path = path.join(root_dir, 'resources/hard_rules.dat')
        self.hard_rules_bin_path = path.join(root_dir, 'model/hard_rules.pkl')
        self.language_model_path = path.join(root_dir, 'markov_dataset')
        self.detect_acronym = detect_acronym(root_dir=root_dir)
        self.language_model = language_model(root_dir=root_dir)
        self.hard_rules = acronym_normalization.load_hard_rules(self)


    @staticmethod
    def load_hard_rules(self):
        hard_rules = utils.load(self.hard_rules_bin_path)
        if hard_rules is not None:
            return hard_rules
        hard_rules = {}
        with open(self.hard_rules_path, 'r', encoding='utf-8') as fp:
            for line in fp:
                info = line.strip().lower().split(u'\t')
                hard_rules.update({info[0] : info[1]})
        utils.save(hard_rules, self.hard_rules_bin_path)
        return hard_rules


    def get_hard_rules(self, word):
        try:
            full = self.hard_rules[word.lower()]
            return full
        except:
            return None


    def normalize(self, str):
        # tokenized_str = tokenizer.predict(str)
        # sentences = tokenized_str.split(u'\n')
        sentences = str.split(u'\n')
        sentences = filter(lambda sen: not is_image_caption(sen), sentences)
        sentences = map(lambda sen: self.remove_dot(sen), sentences)
        sentences = map(lambda sen: self.normalize_sentence(sen), sentences)
        return u'\n'.join(sentences)


    def remove_dot(self, sentence):
        result = []
        words = sentence.split()
        for w in words:
            if w.isupper():
                result.append(w.replace(u'.', u''))
            else: result.append(w)
        return u' '.join(result)


    def normalize_sentence(self, sentence):
        regex_str, number, url, email, datetime, \
        mark, mark2 = self.language_model.pre_processing(sentence, predict_mode=True)

        words = regex_str.split()
        result_words = []
        for i, word in enumerate(words):
            if not self.detect_acronym.is_acronym(word):
                result_words.append(word)
                continue

            if i > 0:
                previous_word = words[i - 1]
            else:
                previous_word = u''
            if i < len(words) - 1:
                next_word = words[i + 1]
            else:
                next_word = u''

            # skip acronym between parentheses, double quotes, etc...
            if previous_word == u'5' and next_word == u'5':
                result_words.append(word)
                continue

            hard_rule = self.get_hard_rules(word)
            if hard_rule != None:
                result_words.append(hard_rule)
                continue

            # skip acronym whose length is less than 2 or more than 4
            # if len(word) < 2 or len(word) > 4:
            if len(word) != 2:
                result_words.append(word)
                continue

            candidates = self.detect_acronym.get_candidates(word)
            if len(candidates) == 0:
                result_words.append(word)
                continue

            best_candidate = self.get_best_candidate(candidates, previous_word, next_word)
            if best_candidate is not None:
                result_words.append(best_candidate)
            else:
                result_words.append(word)

        # result_words = map(lambda x: x.replace(u'_', u' '), result_words)

        final_str = self.language_model.restore_info(u' '.join(result_words),
                                                     number, url, email, datetime,
                                                     mark, mark2)
        return final_str


    def get_best_candidate(self, candidates, previous_word, next_word):
        markov_scores = map(lambda x: self.language_model.get_markov_chain_score(
            u' '.join([previous_word, x, next_word]).lower()), candidates)
        best_index = argmax(markov_scores)
        best_score = markov_scores[best_index]
        if best_score <= self.language_model.MIN_PROB * 3:
            return None
        best_candidate = candidates[best_index]
        return best_candidate






if __name__ == '__main__':
    AN = acronym_normalization()
    result = AN.normalize(u'TP Hà Nội')
    print(result)