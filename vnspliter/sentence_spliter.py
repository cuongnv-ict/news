# -*- coding: utf-8 -*-

import os.path
import re
from io import open

from sklearn.linear_model import LogisticRegression

import loading_data
import utils
from feature.feature import Feature


class SentenceSpliter():
    def __init__(self,path="models/model.dump",is_training=False,new_rule_path=None):
        self.classifier = None
        self.feature_model = None
        self.multi_newline_regex = re.compile("\n+")
        self.c_dir = os.path.abspath(os.path.dirname(__file__))
        self.model_path = "%s/%s"%(self.c_dir,path)
        if not is_training:
            if os.path.exists(self.model_path) and not is_training:
                #print "Loading model..."
                model = utils.pickle_load(self.model_path)
                self.classifier = model.classifier
                self.feature_model = model.feature_model
                if new_rule_path != None:
                    self.load_custom_hard_rule(new_rule_path)
            else:
                print "Unalbe to load the spliter model. %s"%path
                exit(-1)



    def load_normal_data(self,feature_list,label_list,sen_list=None):
        sens = loading_data.load_sentence()
        num_sen = len(sens)
        print "Loading total %s normal sentence."%num_sen
        for i in xrange(num_sen-1):
            sen = sens[i]
            spliter_id = len(sen) - 1

            #for single sentence
            feature,_ = self.feature_model.gen_feature_vector(sen,spliter_id)
            feature_list.append(feature)
            label_list.append(1)
            if sen_list != None:
                sen_list.append(sen)

            #for merge sentence
            sen_merge = " ".join([sens[i],sens[i+1]])
            feature,_ = self.feature_model.gen_feature_vector(sen_merge,spliter_id)
            feature_list.append(feature)
            label_list.append(1)
            if sen_list!=None:
                sen_list.append(sen)
            idx = 0
            for c in sen[:-1]:
                if Feature.is_spliter_candidate(c):
                    feature,_ = self.feature_model.gen_feature_vector(sen,idx)
                    feature_list.append(feature)
                    label_list.append(0)
                    if sen_list != None:
                        sen_list.append(sen)
                idx += 1


    def load_custom_hard_rule(self,path):
        rules = loading_data.load_spliter_rules(path)
        for rule in rules:
            if rule[0]=="#":
                continue
            elif rule[0]=="h":
                rule = rule[1:]
                print "Add a hard rule regex: %s" % rule
                self.feature_model.add_none_spliter_regrex(rule,True)
                continue


    def loading_forcing_spliter_rule(self):
        rules = loading_data.load_spliter_rules(loading_data.raw_forcing_spliter_path)
        for rule in rules:
            if rule[0] == "#":
                continue
            elif rule[0] == "h":
                rule = rule[1:]
                print "Add a hard forcing rule regex: %s" % rule
                self.feature_model.add_forcing_splitter_regrex(rule)

    def loading_none_spliter_rule(self,feature_list,label_list,sen_list=None):
        rules = loading_data.load_spliter_rules()
        print "Loading rules."
        for rule in rules:
            if rule[0]=="#":
                continue
            if rule[0]=="r":
                rule = rule[1:]
                print "Add a soft regex: %s"%rule
                self.feature_model.add_none_spliter_regrex(rule)
                continue
            elif rule[0]=="h":
                rule = rule[1:]
                print "Add a hard rule regex: %s" % rule
                self.feature_model.add_none_spliter_regrex(rule,True)
                continue

            idx = 0
            for c in rule:
                if Feature.is_spliter_candidate(c):
                    feature,_= self.feature_model.gen_feature_vector(rule,idx,is_forced=True)
                    feature_list.append(feature)
                    label_list.append(0)
                    if sen_list != None:
                        sen_list.append(rule)
                idx += 1
        #print Feature.NONE_SPLITER_DICT


    def train(self):
        self.feature_model = Feature()
        feature_list = []
        label_list = []
        sen_list = []
        self.loading_none_spliter_rule(feature_list,label_list,sen_list)
        self.loading_forcing_spliter_rule()
        self.load_normal_data(feature_list,label_list,sen_list)
        self.classifier = LogisticRegression(verbose=False)
        print "Learning..."
        self.classifier.fit(feature_list,label_list)
        print "Saving..."
        utils.pickle_save(self, self.model_path)
        print "Done"
        print "Test..."
        #f = open("wrong.dat","w")
        predicted_labels = self.classifier.predict(feature_list)
        ll = len(predicted_labels)
        cc = 0
        for i in xrange(ll):
            if label_list[i] == 0 and predicted_labels[i]==1:
                cc += 1
                #print sen_list[i]
                #f.write("%s\ndocs"%sen_list[i])
        #f.close()
        print cc,ll,cc*1.0/ll
    def __split_par(self, par, is_debug=False):
        list_sens = []

        list_features = []
        list_candidates = []
        list_hard_rule_none_spliter_idx = []
        list_hard_rule_forcing_spliter_idx = []
        idx = 0
        for c in par:
            if Feature.is_spliter_candidate(c):
                list_candidates.append(idx)
                feature,is_hard = self.feature_model.gen_feature_vector(par, idx)
                if is_hard > 0:
                    list_hard_rule_none_spliter_idx.append(len(list_candidates)-1)
                elif is_hard < 0:
                    list_hard_rule_forcing_spliter_idx.append(len(list_candidates)-1)
                if is_debug:
                    print feature
                list_features.append(feature)
            idx += 1
        if is_debug:
            print list_candidates

        if len(list_candidates) ==0:
            list_sens.append(par)
            return list_sens

        #print list_features
        #list_features = np.array(list_features)
        #print "Shape: ",list_features.shape



        labels = self.classifier.predict(list_features)

        for l in list_hard_rule_none_spliter_idx:
            labels[l] = 0
        for l in list_hard_rule_forcing_spliter_idx:
            labels[l] = 1

        list_true_spliters = [-1]
        for i in xrange(len(labels)):
            if labels[i] == 1:
                list_true_spliters.append(list_candidates[i])

        if list_candidates[-1] != len(par) - 1:
            list_true_spliters.append(len(par)-1)

        if is_debug:
            print list_true_spliters
        if len(list_true_spliters) > 1:
            for i in xrange(len(list_true_spliters) - 1):
                list_sens.append(par[list_true_spliters[i] + 1:list_true_spliters[i + 1] + 1].strip())

        else:
            list_sens.append(par)

        return list_sens

    def split(self,doc,is_debug=False):
        doc = doc.replace("\r","")
        doc = self.multi_newline_regex.sub("\n",doc)
        paragraphs = doc.split("\n")
        sens = []
        for par in paragraphs:
            if len(par)<1:
                continue
            par_sens = self.__split_par(par, is_debug)
            for sen in par_sens:
                sens.append(sen)

        return sens


def train():
    sentence_spliter = SentenceSpliter(is_training=True)
    sentence_spliter.train()
    print sentence_spliter.feature_model.NONE_SPLITER_DICT


def demo_cml():
    sentence_spliter = SentenceSpliter(path="models/model.dump")
    while True:
        par = raw_input("Enter paragraph: ")
        try:
            par = unicode(par)
        except:
            par = unicode(par, encoding="UTF-8")
        print "\nParagraph: ",par
        if len(par) <2:
            continue
        print "--------------------------------"
        print "Result:"
        list_sens= sentence_spliter.split(par, True)
        for sen in list_sens:
            print sen
        #sentence_spliter.feature_model.gen_ve


def demo_file():
    sentence_spliter = SentenceSpliter()
    while True:
        cmd = raw_input("Cmd 1 = Cont 0 = Quit:")
        if len(cmd) < 1:
            continue

        f = open("input.dat",encoding="UTF-8")
        file = "\n".join(f.readlines())
        f.close()
        list_sens = sentence_spliter.split(file, True)
        f = open("output.dat","w",encoding="UTF-8")
        for sen in list_sens:
            print sen
            f.write("%s\n"%sen)
        f.close()

if __name__=="__main__":
   #train()
   demo_file()
   #demo_cml()



