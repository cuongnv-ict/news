# -*- coding: utf-8 -*-
__author__ = 'nobita'

import os
from io import open
import shutil



# return list of string
def load_data_from_dict(data_file):
    d = {}
    with open(data_file, 'r', encoding='utf-8') as f:
        for data in f:
            data = data.strip(u'\n').strip().lower()
            d.update({data:True})
    return d


def load_data_from_list(data_file):
    l = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for data in f:
            l.append(data.strip(u'\n').strip().lower())
    return l



def mkdir(dir):
    if (os.path.exists(dir) == False):
        try:
            os.mkdir(dir)
        except Exception as e:
            print(e.message)


def delete_dir(dir):
    ## Try to remove tree; if failed show an error using try...except on screen
    try:
        shutil.rmtree(dir)
    except OSError, e:
        print ("Warning: %s - %s." % (e.filename, e.strerror))


def push_data_to_stack(stack, file_path, file_name):
    sub_folder = os.listdir(file_path)
    for element in sub_folder:
        element = file_name + '/' + element
        stack.append(element)


def update_dict_from_value(d1, d2):
    for k, v in d1.items():
        for kk, vv in v.items():
            d2[k].update({vv:kk})
    return


def string2bytearray(s):
    l = [c for c in s]
    return l


def add_to_list(l1, l2):
    l = []
    for x in l1:
        for xx in l2:
            l.append(x+xx)
    return l


def get_max(l):
    maximum = max(l)
    return (l.index(maximum), maximum)


def vector_normarize(v):
    total = sum(v)
    return map(lambda x: float(x) / float(total), v)


if __name__ == '__main__':
    ind, m = get_max([1,4,2,3,5,0])
    pass