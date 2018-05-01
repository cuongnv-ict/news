# -*- encoding: utf-8 -*-

from io import open
import topics
import os
import unicodedata
import utils



def load_document_content(dataset, documents):
    stack = os.listdir(dataset)
    while (len(stack) > 0):
        file_name = stack.pop()
        file_path = dataset + '/' + file_name
        if (os.path.isdir(file_path)):  # neu la thu muc thi day vao strong stack
            utils.push_data_to_stack(stack, file_path, file_name)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    raw_content = unicodedata.normalize('NFKC', f.read().strip()).split(u'\n')
                    new_content = []
                    for i, sen in enumerate(raw_content):
                        if i == 0:
                            # highlight title
                            sen = u'<h2>' + sen + u'</h2>'
                        elif i == 1:
                            sen = u'<h5>' + sen + u'</h5>'
                        else:
                            sen = sen + u'<br>'
                        new_content.append(sen)
                    documents.update({raw_content[0].lower() : u'\n'.join(new_content)})
                except:
                    continue


def get_document_by_title(title, documents):
    try:
        content = documents[title]
        return content
    except:
        return u''