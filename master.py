# -*- encoding: utf-8 -*-

import os
from event_detection.detect_event import event_detection
from baomoi_crawler.crawler import crawler
from text_classification.classification import classification
from text_classification import my_map
from collections import Counter
from multiprocessing import Process
import time, datetime
import warnings




warnings.filterwarnings('ignore', category=UserWarning)


class master:
    def __init__(self):
        self.crawler = crawler()
        self.text_clf = classification(root_dir='text_classification')
        self.text_clf.run()
        self.docs_trending = {}
        self.trending_titles = {}
        self.date = datetime.datetime.now().date()
        self.first_run = True
        self.counter = {label:0 for label in my_map.label2name.keys()}


    def run(self):
        while(True):
            # if self.check_date() or self.first_run:
            #     self.reset_all()
            #     self.first_run = False
            #
            # print('run crawler...')
            # self.crawler.run()
            #
            # print('run text classification...')
            # self.text_clf.reset()
            # labels = self.text_clf.predict(self.crawler.new_stories)
            # self.text_clf.save_to_dir(self.crawler.new_stories, labels)
            #
            # self.update_counter(labels)
            self.counter = {0:231}
            print('run event detection...')
            trending_titles, docs_trending = self.run_event_detection()
            self.docs_trending = docs_trending
            self.trending_titles = trending_titles

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


    def run_event_detection(self):
        handles = []
        docs_trending = {}
        trending_titles = {}
        domains = []; events = {}
        for i, label in enumerate(self.counter.keys()):
            if label != 0: continue # topic 'Chinh tri Xa hoi'
            domain = my_map.label2name[label]
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
        return docs_trending, trending_titles


    def config_event_detection(self, domain, ndocs):
        if ndocs < 10:
            return None
        if ndocs > 1000:
            event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                    root_dir='event_detection', num_topics=100, max_iter=1300)
        elif 500 < ndocs and ndocs <= 1000:
            event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                    root_dir='event_detection', num_topics=50, max_iter=1300)
        elif 350 < ndocs and ndocs <= 500:
            event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                    root_dir='event_detection', num_topics=30, max_iter=1300)
        elif 200 < ndocs and ndocs <= 350:
            event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                    root_dir='event_detection', num_topics=20, max_iter=1300)
        elif 50 < ndocs and ndocs <= 200:
            event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                    root_dir='event_detection', num_topics=15, max_iter=1300)
        else:
            event = event_detection(domain, os.path.join(self.text_clf.result_dir, domain),
                                    root_dir='event_detection', num_topics=10, max_iter=1300)
        return event


    def get_trending(self, events, domains, trending_titles, docs_trending):
        for domain in domains:
            event = events[domain]
            d, j = event.load_trending()
            docs_trending.update({domain: d})
            trending_titles.update({domain: j})




if __name__ == '__main__':
    m = master()
    m.run()