# -*- encoding: utf-8 -*

import utils

# MONGO_HOST = '103.35.64.122'
# MONGO_PORT = 2200
# MONGO_USER = 'dbMongo'
# MONGO_PASS = 'SOh3TbYhx8ypJPxmt1oOfL'

MONGO_HOST = '210.245.115.39'
MONGO_PORT = 27017
MONGO_USER = ''
MONGO_PASS = ''

MONGO_DB = 'dora_english'

MONGO_COLLECTION_ARTICLES = 'articles'
MONGO_COLLECTION_HOT_EVENTS = 'hot_events'
MONGO_COLLECTION_HOT_EVENTS_BY_EDITOR = 'hot_events_editor'
MONGO_COLLECTION_NEW_ARTICLES_FOLLOW_EVENT = 'new_articles_follow_event'
MONGO_COLLECTION_SUMMRIES = 'summaries'
MONGO_COLLECTION_LONG_EVENTS = 'long_events'

MONGO_COLLECTION_NORMALIZED_ARTICLES = 'normalized_articles'

MONGO_COLLECTION_DONG_SEA = 'dong_sea_articles'

MONGO_COLLECTION_TTS_ARTICLES = 'tts_articles'
MONGO_COLLECTION_TTS_EVENTS = 'tts_events'


connection, db = utils.connect2mongo(MONGO_HOST, MONGO_PORT,
                                     MONGO_USER, MONGO_PASS,
                                     MONGO_DB)
category_collection = db.get_collection(u'categories')
try:
    categories = []
    documents = category_collection.find()
    for doc in documents:
        categories.append(doc[u'name_english'])
except:
    categories = [u'sport' , u'general', u'business', u'entertainment',
                  u'health', u'science', u'technology']