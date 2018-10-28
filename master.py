# -*- encoding: utf-8 -*-

import os, sys, json
from event_detection.detect_event import event_detection
from get_stories import get_stories
from collections import Counter
from multiprocessing import Process
import time, datetime
import warnings
import config, utils
from sklearn.externals import joblib
from nlp_tools import tokenizer
from duplicate_documents.minhash_lsh import duplicate_docs as lsh
from text_summarization.summary import summary
import get_Dong_sea_articles as dong_sea
from news_normalization.normalization import normalization
import copy



warnings.filterwarnings('ignore', category=UserWarning)

TRENDING_MERGE_THRESHOLD = 0.0
HOUR_TO_RESET = 0  # reset at 0h AM
TIME_TO_SLEEP = 60 * 3 # sleep in 3 minutes

class master:
    def __init__(self):
        self.crawler = get_stories()
        self.lsh = lsh()
        self.normalization = normalization(root_dir='news_normalization')
        self.summary = summary(root_dir='text_summarization')
        self.docs_trending = {}
        self.trending_titles = {}
        self.date = datetime.datetime.now().date()
        self.first_run = True
        self.counter = {domain.lower() : 0 for domain in config.categories}
        self.trending_result_dir = 'trending_result'
        self.trending_titles_file = os.path.join(self.trending_result_dir, 'trending_titles.pkl')
        self.docs_trending_file = os.path.join(self.trending_result_dir, 'docs_trending.pkl')
        self.duplicate_docs = {}
        self.titles = {}
        self.event_id = {}


    def run(self):
        while(True):
            try:
                if self.first_run or self.check_date():
                    self.reset_all()
                    self.first_run = False

                print('connect to mongodb...')
                connection, db = utils.connect2mongo(config.MONGO_HOST, config.MONGO_PORT,
                                                     config.MONGO_USER, config.MONGO_PASS,
                                                     config.MONGO_DB)

                print('run crawler...')
                self.crawler.run(db)
                if len(self.crawler.new_stories) == 0:
                    time.sleep(TIME_TO_SLEEP)
                    continue

                print('tokenize new stories...')
                new_tokenized_titles, new_tokenized_stories = self.tokenize_stories(self.crawler.new_titles,
                                                                                    self.crawler.new_stories)

                articles_category = self.get_article_by_category(new_tokenized_stories,
                                                                 self.crawler.new_categories)

                self.update_counter(self.crawler.new_categories)

                print('run event detection...')
                trending_titles, docs_trending = self.run_event_detection(articles_category)
                self.merge_trending(trending_titles, docs_trending)
                self.merge_trending_ex()
                self.get_original_titles()

                print('remove duplicate stories...')
                new_tokenized_titles_clean, new_tokenized_stories_clean, new_duplicate_categories = \
                    self.lsh.run(new_tokenized_titles, new_tokenized_stories, self.crawler.new_categories)
                if len(new_duplicate_categories) > 0:
                    self.update_duplicate_docs(new_duplicate_categories)
                trending_titles, docs_trending = self.remove_duplicate_trending_docs()

                json_trending = self.build_json_trending(trending_titles, docs_trending)
                self.save_trending_to_mongo(db, json_trending)
                self.save_trending_to_file(trending_titles, docs_trending)

                print('summary stories...')
                self.save_summary_to_mongo(db, new_tokenized_titles_clean,
                                           new_tokenized_stories_clean)

                print('get articles talk about Dong sea...')
                dong_sea.get_articles(db, new_tokenized_titles_clean,
                                      new_tokenized_stories_clean, self.titles)

                connection.close()

                print('sleep in %d seconds...' % (TIME_TO_SLEEP))
                time.sleep(TIME_TO_SLEEP)
            except:
                print(u'Exception occured in master module')
                try:
                    connection.close()
                except: pass
                time.sleep(TIME_TO_SLEEP)
                continue


    def get_article_by_category(self, new_tokenized_stories, categories):
        articles = {}
        for i in xrange(len(categories)):
            try:
                articles[categories[i].lower()].append(new_tokenized_stories[i])
            except:
                articles.update({categories[i].lower() : [new_tokenized_stories[i]]})
        return articles


    def update_duplicate_docs(self, new_duplicate_categories):
        for contentId, domain in new_duplicate_categories.items():
            try:
                self.duplicate_docs[domain].update({contentId : True})
            except:
                self.duplicate_docs.update({domain : {contentId : True}})


    def remove_duplicate_trending_docs(self):
        trending_titles = copy.deepcopy(self.trending_titles)
        docs_trending = copy.deepcopy(self.docs_trending)
        for domain in docs_trending:
            try:
                duplicate_docs = self.duplicate_docs[domain]
                for k in docs_trending[domain].keys():
                    docs = list(docs_trending[domain][k])
                    for doc in docs:
                        contentId = doc.split(u' == ')[0]
                        try:
                            _ = duplicate_docs[contentId]
                            docs_trending[domain][k].remove(doc)
                        except: continue
                    if len(docs_trending[domain][k]) == 0:
                        del docs_trending[domain][k]
                        del trending_titles[domain][k]
            except: continue
        return trending_titles, docs_trending


    def tokenize_stories(self, titles, stories):
        tokenized_titles = []
        tokenized_stories = []
        for i in xrange(len(stories)):
            story = stories[i]
            title = titles[i]

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
                            continue
                except:
                    continue


    def merge_trending(self, trending_titles, docs_trending):
        print('merge trending...')
        for domain in trending_titles.keys():
            try:
                for k1 in trending_titles[domain].keys():
                    for k2 in self.trending_titles[domain].keys():
                        docs1 = [d.split(u' == ')[0] for d in docs_trending[domain][k1]]
                        docs2 = [d.split(u' == ')[0] for d in self.docs_trending[domain][k2]]
                        similarity = utils.get_similarity_score(docs1, docs2)
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
                for k in trending_titles[domain].keys():
                    id = utils.id_generator()
                    self.trending_titles[domain].update({id : trending_titles[domain][k]})
                    self.docs_trending[domain].update({id : docs_trending[domain][k]})
                continue
            for k in trending_titles[domain].keys():
                id = utils.id_generator()
                self.trending_titles[domain].update({id : trending_titles[domain][k]})
                self.docs_trending[domain].update({id : docs_trending[domain][k]})


    def merge_trending_ex(self):
        print('merge trending extra..')
        for domain in self.trending_titles.keys():
            try:
                for k1 in self.trending_titles[domain].keys():
                    for k2 in self.trending_titles[domain].keys():
                        if k1 == k2: continue
                        docs1 = [d.split(u' == ')[0] for d in self.docs_trending[domain][k1]]
                        docs2 = [d.split(u' == ')[0] for d in self.docs_trending[domain][k2]]
                        similarity = utils.get_similarity_score(docs1, docs2)
                        if similarity > TRENDING_MERGE_THRESHOLD:
                            print('[%s] Similarity = %.2f -- MERGE -- %s <==> %s' %
                                  (domain, similarity, self.trending_titles[domain][k1],
                                   self.trending_titles[domain][k2]))
                            # union
                            self.union(self.docs_trending[domain][k2], self.docs_trending[domain][k1])
                            print ('Delete -- %s' % (self.trending_titles[domain][k1]))
                            del self.trending_titles[domain][k1]
                            del self.docs_trending[domain][k1]
                            break
            except: pass


    def union(self, doc1, doc2):
        contentId = {}
        for name in doc1:
            name = name.split(u' == ')
            contentId.update({name[0] : name[1]})
        for name in doc2:
            x = name.split(u' == ')
            try:
                _ = contentId[x[0]]
                continue
            except:
                doc1.append(name)


    def update_counter(self, labels):
        c = Counter(labels)
        for l, ndoc in c.items():
            try:
                self.counter[l] += ndoc
            except Exception as e:
                print(u'Exception in update_counter. %s is not in self.counter' % (e.message))


    def reset_all(self):
        print('reset all...')
        utils.delete_dir(self.trending_result_dir)

        self.trending_titles.clear()
        self.docs_trending.clear()
        self.event_id.clear()
        self.titles.clear()

        self.crawler.clear()

        self.lsh.clear()
        self.duplicate_docs.clear()

        for domain in config.categories:
            event = event_detection(domain, None, root_dir='event_detection')
            event.reset_all()

        for l in self.counter.keys():
            self.counter[l] = 0


    # reset all if it is either the first run or at 00:00 on next day
    def check_date(self):
        present = datetime.datetime.now()
        diff = present.date() - self.date
        if diff.days > 0 and present.hour == HOUR_TO_RESET:
            self.date = present.date()
            return True
        return False


    def run_event_detection(self, articles_category):
        handles = []
        docs_trending = {}
        trending_titles = {}
        domains = []; events = {}
        for domain in self.counter.keys():
            try:
                ndocs = self.counter[domain]
                event = self.config_event_detection(domain, articles_category[domain], ndocs)
                if event == None:
                    continue
                events.update({domain : event})
                handle = Process(target=events[domain].run, kwargs={'save2file':True})
                handle.start()
                handles.append(handle)
                domains.append(domain)
            except:
                continue
        for i in xrange(len(handles)):
            handles[i].join()
        print('All process have finished')
        self.get_trending(events, domains, trending_titles, docs_trending)
        return trending_titles, docs_trending


    def config_event_detection(self, domain, dataset, ndocs):
        if ndocs < 10:
            return None
        event = event_detection(domain, dataset,
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


    def save_trending_to_file(self, trending_titles, docs_trending):
        utils.mkdir(self.trending_result_dir)
        joblib.dump(trending_titles, self.trending_titles_file, compress=True)
        joblib.dump(docs_trending, self.docs_trending_file, compress=True)


    def get_event_id(self, event_name):
        try:
            event_id = self.event_id[event_name]
        except:
            event_id = utils.id_generator()
            self.event_id.update({event_name: event_id})
        return event_id


    def build_trending_domain(self, trending_titles, docs_trending):
        # build json content
        trending = []
        for k, title in trending_titles.items():
            event = {}
            docs = docs_trending[k]
            event_name = title.split(u' == ')[1]
            event_id = self.get_event_id(event_name)
            event.update({u'event_name': event_name, u'event_id' : event_id})
            sub_title = []
            for name in docs:
                name = name.split(u' == ')
                sub_title.append({u'title': name[1], u'contentId' : int(name[0])})
            # sub_title = [{u'title': name} for name in docs]
            event.update({u'stories': sub_title})
            trending.append(event)
        return trending


    def build_json_trending(self, trending_titles, docs_trending):
        hot_events = []
        for domain in trending_titles.keys():
            json_content = {}
            json_content.update({u'domain': domain, u'id': domain.replace(u' ', u'-').lower()})
            trending_domain = self.build_trending_domain(trending_titles[domain],
                                                         docs_trending[domain])
            json_content.update({u'content': trending_domain})
            hot_events.append(json_content)
        hot_events = json.dumps(hot_events, ensure_ascii=False, encoding='utf-8')
        json_trending = {u'hot_events' : hot_events, u'date' : self.date.strftime(u'%Y-%m-%d')}
        return json_trending


    def save_trending_to_mongo(self, db, json_trending):
        print('save trending to mongodb...')
        try:
            collection = db.get_collection(config.MONGO_COLLECTION_HOT_EVENTS)
        except:
            collection = db.create_collection(config.MONGO_COLLECTION_HOT_EVENTS)
        documents = collection.find({u'date' : {u'$eq' : self.date.strftime(u'%Y-%m-%d')}})
        for doc in documents:
            collection.remove(doc[u'_id'])
        collection.insert_one(json_trending)


    def save_summary_to_mongo(self, db, new_tokenized_titles, new_tokenized_stories):
        print('save summary to mongodb...')

        try:
            collection = db.get_collection(config.MONGO_COLLECTION_SUMMRIES)
        except:
            collection = db.create_collection(config.MONGO_COLLECTION_SUMMRIES)

        begin_time = time.time()
        for i in xrange(len(new_tokenized_stories)):
            tokenized_title = new_tokenized_titles[i].split(u' == ')
            contentId = tokenized_title[0]
            try:
                title = self.titles[tokenized_title[0]].split(u' == ')[1]
            except:
                title = tokenized_title[1].replace(u'_', u' ')

            # normalize article before summary
            des, body = utils.get_des_and_remove_tags(new_tokenized_stories[i])
            normalized_title = self.normalization.run(tokenized_title[1])
            normalized_des = self.normalization.run(des)
            normalized_body = self.normalization.run(body)
            normalized_article = u'\n'.join([normalized_title, normalized_des, normalized_body])

            summ = self.summary.run(title=normalized_title,
                                    des=normalized_des,
                                    body=normalized_body)
            summary = {u'contentId' : int(contentId), u'title' : title,
                       u'summaries' : summ, u'normalized_article' : normalized_article}
            collection.insert_one(summary)
            print '\rsummaried %d stories' % (i+1),
            sys.stdout.flush()
        end_time = time.time()
        print('')
        print ('time to summary = %.2f minutes' % (float(end_time - begin_time) / float(60)))




if __name__ == '__main__':
    m = master()
    m.run()