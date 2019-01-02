# -*- encoding: utf-8 -*

# MONGO_HOST = '103.35.64.122'
# MONGO_PORT = 2200
# MONGO_USER = 'dbMongo'
# MONGO_PASS = 'SOh3TbYhx8ypJPxmt1oOfL'

MONGO_HOST = '210.245.115.39'
MONGO_PORT = 27017
MONGO_USER = ''
MONGO_PASS = ''

MONGO_DB = 'dbMongo'

MONGO_COLLECTION_ARTICLES = 'articles'
MONGO_COLLECTION_HOT_EVENTS = 'hot_events'
MONGO_COLLECTION_HOT_EVENTS_BY_EDITOR = 'hot_events_editor'
MONGO_COLLECTION_NEW_ARTICLES_FOLLOW_EVENT = 'new_articles_follow_event'
MONGO_COLLECTION_SUMMRIES = 'summaries'
MONGO_COLLECTION_LONG_EVENTS = 'long_events'

MONGO_COLLECTION_NORMALIZED_ARTICLES = 'normalized_articles'

MONGO_COLLECTION_DONG_SEA = 'dong_sea_articles'

MONGO_COLLECTION_UPDATE_TIME = 'update_time'

MONGO_COLLECTION_TTS_ARTICLES = 'tts_articles'
MONGO_COLLECTION_TTS_EVENTS = 'tts_events'

categories = [u'giáo dục', u'thể thao', u'giải trí',
              u'thế giới', u'xã hội', u'văn hóa',
              u'đời sống', u'pháp luật', u'kinh tế',
              u'nhà đất', u'khoa học', u'công nghệ', u'xe cộ']

EVENT_MIN_TRENDING_DOCS = {u'giáo dục' : 10, u'thể thao' : 8, u'giải trí' : 10,
                           u'thế giới' : 15, u'xã hội':15, u'văn hóa' : 8,
                           u'đời sống' : 10, u'pháp luật' : 15, u'kinh tế' : 15,
                           u'nhà đất' : 10, u'khoa học' : 8, u'công nghệ' : 8,
                           u'xe cộ' : 8}