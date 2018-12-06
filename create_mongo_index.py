# -*- encoding: utf-8 -*-

import config
import utils


connection, db = utils.connect2mongo(config.MONGO_HOST, config.MONGO_PORT,
                                     config.MONGO_USER, config.MONGO_PASS,
                                     config.MONGO_DB)


print('create mongo index ...')

try:
    collection = db.get_collection(config.MONGO_COLLECTION_ARTICLES)
    utils.create_mongo_index(collection, u'contentId')

    collection = db.get_collection(config.MONGO_COLLECTION_NORMALIZED_ARTICLES)
    utils.create_mongo_index(collection, u'contentId')

    collection = db.get_collection(config.MONGO_COLLECTION_SUMMRIES)
    utils.create_mongo_index(collection, u'contentId')

    collection = db.get_collection(config.MONGO_COLLECTION_NEW_ARTICLES_FOLLOW_EVENT)
    utils.create_mongo_index(collection, u'contentId')

    collection = db.get_collection(config.MONGO_COLLECTION_DONG_SEA)
    utils.create_mongo_index(collection, u'contentId')

    collection = db.get_collection(config.MONGO_COLLECTION_HOT_EVENTS)
    utils.create_mongo_index(collection, u'date')

    collection = db.get_collection(config.MONGO_COLLECTION_HOT_EVENTS_BY_EDITOR)
    utils.create_mongo_index(collection, u'event_id')

    collection = db.get_collection(config.MONGO_COLLECTION_LONG_EVENTS)
    utils.create_mongo_index(collection, u'event_id')

    collection = db.get_collection(config.MONGO_COLLECTION_UPDATE_TIME)
    utils.create_mongo_index(collection, u'name')
except Exception as e:
    print(e.message)