# -*- encoding: utf-8 -*-
# module get all articles talk about Đông sea event but not in weather forecast category
import config
import utils
from bson.objectid import ObjectId


forecast_weather_titles = [u'dự báo thời tiết']

forecast_weather_contents = [u'trung tâm dự báo khí tượng thủy văn',
                             u'trung tâm khí tượng thủy văn quốc gia',
                             u'trung tâm khí tượng thủy văn trung ương',
                             u'trung tâm dự báo khí tượng thủy văn quốc gia',
                             u'trung tâm dự báo khí tượng thủy văn trung ương',
                             u'trung tâm dbkttv tư', u'tt dbkttv tư',
                             u'bão', u'áp thấp', u'lũ', u'lốc',
                             u'sạt lở đất', u'rét', u'thiên tai']

keywords = [u'biển đông']


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
    title = title.lower()
    content = content.lower()

    for t in forecast_weather_titles:
        if title.find(t) != -1:
            return True

    for c in forecast_weather_contents:
        if content.find(c) != -1:
            return True

    return False


def get_articles(db, list_titles, list_contents, original_title, contentId2date, contenId2publisher):
    try:
        collection = db.get_collection(config.MONGO_COLLECTION_DONG_SEA)
    except:
        collection = db.create_collection(config.MONGO_COLLECTION_DONG_SEA)
        utils.create_mongo_index(collection, u'contentId')

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
            article = {u'contentId' : int(contentId),
                       u'title' : title,
                       u'date' : contentId2date[contentId],
                       u'publisher' : contenId2publisher[contentId]}
            collection.insert_one(article)

            now = utils.get_time_at_present()
            update_collection_time_info(db, config.MONGO_COLLECTION_DONG_SEA)


def update_collection_time_info(db, collection_name):
    try:
        collection = db.get_collection(config.MONGO_COLLECTION_UPDATE_TIME)
    except:
        collection = db.create_collection(config.MONGO_COLLECTION_UPDATE_TIME)
        utils.create_mongo_index(collection, u'name')

    now = utils.get_time_at_present()

    try:
        document = collection.find_one({u'name': {u'$eq': collection_name}}, max_time_ms=1000)
        _id = ObjectId(document[u'_id'])
        collection.update_one({u'_id': _id},
                              {u'$set': {u'update_time' : now}})
    except:
        collection.insert_one({u'name' : collection_name,
                               u'create_time' : now,
                               u'update_time' : now})