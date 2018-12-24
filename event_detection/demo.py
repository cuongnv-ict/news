# -*- encoding: utf-8 -*-

import utils
import config


def normalize_html_format(short_summary, normalized_content):
    raw_content = normalized_content.strip().split(u'\n')
    new_content = []
    html_content = u'<h2>Summary:</h2><br>' + short_summary + u'<br><br>'
    for i, sen in enumerate(raw_content):
        if i == 0:
            # highlight title
            sen = u'<h2>' + sen + u'</h2>'
        elif i == 1:
            sen = u'<h5>' + sen + u'</h5>'
        else:
            sen = sen + u'<br>'
        new_content.append(sen)
    html_content += u'<h2>Document content:<h2><br>'
    html_content += u'\n'.join(new_content)
    return html_content


def get_summary_and_content(contentId):
    connection, db = utils.connect2mongo(config.MONGO_HOST, config.MONGO_PORT,
                                         config.MONGO_USER, config.MONGO_PASS,
                                         config.MONGO_DB)
    try:
        collection = db.get_collection(config.MONGO_COLLECTION_NORMALIZED_ARTICLES)
        document_content = collection.find_one({u'contentId': {u'$eq': int(contentId)}}, max_time_ms=1000)
        normalized_content = document_content[u'normalized_article']
    except:
        normalized_content = u'Can\'t get document content'
    try:
        collection = db.get_collection(config.MONGO_COLLECTION_SUMMRIES)
        document_summary = collection.find_one({u'contentId': {u'$eq': int(contentId)}}, max_time_ms=1000)
        # short_summary = document_summary[u'summaries'][u'short']
        medium_summary = document_summary[u'summaries'][u'medium']
    except:
        # short_summary = u'Can\'t get document summary'
        medium_summary = u'Can\'t get document summary'
    # html_content = normalize_html_format(short_summary, normalized_content)
    html_content = normalize_html_format(medium_summary, normalized_content)
    connection.close()
    return html_content