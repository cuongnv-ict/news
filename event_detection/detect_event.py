# -*- encoding: utf-8 -*-
import preprocessing
import build_data
import utils
import os
from random import randint
from sklearn.externals import joblib
from sklearn.cluster import DBSCAN



MIN_DOCS = 5
MIN_TRENDING_DOCS = 10

class event_detection:
    def __init__(self, domain, dataset, root_dir='.'):
        self.domain = domain
        self.dataset = dataset
        self.root_dir = root_dir
        self.root_output_dir = os.path.join(self.root_dir, 'event_result')
        self.domain_output_dir = os.path.join(self.root_output_dir, self.domain)
        self.clean_dataset_dir = os.path.join(self.domain_output_dir, 'clean_dataset')
        self.title_dir = os.path.join(self.domain_output_dir, 'titles')
        self.title_file = os.path.join(self.title_dir, 'titles.dat')
        self.title_map_file = os.path.join(self.title_dir, 'title_map_file.pkl')
        self.topic_result_dir = os.path.join(self.domain_output_dir, 'topics')
        self.topic_result_file = os.path.join(self.topic_result_dir, 'topics.txt')
        self.vocab_file = os.path.join(self.domain_output_dir, 'vocab.dat')
        self.trending_titles_file = os.path.join(self.domain_output_dir, 'trending_titles.pkl')
        self.docs_trending_file = os.path.join(self.domain_output_dir, 'docs_trending.pkl')
        self.docs_content_file = os.path.join(self.domain_output_dir, 'docs_content.pkl')
        self.trending_json_file = os.path.join(self.domain_output_dir, 'trending_json.pkl')


    def load_title_map(self):
        try:
            return joblib.load(self.title_map_file)
        except:
            return None


    def save_title_map(self, title_map):
        utils.mkdir(self.title_dir)
        joblib.dump(title_map, self.title_map_file, compress=True)


    def prepare_data(self):
        title_map = self.load_title_map()
        if title_map == None:
            title_map = {}
        names = build_data.update_title_map(self.dataset, title_map)
        preprocessing.remove_stop_postag(self.dataset, self.clean_dataset_dir, names)
        vectorizer, contents, titles = build_data.build_vocab(self.clean_dataset_dir,
                                                              self.vocab_file,
                                                              self.root_dir, title_map)
        print('There are %s docs in domain %s' % (len(contents), self.domain))
        # build_data.save_titles_to_file(titles, self.title_dir, self.title_file)
        self.save_title_map(title_map)
        return titles, vectorizer.transform(contents)


    def reset_all(self):
        utils.delete_dir(self.domain_output_dir)


    def get_trending(self, clusters, total, titles):
        trending_titles = {}
        docs_trending = {}
        trending_threshold = self.get_trending_threshold(total)
        for k, cluster in clusters.items():
            if len(cluster) < MIN_DOCS:
                continue
            percent = float(len(cluster)) / float(total)
            if percent < trending_threshold and len(cluster) < MIN_TRENDING_DOCS:
                continue
            docs_trending.update({k : [titles[i] for i in cluster]})
            index = randint(0, len(cluster) - 1)
            trending_titles.update({k : titles[cluster[index]]})
        return trending_titles, docs_trending


    def get_trending_threshold(self, ndocs):
        if ndocs < 20:
            threshold = 0.21
        elif ndocs < 50:
            threshold = 0.12
        elif ndocs < 350:
            threshold = 0.08
        elif ndocs < 1000:
            threshold = 0.05
        elif ndocs < 1500:
            threshold = 0.035
        else:
            threshold = 0.0275
        return threshold


    def run(self, save2file=False):
        utils.mkdir(self.root_output_dir)
        utils.mkdir(self.domain_output_dir)

        titles, X = self.prepare_data()

        # dbscan use cosine_distance is metric.
        # note that: cosine_distance = 1 - cosine_similarity
        clustering = DBSCAN(eps=0.5, min_samples=3, metric='cosine')
        labels = clustering.fit_predict(X)
        clusters = self.get_cluster(labels)
        total = len(labels)

        trending_titles, docs_trending = self.get_trending(clusters, total, titles)

        if save2file:
            self.save_trending(trending_titles, docs_trending)
        return trending_titles, docs_trending


    def get_cluster(self, labels):
        cluster = {}
        for k, label in enumerate(labels):
            if label == -1:
                continue
            try:
                cluster[label].append(k)
            except:
                cluster.update({label : [k]})
        return cluster


    def save_trending(self, trending_titles, docs_trending):
        joblib.dump(trending_titles, self.trending_titles_file, compress=True)
        joblib.dump(docs_trending, self.docs_trending_file, compress=True)


    def load_trending(self):
        trending_titles = joblib.load(self.trending_titles_file)
        docs_trending = joblib.load(self.docs_trending_file)
        return trending_titles, docs_trending
