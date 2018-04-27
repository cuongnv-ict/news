# -*- encoding: utf-8 -*-

import os
from event_detection.detect_event import event_detection
from baomoi_crawler.crawler import crawler
from text_classification.classification import classification
from text_classification import my_map
from collections import Counter
from multiprocessing import Process
import time, datetime
from sklearn.externals import joblib



class master:
    def __init__(self):
        self.crawler = crawler()
        self.text_clf = classification(root_dir='text_classification')
        self.text_clf.run()
        self.documents = {}
        self.trending_jsons = {}
        self.date = datetime.datetime.now().date()
        self.first_run = True
        self.counter = {label:0 for label in my_map.label2name.keys()}


    def run(self):
        while(True):
            if self.check_date() or self.first_run:
                self.reset_all()
                self.first_run = False

            print('run crawler...')
            self.crawler.run()
            joblib.dump(self.crawler.new_stories, 'new_stories.pkl')
            self.crawler.new_stories = joblib.load('new_stories.pkl')

            print('run text classification...')
            self.text_clf.reset()
            labels = self.text_clf.predict(self.crawler.new_stories)
            self.text_clf.save_to_dir(self.crawler.new_stories, labels)

            self.update_counter(labels)

            print('run event detection...')
            documents, trending_jsons = self.run_event()
            self.documents = documents
            self.trending_jsons = trending_jsons

            time.sleep(1300)


    def update_counter(self, labels):
        c = Counter(labels)
        for l, ndoc in c.items():
            self.counter[l] += ndoc


    def reset_all(self):
        self.crawler.remove_old_documents()
        self.text_clf.reset()
        for domain in my_map.name2label.keys():
            event = event_detection(domain, None, root_dir='event_detection')
            event.reset_all()
        for l in self.counter.keys():
            self.counter[l] = 0


    def check_date(self):
        present = datetime.datetime.now().date()
        if self.date < present:
            self.date = present
            return True
        return False


    def run_event(self):
        handles = []
        documents = {}
        trending_json = {}
        domains = []
        events = {}
        for i, label in enumerate(self.counter.keys()):
            if label != 7: continue
            domain = my_map.label2name[label]
            ndocs = self.counter[label]
            if ndocs < 10:
                continue
            if ndocs > 500:
                event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                        root_dir='event_detection', num_topics=100)
            elif 350 <= ndocs:
                event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                        root_dir='event_detection', num_topics=50)
            elif 200 <= ndocs and ndocs < 350:
                event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                        root_dir='event_detection', num_topics=30)
            elif 50 <= ndocs and ndocs < 200:
                event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                        root_dir='event_detection', num_topics=20)
            else:
                event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                        root_dir='event_detection', num_topics=10)
            events.update({domain : event})
            handle = Process(target=events[domain].run_demo)
            handle.start()
            handles.append(handle)
            domains.append(domain)
        for i in xrange(len(handles)):
            handles[i].join()
        print('All process have finished')
        self.get_trending(events, domains, documents, trending_json)
        return documents, trending_json


    def get_trending(self, events, domains, documents, trending_json):
        for domain in domains:
            event = events[domain]
            d, j = event.load_trending()
            documents.update({domain: d})
            trending_json.update({domain: j})



if __name__ == '__main__':
    m = master()
    m.run()