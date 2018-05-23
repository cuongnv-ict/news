# -*- encoding: utf-8 -*-

import utils
import os
import my_map
import preprocessing
from sklearn.externals import joblib
from io import open



class classification:
    def __init__(self, root_dir='.'):
        self.model = None
        self.vectorizer = None
        self.root_dir = root_dir
        self.result_dir = os.path.join(self.root_dir, 'result')


    def load(self, model):
        print('loading %s ...' % (model))
        if os.path.isfile(model):
            return joblib.load(model)
        else:
            return None


    def load_model(self):
        self.vectorizer = self.load('text_classification/model/vectorizer.pkl')
        self.model = self.load('text_classification/model/model.pkl')


    def feature_extraction(self, X):
        return self.vectorizer.transform(X)


    def run(self):
        self.load_model()
        assert self.model != None and self.vectorizer != None, \
            'don\'t find text classification model'


    def predict(self, list_document):
        docs = preprocessing.load_dataset_ex(list_document)
        X = self.feature_extraction(docs)
        return self.model.predict(X)


    def save_to_dir(self, list_document, labels):
        utils.mkdir(self.result_dir)
        _ = map(lambda x: utils.mkdir(os.path.join(self.result_dir, x)), my_map.domain2label.keys())
        for i in xrange(len(labels)):
            output_dir = os.path.join(self.result_dir, my_map.label2domain[labels[i]])
            with open(os.path.join(output_dir, utils.id_generator()), 'w', encoding='utf-8') as fw:
                fw.write(unicode(list_document[i]))


    def clear(self):
        utils.delete_dir(self.result_dir)




if __name__ == '__main__':
    c = classification()
    c.run()