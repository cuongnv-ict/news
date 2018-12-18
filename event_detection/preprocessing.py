# -*- encoding: utf-8 -*-

import os, utils
from io import open
from nltk import tokenize






def sentence_tokenize(dataset, output_dir, names):
    utils.mkdir(output_dir)
    total_doc = 0
    for id, data in enumerate(dataset):
        # original_content = tokenizer.predict(data)
        sens = []
        for s in data.split(u'\n'):
            ss = tokenize.sent_tokenize(s)
            sens += ss
        with open(os.path.join(output_dir, names[id]),
                  'w', encoding='utf-8') as fw:
            if len(sens) > 0:
                fw.write(u'\n'.join(sens))
            else: fw.write(data)
        total_doc += 1






if __name__ == '__main__':
    sentence_tokenize('dataset')
