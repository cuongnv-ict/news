# -*- encoding: utf-8 -*-

import regex
import os
import my_map
import utils
from io import open
import unicodedata
from nlp_tools import tokenizer

r = regex.regex()

def load_dataset(dataset):
    list_samples = {k:[] for k in my_map.name2label.keys()}
    stack = os.listdir(dataset)
    print 'loading data in ' + dataset
    while (len(stack) > 0):
        file_name = stack.pop()
        file_path = os.path.join(dataset, file_name)
        if (os.path.isdir(file_path)):
            utils.push_data_to_stack(stack, file_path, file_name)
        else:
            print(file_path)
            with open(file_path, 'r', encoding='utf-16') as fp:
                content = r.run(unicodedata.normalize('NFKC', fp.read()))
                content = tokenizer.predict(content)
                dir_name = utils.get_dir_name(file_path)
                list_samples[dir_name].append(content)
    return list_samples


def load_dataset_ex(list_samples):
    result = []
    for sample in list_samples:
        sample = r.run(sample)
        sample = tokenizer.predict(sample)
        result.append(sample)
    return result




if __name__ == '__main__':
    load_dataset('dataset/train')