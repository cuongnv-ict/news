import numpy as np
import re
class Feature:

    NONE_SPLITER_OFFSET = 100
    NEXT_LOCAL_STEP = 15
    MAX_NAME_LENGTH = 15

    def __init__(self):
        self.NONE_SPLITER_DICT = dict()
        self.is_name_re = re.compile("[A-Z]{1,2}\.")
        self.NONE_SPILTER_REGEXES = []
        self.HARD_RULES_REGEXES = []
        self.FORCE_SPLITER_REGREXES = []

    def add_none_spliter_regrex(self,sregex,is_hard=False):
        if is_hard == False:
            self.NONE_SPILTER_REGEXES.append(re.compile(sregex,re.UNICODE))
        else:
            self.HARD_RULES_REGEXES.append(re.compile(sregex,re.UNICODE))
    def add_forcing_splitter_regrex(self,sregex):
        self.FORCE_SPLITER_REGREXES.append(re.compile(sregex,re.UNICODE))

    def is_match_regex_rules(self,word):
        for reg in self.NONE_SPILTER_REGEXES:
            ss = reg.search(word)
            if ss != None:
                return 100

        return 0

    def is_match_hard_rules(self,word):
        for reg in self.FORCE_SPLITER_REGREXES:
            ss = reg.search(word)
            if ss != None:
                return -1

        for reg in self.HARD_RULES_REGEXES:
            ss = reg.search(word)
            if ss != None:
                return 1

        return 0

    def gen_feature_vector(self,sent,current_id,is_forced=False,is_none=False):
        next_word = Feature.get_next_word(sent,current_id)
        previous_word = Feature.get_previous_word(sent,current_id)

        features = []
        local_word,long_name_local_word = Feature.get_local_word(sent,current_id,previous_word,next_word)
        # print local_word,"_",long_name_local_word

        is_regex = self.is_match_regex_rules(local_word)
        is_hard_rule = self.is_match_hard_rules(local_word)
        if is_hard_rule == 0 and not long_name_local_word == None:
            is_hard_rule = self.is_match_hard_rules(long_name_local_word)

        # print "Hard rule: ",is_hard_rule

        features.append(is_regex)
        pre_plus  = 0
        next_plus = 0
        if is_regex != 0:
            pre_plus = 100
            next_plus = 0

        features.append(Feature.is_ending_char(sent,current_id))
        features.append(Feature.is_next_new_line_char(sent,current_id))
        features.append(Feature.is_space_next_char(sent,current_id))
        features.append(Feature.is_none_space_previous_char(sent,current_id))
        features.append(Feature.is_title_at_next_word(sent,current_id,next_word))
        features.append(Feature.is_none_title_at_previous_word(sent,current_id,previous_word))

        features.append(self.get_none_spliter_next_word(sent,current_id,next_word,is_forced,next_plus))
        features.append(self.get_none_spliter_previous_word(sent,current_id,previous_word,is_forced,pre_plus))
        features.append(Feature.is_digit(next_word))
        features.append(Feature.is_digit(previous_word))
        features.append(Feature.is_end_3_dot(sent,current_id))
        features.append(len(next_word))
        features.append(len(previous_word))
        features.append(Feature.if_contain_dot(next_word))
        features.append(self.is_name_style(previous_word+"."))
        features.append(self.is_name_style(next_word))
        features.append(Feature.is_next_local_contain_seperator(sent, current_id))

        features.append(Feature.if_close_pre_contains_dot(sent,current_id))
        #return np.array(features,dtype=float)
        return features,is_hard_rule

    @staticmethod
    def get_local_word(sent,current_id,pre,next):
        long_pre_local = None
        local_word = None

        if current_id == len(sent)-1:
            return pre+sent[current_id],long_pre_local
        s = ""
        if sent[current_id+1] == " ":
            s = " "
        # Get long pre local: Jose J. S
        if len(pre) <= 2 and pre.istitle():
            pre_id = current_id - len(pre)
            for offset in xrange(2,Feature.MAX_NAME_LENGTH):
                sep_id = pre_id-offset
                if sep_id >= 0:
                    if sent[sep_id] == " " or sep_id==0:
                        long_pre_local = sent[sep_id:current_id]+sent[current_id]+s+next
                        break


        local_word = pre+sent[current_id]+s+next
        return local_word,long_pre_local


    @staticmethod
    def if_close_pre_contains_dot(sent,current_id):
        if current_id < 3:
            return 10
        for c in sent[current_id-3:current_id]:
            if c == "." or c == "\n":
                return 10
        return 0
    @staticmethod
    def if_contain_dot(word):
        if word.__contains__("."):
            return 1
        return 0

    @staticmethod
    def is_next_local_contain_seperator(sent, current_id):
        for i in xrange(current_id+1,current_id + Feature.NEXT_LOCAL_STEP):
            if i >= len(sent)-1:
                break
            if sent[i]==","  or sent[i] == "." or sent[i]=="-":
                return 1
        return 0
    @staticmethod
    def is_before_local_contain_colon(sent,current_id):
        pass

    def is_name_style(self,word):
        X = self.is_name_re.search(word)
        if X == None:
            return 0
        return 1


    @staticmethod
    def is_spliter_candidate(char):
        return char == "." or char =="?" or char == "!" or char=="\n" or char == "\r"
    @staticmethod
    def is_end_3_dot(sen,current_id):
        if(current_id>1):
            if sen[current_id-2:current_id+1] == "...":
                return 1
        return 0

    @staticmethod
    def get_next_word(sent, current_id):
        start_id = current_id
        if start_id < len(sent)-1 and sent[start_id + 1] == " ":
            start_id += 1

        try:
            next_space_id = sent.index(" ", start_id + 1)
        except:
            next_space_id = len(sent)

        if next_space_id != 0:
            next_word = sent[start_id + 1: next_space_id]
        else:
            next_word = ""
        return next_word




    @staticmethod
    def get_previous_word(sent, current_id):
        idx = current_id - 1
        while idx >= 0:
            if sent[idx] == " ":
                break
            idx -= 1

        previous_word = sent[idx + 1: current_id]
        return previous_word

    @staticmethod
    def is_digit(word):
        if word.isdigit():
            return 1
        return 0


    @staticmethod
    def is_ending_char(sent,current_id):
        if current_id == len(sent) - 1:
            return 1
        return 0

    @staticmethod
    def is_next_new_line_char(sent,current_id):
        if current_id < len(sent) - 1:
            next_id = current_id + 1
            if sent[next_id] == "\n" or sent[next_id] == "\r":
                return 1
        return 0

    @staticmethod
    def is_space_next_char(sent,current_id):
        if current_id < len(sent) - 1:
            if sent[current_id + 1] == " ":
                return 1
        return 0

    @staticmethod
    def is_none_space_previous_char(sent,current_id):
        if current_id > 0:
            if sent[current_id-1] != " ":
                return 1

        return 0



    @staticmethod
    def is_title_at_next_word(sent,current_id,next_word=None):
        if next_word == None:
            next_word  = Feature.get_next_word(sent,current_id)
        if next_word.istitle():
            return 1
        return 0

    @staticmethod
    def is_none_title_at_previous_word(sent,current_id,previous_word=None):
        if previous_word == None:
            previous_word = Feature.get_previous_word(sent,current_id)
        if not previous_word.istitle():
            return 1
        return 0

    def force_getting_none_slitter_wordid(self,word):
        try:
            word_id = self.NONE_SPLITER_DICT[word]
        except:
            word_id = len(self.NONE_SPLITER_DICT) + self.NONE_SPLITER_OFFSET
            self.NONE_SPLITER_DICT[word] = word_id
        return word_id

    def get_only_none_slitter_wordid(self,word):
        try:
            word_id = self.NONE_SPLITER_DICT[word]
        except:
            word_id = -1
        return word_id

    def get_none_spliter_next_word(self,sent,current_id,next_word=None,is_forced=False,is_regex=0):

        if next_word == None:
            next_word = Feature.get_next_word(sent,current_id)
        if is_forced == False:
            return self.get_only_none_slitter_wordid(next_word) + is_regex
        return self.force_getting_none_slitter_wordid(next_word) + is_regex

    def get_none_spliter_previous_word(self,sent,current_id,previous_word=None,is_forced=False,is_regex=0):
        if previous_word == None:
            previous_word = Feature.get_previous_word(sent,current_id)
        if is_forced == False:
            return self.get_only_none_slitter_wordid(previous_word) + is_regex
        return self.force_getting_none_slitter_wordid(previous_word) + is_regex




