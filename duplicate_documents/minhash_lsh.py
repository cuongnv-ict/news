# -*- encoding: utf-8 -*-

import os
from document import document
from datasketch import MinHashLSH
import config, utils
from sklearn.externals import joblib
import unicodedata
import sys



class duplicate_docs:
    def __init__(self):
        self.docs = {}
        self.docs_time = {}
        self.lsh = MinHashLSH(num_perm=config.LSH_CONFIG['num_permutation'],
                              params=(config.LSH_CONFIG['b'], config.LSH_CONFIG['r']))


    def load(self, model):
        print('loading %s ...' % (model))
        if os.path.isfile(model):
            return joblib.load(model)
        else:
            return None


    def save(self, model, path):
        print('saving %s ...' % (path))
        joblib.dump(model, path)
        return


    # load data from list documents
    def run(self, list_titles, list_docs, list_categories):
        total_files = len(list_docs)
        clean_docs = []
        clean_titles = []
        duplicate_categories = {}
        for i in xrange(len(list_docs)):
            raw_doc = list_docs[i]
            data = unicodedata.normalize('NFKC', raw_doc.strip())
            doc = document(data)
            did = self.insert(doc, check_duplication=True)
            if did == None:
                contentId = list_titles[i].split(u' == ')[0]
                duplicate_categories.update({contentId : list_categories[i]})
            else:
                clean_docs.append(raw_doc)
                clean_titles.append(list_titles[i])
            print ('\r%d -- %s' % (total_files, did)),
            sys.stdout.flush()
        print('')
        print ('total files = %d' % (total_files))
        print ('number of duplicate document = %d' % (len(duplicate_categories)))
        return clean_titles, clean_docs, duplicate_categories


    def run_ex(self, list_docs):
        # total_files = len(list_docs)
        clean_docs = []
        nduplicate = 0
        for i in xrange(len(list_docs)):
            raw_doc = list_docs[i]
            data = unicodedata.normalize('NFKC', raw_doc.strip())
            doc = document(data)
            did = self.insert(doc, check_duplication=True)
            if did == None:
                nduplicate += 1
            else:
                clean_docs.append(raw_doc)
            # print ('\r%d -- %s' % (total_files, did)),
            # sys.stdout.flush()
        # print('')
        # print ('total files = %d' % (total_files))
        # print ('number of duplicate document = %d' % (nduplicate))
        return clean_docs


    # insert a document object
    # output: key if document does not exist duplicate item
    # otherwise return alert duplication.
    def insert(self, doc, check_duplication=True):
        key = utils.id_generator()
        minhash = doc.get_minhash(doc.k_shingles,
                                  config.MINHASH_CONFIG['num_permutation'])
        if len(doc.k_shingles) == 0:
            return u'Does not insert this document to database.\nDocument\'s shingle = 0.\nDocument need to contain at least %d word' \
                   % (config.SHINGLE_CONFIG['k'])
        now = utils.get_date_now()
        if check_duplication:
            if not self.is_duplicate(doc.k_shingles, minhash): # not duplicate
                self.lsh.insert(key, minhash)
                self.docs.update({key : doc})
                try:
                    self.docs_time[now].append(key)
                except:
                    self.docs_time.update({now : [key]})
                return key
            else:
                return None
        else:
            self.lsh.insert(key, minhash)
            self.docs.update({key: doc})
            try:
                self.docs_time[now].append(key)
            except:
                self.docs_time.update({now: [key]})
            return key


    # remove document by key
    def remove(self, key):
        try:
            del self.docs[key]
            self.lsh.remove(key)
            return u'Have deleted document has key is %s.' % (key)
        except Exception as e:
            # print e.message
            return u'The given key %s does not exist in database' % (key)


    # remove all docs
    def clear(self, time=None):
        docs_id = self.docs.keys()
        for id in docs_id:
            self.remove(id)
        if time is None:
            time = utils.get_date_now()
        times = self.docs_time.keys()
        for t in times:
            diff = time - t
            if diff.days >= config.TIME_TO_DELETE:
                del self.docs_time[t]


    # check duplication
    # input: shingles and minhash of document
    def is_duplicate(self, shingles, minhash):
        result = self.lsh.query(minhash)
        if len(result) == 0:
            return False
        for key in result:
            jaccard = self.get_actual_jaccard(shingles, self.docs[key].k_shingles)
            if jaccard > config.LSH_CONFIG['similarity_threshold']:
                return True
        return False


    def get_actual_jaccard(self, shingles1, shingles2):
        union = float(len(shingles1.union(shingles2)))
        if union == 0.0:
            return 0.0
        intersection = float(len(shingles1.intersection(shingles2)))
        return intersection / union


    # remove docs is older than (x + 30) days
    def remove_old_doc(self, days=2):
        for day in xrange(days + 30):
            previous_date = utils.get_previous_date(days)
            try:
                docs_id = self.docs_time[previous_date]
                for id in docs_id:
                    try:
                        self.remove(id)
                    except:
                        continue
                del self.docs_time[previous_date]
            except: continue


    def load_model(self):
        self.lsh = self.load('model/lsh.pkl')
        self.docs = self.load('model/docs.pkl')
        self.docs_time = self.load('model/docs_time.pkl')
        if self.lsh != None and self.docs != None and self.docs_time != None:
            return True
        return False


    def save_model(self):
        utils.mkdir('model')
        self.save(self.lsh, 'model/lsh.pkl')
        self.save(self.docs, 'model/docs.pkl')
        self.save(self.docs_time, 'model/docs_time.pkl')
