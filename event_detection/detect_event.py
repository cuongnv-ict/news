# -*- encoding: utf-8 -*-
import preprocessing
import create_lda_data as lda
import subprocess
import topics
import utils
import os
import demo
import json
from sklearn.externals import joblib



class event_detection:
    def __init__(self, domain, dataset, root_dir='.', num_topics=50, max_iter=500):
        self.domain = domain
        self.dataset = dataset
        self.root_dir = root_dir
        self.num_topics = num_topics
        self.max_iter = max_iter
        self.root_output_dir = os.path.join(self.root_dir, 'event_result')
        self.domain_output_dir = os.path.join(self.root_output_dir, self.domain)
        self.clean_dataset_dir = os.path.join(self.domain_output_dir, 'clean_dataset')
        self.title_dir = os.path.join(self.domain_output_dir, 'titles')
        self.title_file = os.path.join(self.title_dir, 'titles.dat')
        self.lda_dataset_dir = os.path.join(self.domain_output_dir, 'lda_dataset')
        self.lda_train_file = os.path.join(self.lda_dataset_dir, 'mult.dat')
        self.lda_gibb_dir = os.path.join(self.root_dir, 'lda_gibb')
        self.lda_bin_file = os.path.join(self.lda_gibb_dir, 'lda')
        self.lda_output_dir = '/'.join([self.domain_output_dir,
                                        '_'.join(['lda', 'fit', str(self.num_topics)])])
        self.lda_theta_file = os.path.join(self.lda_output_dir, 'final.doc.states')
        self.lda_beta_file = os.path.join(self.lda_output_dir, 'final.topics')
        self.topic_result_dir = os.path.join(self.domain_output_dir, 'topics')
        self.topic_result_file = os.path.join(self.topic_result_dir, 'topics.txt')
        self.vocab_file = os.path.join(self.domain_output_dir, 'vocab.dat')


    def prepare_data(self):
        # prepare LDA dataset
        preprocessing.remove_stop_postag(self.dataset, self.clean_dataset_dir)
        contents = lda.build_vocab(self.clean_dataset_dir, self.vocab_file, self.root_dir)
        print('There are %s docs in domain %s' % (len(contents), self.domain))
        vocab = lda.load_vocab(self.vocab_file)
        lda.get_lda_data(contents, vocab, self.lda_dataset_dir, self.lda_train_file)
        lda.get_title(self.dataset, self.title_dir, self.title_file)


    def reset_all(self):
        utils.delete_dir(self.domain_output_dir)


    def run_gibb_LDA(self):
        # run LDA
        command = [self.lda_bin_file, '--directory', self.lda_output_dir,
                   '--train_data', self.lda_train_file,
                   '--num_topics', str(self.num_topics), '--save_lag', '10000',
                   '--eta', '0.01', '--alpha', '0.1', '--max_iter', str(self.max_iter)]
        subprocess.call(command)
        # print('\nlda training has finished')


    def get_trending(self):
        # print topics and get trending topics
        theta, topics_title, titles = topics.get_topics_title(
            self.lda_theta_file,
            self.title_file)
        utils.mkdir(self.topic_result_dir)
        topics.print_topics(self.lda_beta_file, topics_title,
                            self.vocab_file, 20, self.topic_result_file)
        trending_titles, docs_trending = topics.get_trending_topics(theta, topics_title, titles)
        # print(trending_titles)
        # print(docs_trending)
        return trending_titles, docs_trending


    def run(self):
        utils.mkdir(self.root_output_dir)
        utils.mkdir(self.domain_output_dir)
        self.prepare_data()
        self.run_gibb_LDA()
        trending_titles, docs_trending = self.get_trending()
        return trending_titles, docs_trending


    def run_demo(self):
        print('get trending domain %s' % (self.domain))
        trending_titles, docs_trending = self.run()
        documents_content = demo.load_document_content(self.dataset)
        # build json content
        trending = []
        for k, title in trending_titles.items():
            event = {}
            event.update({u'title': u'topic ' + unicode(k) + u' - ' + title})
            # sub_title = []
            docs = docs_trending[k]
            sub_title = [{u'title': name} for name in docs]
            event.update({u'subTitles': sub_title})
            trending.append(event)
        self.save_trending(documents_content, json.dumps(trending, ensure_ascii=False, encoding='utf-8'))


    def save_trending(self, documents, trending_json):
        joblib.dump(documents, os.path.join(self.domain_output_dir, 'documents.pkl'), compress=True)
        joblib.dump(trending_json, os.path.join(self.domain_output_dir, 'trending_json.pkl'), compress=True)


    def load_trending(self):
        documents = joblib.load(os.path.join(self.domain_output_dir, 'documents.pkl'))
        trending_json = joblib.load(os.path.join(self.domain_output_dir, 'trending_json.pkl'))
        return documents, trending_json



if __name__ == '__main__':
    event = event_detection('CTXH', '../classification_result/Chinh tri Xa hoi', num_topics=50)
    event.run()
