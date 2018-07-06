# -*- encoding: utf-8 -*-
# module get all articles talk about Đông sea event but not in weather forecast category
import config


skip_titles = {u'dự báo thời tiết' : True}

skip_contents = {u'Trung tâm Dự báo Khí tượng Thủy văn Quốc gia' : True,
                 u'Trung tâm Dự báo Khí tượng Thủy văn Trung ương' : True,
                 u'Trung tâm DBKTTV TƯ' : True,
                 u'TT DBKTTV TƯ' : True}

keywords = [u'biển đông', u'trường sa', u'hoàng sa',
           u'quần đảo trường sa', u'quần đảo hoàng sa']


def parser_title(raw_title):
    raw = raw_title.split(u' == ')
    contentId = raw[0]
    title = raw[1]
    return contentId, title


def parser_content(content):
    sentences = content.split(u'\n')
    if u'[tags] : ' in sentences[len(sentences) - 1]:
        tags = sentences[len(sentences) - 1].split(u'[tags] : ')
        tags = tags[1].split(u' , ')
        return {tag.lower() : True for tag in tags}
    else: return {}


def is_Dong_sea_article(tags):
    for key in keywords:
        try:
            _ = tags[key.lower()]
            return True
        except: pass
    return False


def get_articeles(db, list_titles, list_contents):
    try:
        collection = db.get_collection(config.MONGO_COLLECTION_DONG_SEA)
    except:
        collection = db.create_collection(config.MONGO_COLLECTION_DONG_SEA)

    for i in xrange(len(list_titles)):
        raw_title = list_titles[i]
        contentId, title = parser_title(raw_title)
        tags = parser_content(list_contents[i])
        if is_Dong_sea_article(tags):
            print(u'Dong sea article: %s' % (title))
            article = {u'contentId' : int(contentId), u'title' : title}
            collection.insert_one(article)


