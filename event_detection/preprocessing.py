# -*- encoding: utf-8 -*-

import os, utils
from io import open
import unicodedata
from nlp_tools import tokenizer, spliter
try:
    from pyvi.pyvi import ViPosTagger
except:
    from pyvi import ViPosTagger



importance_pos = {'N':True, 'Np':True, 'Ny':True, 'V':True}

def is_exist(postag):
    try:
        _ = importance_pos[postag]
        return True
    except:
        return False


def remove_stop_postag(dataset, output_dir, names):
    utils.mkdir(output_dir)
    total_doc = 0
    for id, data in enumerate(dataset):
        # original_content = tokenizer.predict(data)
        content = map(lambda x: ViPosTagger.postagging(x),
                      spliter.split(data))
        clean_content = []
        for info in content:
            sen = []
            for i in xrange(len(info[0])):
                if is_exist(info[1][i]):
                    sen.append(info[0][i])
            clean_content.append(u' '.join(sen))
        with open(os.path.join(output_dir, names[id]),
                  'w', encoding='utf-8') as fw:
            if len(clean_content) > 0:
                fw.write(u'\n'.join(clean_content))
            else: fw.write(data)
        total_doc += 1






if __name__ == '__main__':
    remove_stop_postag('dataset')
