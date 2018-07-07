# -*- encoding: utf-8 -*-
# module get all articles talk about Đông sea event but not in weather forecast category
import config


skip_titles = [u'dự báo thời tiết']

skip_contents = [u'Trung tâm Dự báo Khí tượng Thủy văn Quốc gia',
                 u'Trung tâm Dự báo Khí tượng Thủy văn Trung ương',
                 u'Trung tâm DBKTTV TƯ', u'TT DBKTTV TƯ']

keywords = [u'biển đông', u'trường sa', u'hoàng sa',
           u'quần đảo trường sa', u'quần đảo hoàng sa']


def parser_title(raw_title):
    raw = raw_title.split(u' == ')
    contentId = raw[0]
    title = raw[1].replace(u'_', u' ')
    return contentId, title


def parser_content(content):
    content = content.replace(u'_', u' ')
    sentences = content.split(u'\n')
    if u'[ tags ] : ' in sentences[len(sentences) - 1]:
        tags = sentences[len(sentences) - 1].split(u'[ tags ] : ')
        tags = tags[1].split(u' , ')
        return content, {tag.lower() : True for tag in tags}
    else:
        return content, {}


def is_Dong_sea_article(tags):
    for key in keywords:
        try:
            _ = tags[key.lower()]
            return True
        except: pass
    return False


def is_weather_forecast(title, content):
    for t in skip_titles:
        if title.find(t) != -1:
            return True

    for c in skip_contents:
        if content.find(c) != -1:
            return True

    return False


def get_articles(db, list_titles, list_contents, original_title):
    try:
        collection = db.get_collection(config.MONGO_COLLECTION_DONG_SEA)
    except:
        collection = db.create_collection(config.MONGO_COLLECTION_DONG_SEA)

    for i in xrange(len(list_titles)):
        raw_title = list_titles[i]
        contentId, new_title = parser_title(raw_title)
        try:
            title = original_title[contentId]
            title = title.split(u' == ')[1]
        except:
            title = new_title
        content, tags = parser_content(list_contents[i])
        if is_Dong_sea_article(tags) and not is_weather_forecast(title, content):
            print(u'Dong sea article: %s' % (title))
            article = {u'contentId' : int(contentId), u'title' : title}
            collection.insert_one(article)