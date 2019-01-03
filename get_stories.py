import json
from bs4 import BeautifulSoup
from datetime import datetime
import config
from sklearn.externals import joblib
from dateutil.parser import parse



class get_stories:
    def __init__(self):
        self.contentId = self.load_contentId()
        self.ids = {}
        self.new_stories = []
        self.new_titles = []
        self.new_categories = []
        self.new_dates = []
        self.new_publisher = []


    def run(self, db):
        collection = db.get_collection(config.MONGO_COLLECTION_ARTICLES)
        documents = collection.find({u'contentId' : {u'$gt' : self.contentId}})

        del self.new_stories[:]
        del self.new_titles[:]
        del self.new_categories[:]
        del self.new_dates[:]
        del self.new_publisher[:]

        for doc in documents:
            date_obj = parse(doc[u'date'])
            publisher = doc[u'publisherName'].strip()
            if self.check_date(date_obj):
                continue
            title, story, category = self.get_content(doc)
            if story == u'' or title == u'':
                continue
            self.new_dates.append(date_obj)
            self.new_publisher.append(publisher)
            self.new_stories.append(story.strip())
            self.new_titles.append(title)
            self.new_categories.append(category.lower())

        print('There are %d new stories' % len(self.new_stories))

        self.save_contentId()


    def check_date(self, date_obj):
        datetime_obj = date_obj.date()
        now = datetime.now()
        diff = now.date() - datetime_obj
        if diff.days != 0:
            return True
        return False


    def get_content(self, doc):
        doc_id = doc[u'_id']
        if self.is_exist(doc_id):
            return u'', u'', u''
        contentId = doc[u'contentId']
        title = doc[u'title'].strip()
        if title != u'':
            title = u' == '.join([unicode(contentId), title])
            print(title)
        else:
            return u'', u'', u''
        tags = map(lambda x: x.strip(), json.loads(doc[u'tags'], encoding='utf-8'))
        tags = u'[tags] : ' + u' , '.join(tags)
        description = doc[u'description'].strip()
        raw_body = json.loads(doc[u'body'], encoding='utf-8')
        body = self.get_body(raw_body)
        story = u'\n'.join([title, description, body, tags])

        if contentId > self.contentId:
            self.contentId = contentId

        category = doc[u'parentCategoryName'].strip().lower()

        return title, story, category


    def get_body(self, raw_body):
        clean_body = []
        for content in raw_body:
            try:
                if content[u'type'] != u'text':
                    continue
                clean_content = BeautifulSoup(content[u'content']).text.strip()
                clean_body.append(clean_content)
            except:
                continue
        return u'\n'.join(clean_body)


    def is_exist(self, doc_id):
        try:
            _ = self.ids[doc_id]
            return True
        except:
            self.ids.update({doc_id : True})
            return False


    def clear(self):
        del self.new_stories[:]
        del self.new_titles[:]
        del self.new_categories[:]
        del self.new_dates[:]
        del self.new_publisher[:]
        self.ids.clear()


    def save_contentId(self):
        joblib.dump(self.contentId, 'contentId.pkl')


    def load_contentId(self):
        try:
            contentId = joblib.load('contentId.pkl')
            return contentId
        except: return 0





if __name__ == '__main__':
    import utils

    connection, db = utils.connect2mongo(config.MONGO_HOST, config.MONGO_PORT,
                                         config.MONGO_USER, config.MONGO_PASS,
                                         config.MONGO_DB)

    stories = get_stories()
    stories.run(db)

    connection.close()