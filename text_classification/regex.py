# -*- encoding: utf-8 -*-
__author__ = 'nobita'

import re
import utils


class regex:
    def __init__(self):
        self.rm_except_chars = re.compile(u'[^\w\s\d…\-–\./_,\(\)$%“”\"\'?!;:@#^&*\+=<>\[\]\{\}²³áÁàÀãÃảẢạẠăĂắẮằẰẳẲặẶẵẴâÂấẤầẦẩẨậẬẫẪđĐéÉèÈẻẺẽẼẹẸêÊếẾềỀễỄểỂệỆíÍìÌỉỈĩĨịỊóÓòÒỏỎõÕọỌôÔốỐồỒổỔỗỖộỘơƠớỚờỜởỞỡỠợỢúÚùÙủỦũŨụỤưƯứỨừỪửỬữỮựỰýÝỳỲỷỶỹỸỵỴ]')
        self.normalize_space = re.compile(u' +')
        self.detect_url = re.compile(u'(https|http|ftp|ssh)://[^\s\[\]\(\)\{\}]+', re.I)
        self.detect_num = re.compile(ur'(\d+\,\d+\w*)|(\d+\.\d+\w*)|(\w*\d+\w*)')
        self.detect_email = re.compile(u'[^@|\s]+@[^@|\s]+')
        self.detect_datetime = re.compile(u'\d+[\-/]\d+[\-/]*\d*')
        self.change_to_space = re.compile(u'\t')
        self.normalize_special_mark = re.compile(u'(?P<special_mark>[\.,\(\)\[\]\{\};!?:“”\"\'/\<\>$%–@#^&*+=])')
        self.detect_special_mark = re.compile(u'[\(\)\[\]\{\}\<\>“”\"\']')
        self.detect_special_mark2 = re.compile(u'[\.;!?:,]')
        self.detect_special_mark3 = re.compile(u'[/\-$%–@#^&*+=]')
        # detect non-vietnamese words
        self.detect_non_vnese = self.detect_non_vietnamese()


    def run(self, data):
        s = self.detect_num.sub(u'1', data) # replaced number to 1
        s = self.detect_url.sub(u'2', s)
        s = self.detect_email.sub(u'3', s)
        s = self.detect_datetime.sub(u'4', s)
        s = self.change_to_space.sub(u' ', s)
        s = self.rm_except_chars.sub(u'', s)
        # s = self.detect_non_vnese.sub(u'5', s)
        s = self.normalize_special_mark.sub(u' \g<special_mark> ', s)
        s = self.detect_special_mark.sub(u'6', s)
        s = self.detect_special_mark2.sub(u'7', s)
        # s = self.detect_special_mark3.sub(u'8', s)
        s = self.normalize_space.sub(u' ', s)
        return s.strip()


    def detect_non_vietnamese(self):
        vowel = [u'a', u'e', u'i', u'o', u'u', u'y']
        vowel2 = [u'a', u'e', u'i', u'o', u'y']
        vowel3 = [u'y']
        double_vowel = [w+w for w in vowel]
        double_vowel = list(set(double_vowel)-set([u'uu']))
        double_vowel2 = utils.add_to_list(vowel3, vowel)
        double_vowel2 = list(set(double_vowel2)-set([u'yy']))
        consonant = [u'b', u'label', u'd', u'g', u'h', u'k', u'l', u'm', u'ndocs', u'p', u'q',
                     u'r', u's', u't', u'v', u'x']
        consonant2 = [u'b', u'd', u'g',  u'h',  u'k', u'l', u'q', u'r',  u's', u'v', u'x']
        consotant3 = [u'm',  u'p']
        consonant4 = [u'p', u'q']
        consonant5 = [u'b', u'label', u'd', u'g', u'ndocs', u'r']
        special_pattern = [u'ch', u'gh', u'kh', u'nh', u'ng', u'ph', u'th', u'tr']
        special_pattern2 = [u'ae', u'ea', u'ei', u'ey', u'iy', u'oy', u'ya', u'yi', u'yo', u'yu']
        special_pattern3 = [u'gh', u'kh', u'ph', u'th', u'tr']
        special_pattern4 = [u'ge', u'gy', u'ka', u'ko', u'ku', u'ry']
        english_chars = [u'f', u'j', u'w', u'z']
        double_consonant = utils.add_to_list(consonant, consonant)
        double_consonant = list(set(double_consonant) - set(special_pattern))
        non_vietnamese = double_vowel + double_consonant + utils.add_to_list(vowel, consonant2)
        non_vietnamese += consotant3 + special_pattern2 + utils.add_to_list(vowel, special_pattern3)
        non_vietnamese += utils.add_to_list(vowel, utils.add_to_list(consonant, vowel))
        non_vietnamese += special_pattern4 + utils.add_to_list(consonant4, vowel2) + \
                          utils.add_to_list(consonant, double_vowel2) + utils.add_to_list(consonant5, vowel3)
        non_vietnamese = self.filter_non_vnese(set(non_vietnamese)) + english_chars
        s = u'|'.join(non_vietnamese)
        return re.compile(ur'\w*(' + s + ur')\w*', re.I)

    def filter_non_vnese(self, s):
        two = filter(lambda x: len(x) == 2, s)
        three = list(set(s) - set(two))
        new_three = []
        for x1 in three:
            flag = False
            if len(x1) != 3: continue
            for x2 in two:
                if x2 in x1:
                    flag = True;
                    break
            if not flag: new_three.append(x1)
        return two + new_three


if __name__ == '__main__':
    r = regex()
    s = u'bền k56k năm'
    ss = r.detect_num.sub(u'1', s)
    print ss