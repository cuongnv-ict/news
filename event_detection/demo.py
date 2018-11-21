# -*- encoding: utf-8 -*-

from io import open
import os
import unicodedata
import utils
import config


def normalize_html_format(normalized_content):
    raw_content = normalized_content.strip().split(u'\n')
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
    return u'\n'.join(new_content)


def get_document_content(contentId):
    connection, db = utils.connect2mongo(config.MONGO_HOST, config.MONGO_PORT,
                                         config.MONGO_USER, config.MONGO_PASS,
                                         config.MONGO_DB)
    try:
        collection = db.get_collection(config.MONGO_COLLECTION_NORMALIZED_ARTICLES)
        document = collection.find_one({u'contentId': {u'$eq': int(contentId)}}, max_time_ms=1000)
        normalized_content = document[u'normalized_article']
        html_content = normalize_html_format(normalized_content)
    except:
        html_content = u'<h4>Can\'t get content of article</h4>'
    connection.close()
    return html_content