# -*- encoding: utf-8 -*-
import preprocessing
import create_lda_data as lda
import subprocess
import topics
import utils
import os
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
        self.title_map_file = os.path.join(self.title_dir, 'title_map_file.pkl')
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
        joblib.dump(title_map, self.title_map_file, compress=True)


    def prepare_data(self):
        # prepare LDA dataset
        title_map = self.load_title_map()
        if title_map == None:
            title_map = {}
        lda.update_title_map(self.dataset, title_map)
        preprocessing.remove_stop_postag(self.dataset, self.clean_dataset_dir)
        contents, titles = lda.build_vocab(self.clean_dataset_dir, self.vocab_file,
                                           self.root_dir, title_map)
        print('There are %s docs in domain %s' % (len(contents), self.domain))
        vocab = lda.load_vocab(self.vocab_file)
        lda.get_lda_data(contents, vocab, self.lda_dataset_dir, self.lda_train_file)
        lda.save_titles_to_file(titles, self.title_dir, self.title_file)
        self.save_title_map(title_map)


    def reset_all(self):
        utils.delete_dir(self.domain_output_dir)


    def run_gibb_LDA(self):
        # run LDA
        command = [self.lda_bin_file, '--directory', self.lda_output_dir,
                   '--train_data', self.lda_train_file,
                   '--num_topics', str(self.num_topics), '--save_lag', '10000',
                   '--eta', '0.01', '--alpha', '0.1', '--max_iter', str(self.max_iter)]
        subprocess.call(command)


    def get_trending(self):
        # print topics and get trending topics
        theta, topics_title, titles = topics.get_topics_title(
            self.lda_theta_file,
            self.title_file)
        utils.mkdir(self.topic_result_dir)
        topics.print_topics(self.lda_beta_file, topics_title,
                            self.vocab_file, 20, self.topic_result_file)
        trending_titles, docs_trending = topics.get_trending_topics(theta, topics_title, titles)
        return trending_titles, docs_trending


    def run(self, save2file=False):
        utils.mkdir(self.root_output_dir)
        utils.mkdir(self.domain_output_dir)
        self.prepare_data()
        self.run_gibb_LDA()
        trending_titles, docs_trending = self.get_trending()
        if save2file:
            self.save_trending(trending_titles, docs_trending)
        return trending_titles, docs_trending


    def save_trending(self, trending_titles, docs_trending):
        joblib.dump(trending_titles, self.trending_titles_file, compress=True)
        joblib.dump(docs_trending, self.docs_trending_file, compress=True)


    def load_trending(self):
        trending_titles = joblib.load(self.trending_titles_file)
        docs_trending = joblib.load(self.docs_trending_file)
        return trending_titles, docs_trending



if __name__ == '__main__':
    event = event_detection('CTXH', '../classification_result/Chinh tri Xa hoi', num_topics=50)
    event.run()
