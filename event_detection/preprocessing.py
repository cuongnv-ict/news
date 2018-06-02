# -*- encoding: utf-8 -*-

import os, utils
from io import open
import unicodedata
from pyvi.pyvi import ViPosTagger
from nlp_tools import tokenizer, spliter



importance_pos = {'N':True, 'Np':True, 'Ny':True, 'V':True}

def is_exist(postag):
    try:
        _ = importance_pos[postag]
        return True
    except:
        return False


def remove_stop_postag(dataset, output_dir):
    utils.mkdir(output_dir)
    stack = os.listdir(dataset)
    # print 'loading data in ' + dataset
    total_doc = 0
    while (len(stack) > 0):
        file_name = stack.pop()
        file_path = os.path.join(dataset, file_name)
        if (os.path.isdir(file_path)):  # neu la thu muc thi day vao strong stack
            utils.push_data_to_stack(stack, file_path, file_name)
        else:
            with open(file_path, 'r', encoding='utf-8') as fr:
                data = unicodedata.normalize('NFKC', fr.read().strip())
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
                with open(os.path.join(output_dir, os.path.basename(file_name)),
                          'w', encoding='utf-8') as fw:
                    if len(clean_content) > 0:
                        fw.write(u'\n'.join(clean_content))
                    else: fw.write(data)
                total_doc += 1
                # print '\rprocessed doc %2dth' % (total_doc),
                # sys.stdout.flush()
    # print('')





if __name__ == '__main__':
    remove_stop_postag('dataset')
