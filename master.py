# -*- encoding: utf-8 -*-

import os, sys, json
from event_detection.detect_event import event_detection
from get_stories import get_stories
from text_classification.classification import classification
from text_classification import my_map, utils
from collections import Counter
from multiprocessing import Process
import time, datetime
import warnings
from sklearn.externals import joblib
from nlp_tools import tokenizer
import config
from pymongo import MongoClient
from duplicate_documents.minhash_lsh import duplicate_docs as lsh
from text_summarization.summary import summary
import regex



warnings.filterwarnings('ignore', category=UserWarning)

TRENDING_MERGE_THRESHOLD = 0.0
HOUR_TO_RESET = 0  # reset at 3h AM
TIME_TO_SLEEP = 300

class master:
    def __init__(self):
        self.crawler = get_stories()
        self.lsh = lsh()
        self.text_clf = classification(root_dir='text_classification')
        self.text_clf.run()
        self.summary = summary(root_dir='text_summarization')
        self.docs_trending = {}
        self.trending_titles = {}
        self.date = datetime.datetime.now().date()
        self.first_run = True
        self.counter = {label:0 for label in my_map.label2domain.keys()}
        self.trending_result_dir = 'trending_result'
        self.trending_titles_file = os.path.join(self.trending_result_dir, 'trending_titles.pkl')
        self.docs_trending_file = os.path.join(self.trending_result_dir, 'docs_trending.pkl')
        self.duplicate_docs = {}
        self.titles = {}
        self.re = regex.regex()


    def run(self):
        while(True):
            if self.check_date() or self.first_run:
                self.reset_all()
                self.first_run = False

            print('run crawler...')
            self.crawler.run()
            if len(self.crawler.new_stories) == 0:
                time.sleep(TIME_TO_SLEEP)
                continue

            print('tokenize new stories...')
            new_tokenized_titles, new_tokenized_stories = self.tokenize_stories(self.crawler.new_titles,
                                                                                self.crawler.new_stories)

            print('run text classification...')
            self.text_clf.reset()
            labels = self.text_clf.predict(new_tokenized_stories)
            self.text_clf.save_to_dir(new_tokenized_stories, labels)

            self.update_counter(labels)

            print('run event detection...')
            trending_titles, docs_trending = self.run_event_detection()
            self.merge_trending(trending_titles, docs_trending)
            self.get_original_titles()

            print('remove duplicate stories...')
            new_tokenized_titles, new_tokenized_stories, new_duplicate_stories = \
                self.lsh.run(new_tokenized_titles, new_tokenized_stories)
            if len(new_duplicate_stories) > 0:
                self.update_duplicate(new_duplicate_stories)
                self.remove_duplicate_trending_docs()

            json_trending = self.build_json_trending()
            self.save_trending_to_mongo(json_trending)
            self.save_trending_to_file()

            print('summary stories...')
            self.save_summary_to_mongo(new_tokenized_titles, new_tokenized_stories)

            print('sleep in %d seconds...' % (TIME_TO_SLEEP))
            time.sleep(TIME_TO_SLEEP)


    def update_duplicate(self, new_duplicate_stories):
        new_duplicate_contents = []
        new_duplicate_contentId = new_duplicate_stories.keys()
        for contentId in new_duplicate_stories.keys():
            new_duplicate_contents.append(new_duplicate_stories[contentId])
        new_duplicate_labels = self.text_clf.predict(new_duplicate_contents)
        for i in xrange(len(new_duplicate_labels)):
            domain = my_map.label2domain[new_duplicate_labels[i]]
            contentId = new_duplicate_contentId[i]
            try:
                self.duplicate_docs[domain].update({contentId : True})
            except:
                self.duplicate_docs.update({domain : {contentId : True}})


    def remove_duplicate_trending_docs(self):
        for domain in self.docs_trending:
            try:
                duplicate_docs = self.duplicate_docs[domain]
                for k in self.docs_trending[domain].keys():
                    for i in xrange(len(self.docs_trending[domain][k])):
                        contentId = self.docs_trending[domain][k][i].split(u' == ')[0]
                        try:
                            _ = duplicate_docs[contentId]
                            del self.docs_trending[domain][k][i]
                        except: continue
            except: continue



    def tokenize_stories(self, titles, stories):
        tokenized_titles = []
        tokenized_stories = []
        for i in xrange(len(stories)):
            story = stories[i]
            title = titles[i]

            story = self.re.detect_url.sub(u'', story)

            tokenized_story = tokenizer.predict(story)
            tokenized_title = tokenized_story.split(u'\n')[0]

            tokenized_stories.append(tokenized_story)
            tokenized_titles.append(tokenized_title)

            contentId = tokenized_title.split(u' == ')[0]

            self.titles.update({contentId : title})

            print '\rtokenized %d stories' % (i + 1),
            sys.stdout.flush()
        print('')
        return tokenized_titles, tokenized_stories


    def get_original_titles(self):
        print('get original titles...')
        for domain in self.trending_titles.keys():
            for k in self.trending_titles[domain]:
                try:
                    tokenized_title = self.trending_titles[domain][k]
                    contentId = tokenized_title.split(u' == ')[0]
                    original_title = self.titles[contentId]
                    self.trending_titles[domain][k] = original_title
                    for i in xrange(len(self.docs_trending[domain][k])):
                        try:
                            tokenized_title = self.docs_trending[domain][k][i]
                            contentId = tokenized_title.split(u' == ')[0]
                            original_title = self.titles[contentId]
                            self.docs_trending[domain][k][i] = original_title
                        except:
                            # print('tokenized_title error: %s' % (tokenized_title))
                            continue
                except:
                    # print('tokenized_title error: %s' % (tokenized_title))
                    continue


    def merge_trending(self, trending_titles, docs_trending):
        print('merge trending...')
        for domain in trending_titles.keys():
            try:
                for k1 in trending_titles[domain].keys():
                    for k2 in self.trending_titles[domain].keys():
                        docs1 = [d.split(u' == ')[0] for d in docs_trending[domain][k1]]
                        docs2 = [d.split(u' == ')[0] for d in self.docs_trending[domain][k2]]
                        similarity = self.get_similarity_score(docs1, docs2)
                        if similarity > TRENDING_MERGE_THRESHOLD:
                            print('[%s] Similarity = %.2f -- MERGE -- %s <==> %s' %
                                  (domain, similarity, trending_titles[domain][k1],
                                   self.trending_titles[domain][k2]))
                            # union
                            self.union(self.docs_trending[domain][k2], docs_trending[domain][k1])
                            print ('Delete -- %s' % (trending_titles[domain][k1]))
                            del trending_titles[domain][k1]
                            del docs_trending[domain][k1]
                            break
            except:
                self.trending_titles.update({domain : {}})
                self.docs_trending.update({domain : {}})
                for i, k in enumerate(trending_titles[domain].keys()):
                    self.trending_titles[domain].update({i : trending_titles[domain][k]})
                    self.docs_trending[domain].update({i : docs_trending[domain][k]})
                continue
            for k in trending_titles[domain].keys():
                kk = len(self.trending_titles[domain])
                self.trending_titles[domain].update({kk : trending_titles[domain][k]})
                self.docs_trending[domain].update({kk : docs_trending[domain][k]})


    def union(self, doc1, doc2):
        contentID = {}
        for name in doc1:
            name = name.split(u' == ')
            contentID.update({name[0] : name[1]})
        for name in doc2:
            x = name.split(u' == ')
            try:
                _ = contentID[x[0]]
                continue
            except:
                doc1.append(name)



    def update_counter(self, labels):
        c = Counter(labels)
        for l, ndoc in c.items():
            self.counter[l] += ndoc


    def reset_all(self):
        print('reset all...')
        utils.delete_dir(self.trending_result_dir)
        self.trending_titles = {}
        self.docs_trending = {}
        self.crawler.remove_old_documents()
        self.lsh.clear()
        self.text_clf.reset()
        self.titles.clear()
        self.duplicate_docs.clear()
        for domain in my_map.domain2label.keys():
            event = event_detection(domain, None, root_dir='event_detection')
            event.reset_all()
        for l in self.counter.keys():
            self.counter[l] = 0


    # reset all if it is either the first run or at 3h AM on next day
    def check_date(self):
        present = datetime.datetime.now()
        diff = present.date() - self.date
        if diff.days >= 1 and present.hour == HOUR_TO_RESET:
            self.date = present.date()
            return True
        return False


    def run_event_detection(self):
        handles = []
        docs_trending = {}
        trending_titles = {}
        domains = []; events = {}
        for i, label in enumerate(self.counter.keys()):
            # if label != 0: continue # Chinh tri Xa hoi
            domain = my_map.label2domain[label]
            ndocs = self.counter[label]
            event = self.config_event_detection(domain, ndocs)
            if event == None:
                continue
            events.update({domain : event})
            handle = Process(target=events[domain].run, kwargs={'save2file':True})
            handle.start()
            handles.append(handle)
            domains.append(domain)
        for i in xrange(len(handles)):
            handles[i].join()
        print('All process have finished')
        self.get_trending(events, domains, trending_titles, docs_trending)
        return trending_titles, docs_trending


    def config_event_detection(self, domain, ndocs):
        if ndocs < 10:
            return None
        event = event_detection(domain,
                                os.path.join(self.text_clf.result_dir, domain),
                                root_dir='event_detection')
        return event


    def get_trending(self, events, domains, trending_titles, docs_trending):
        for domain in domains:
            try:
                event = events[domain]
                j, d = event.load_trending()
                docs_trending.update({domain: d})
                trending_titles.update({domain: j})
            except: continue


    def save_trending_to_file(self):
        utils.mkdir(self.trending_result_dir)
        joblib.dump(self.trending_titles, self.trending_titles_file, compress=True)
        joblib.dump(self.docs_trending, self.docs_trending_file, compress=True)


    def build_trending_domain(self, trending_titles, docs_trending):
        # build json content
        trending = []
        for k, title in trending_titles.items():
            event = {}
            docs = docs_trending[k]
            event.update({u'event_name': title.split(u' == ')[1]})
            sub_title = []
            for name in docs:
                name = name.split(u' == ')
                sub_title.append({u'title': name[1], u'contentId' : int(name[0])})
            # sub_title = [{u'title': name} for name in docs]
            event.update({u'stories': sub_title})
            trending.append(event)
        return trending


    def build_json_trending(self):
        hot_events = []
        for domain in self.trending_titles.keys():
            json_content = {}
            json_content.update({u'domain': domain, u'id': domain.replace(u' ', u'-').lower()})
            trending_domain = self.build_trending_domain(self.trending_titles[domain],
                                                         self.docs_trending[domain])
            json_content.update({u'content': trending_domain})
            hot_events.append(json_content)
        hot_events = json.dumps(hot_events, ensure_ascii=False, encoding='utf-8')
        json_trending = {u'hot_events' : hot_events, u'date' : self.date.strftime(u'%Y-%m-%d')}
        return json_trending


    def save_trending_to_mongo(self, json_trending):
        print('save trending to mongodb...')
        # connect to mongodb
        connection = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
        db = connection[config.MONGO_DB]
        # db.authenticate(config.MONGO_USER, config.MONGO_PASS)
        try:
            collection = db.get_collection(config.MONGO_COLLECTION_HOT_EVENTS)
        except:
            collection = db.create_collection(config.MONGO_COLLECTION_HOT_EVENTS)
        documents = collection.find({u'date' : {u'$eq' : self.date.strftime(u'%Y-%m-%d')}})
        for doc in documents:
            collection.remove(doc[u'_id'])
        collection.insert_one(json_trending)
        connection.close()


    def save_summary_to_mongo(self, new_tokenized_titles, new_tokenized_stories):
        print('save summary to mongodb...')
        # connect to mongodb
        connection = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
        db = connection[config.MONGO_DB]
        # db.authenticate(config.MONGO_USER, config.MONGO_PASS)

        try:
            collection = db.get_collection(config.MONGO_COLLECTION_SUMMRIES)
        except:
            collection = db.create_collection(config.MONGO_COLLECTION_SUMMRIES)
        begin_time = time.time()
        for i in xrange(len(new_tokenized_stories)):
            summ = self.summary.run(new_tokenized_stories[i])
            tokenized_title = new_tokenized_titles[i].split(u' == ')
            contentId = tokenized_title[0]
            try:
                title = self.titles[tokenized_title[0]].split(u' == ')[1]
            except:
                title = tokenized_title[1].replace(u'_', u' ')
            summary = {u'contentId' : int(contentId), u'title' : title, u'summaries' : summ}
            collection.insert_one(summary)
            print '\rsummaried %d stories' % (i+1),
            sys.stdout.flush()
        end_time = time.time()
        print('')
        print ('time to summary = %.2f minutes' % (float(end_time - begin_time) / float(60)))
        connection.close()


    def get_similarity_score(self, docs1, docs2):
        set1 = set(docs1)
        set2 = set(docs2)
        if len(set1) >= len(set2):
            m = float(len(set2))
        else:
            m = float(len(set1))
        if m == 0: return 0.0
        intersection = float(len(set1.intersection(set2)))
        return intersection / m



if __name__ == '__main__':
    m = master()
    m.run()