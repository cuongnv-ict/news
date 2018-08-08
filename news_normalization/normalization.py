# -*- encoding: utf-8 -*-
from os import path
from acronym_normalization import acronym_normalization
from remove_redundance import normalize_ending_mark



class normalization:
    def __init__(self, root_dir=u'.'):
        self.acronym = acronym_normalization(root_dir)


    def run(self, str):
        result = normalize_ending_mark(str)
        result = self.acronym.normalize(result)
        return result