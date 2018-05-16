import json
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import config



class get_stories:
    def __init__(self):
        self.contentId = 0
        self.ids = {}
        self.new_stories = []
        self.new_titles = []


    def run(self):
        # connect to mongodb
        connection = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
        db = connection[config.MONGO_DB]
        # db.authenticate(config.MONGO_USER, config.MONGO_PASS)

        collection = db.get_collection(config.MONGO_COLLECTION_ARTICLES)
        documents = collection.find({u'contentId' : {u'$gt' : self.contentId}})

        del self.new_stories[:]
        del self.new_titles[:]

        for doc in documents:
            date = doc[u'date']
            if self.check_date(date):
                continue
            title, story = self.get_content(doc)
            if story == u'' or title == u'':
                continue
            self.new_stories.append(story.strip())
            self.new_titles.append(title)
            # if len(self.new_stories) > 1000: break
        print('There are %d new stories' % len(self.new_stories))

        connection.close()


    def check_date(self, raw_date):
        date_str = raw_date.split(u'T')[0]
        datetime_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        now = datetime.now()
        diff = now.date() - datetime_obj
        if diff.days != 0:
            return True
        return False


    def get_content(self, doc):
        doc_id = doc[u'_id']
        if self.is_exist(doc_id):
            return u''
        title = doc[u'title'].strip()
        print(title)
        description = doc[u'description'].strip()
        raw_body = json.loads(doc[u'body'], encoding='utf-8')
        body = self.get_body(raw_body)
        story = u'\n'.join([title, description, body])

        contentId = doc[u'contentId']
        if contentId > self.contentId:
            self.contentId = contentId

        return title, story


    def get_body(self, raw_body):
        clean_body = []
        for content in raw_body:
            try:
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


    def remove_old_documents(self):
        del self.new_stories[:]
        del self.new_titles[:]
        self.ids.clear()





if __name__ == '__main__':
    stories = get_stories()
    stories.run()