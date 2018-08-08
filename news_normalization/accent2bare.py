# -*- coding: utf-8 -*-
__author__ = 'nobita'

import sys
from io import open

conv_dict = {u'a':u'a', u'á':u'a', u'à':u'a', u'ạ':u'a', u'ã':u'a', u'ả':u'a',
			u'ă':u'a', u'ắ':u'a', u'ằ':u'a', u'ặ':u'a', u'ẵ':u'a', u'ẳ':u'a',
			u'â':u'a', u'ấ':u'a', u'ầ':u'a', u'ậ':u'a', u'ẫ':u'a', u'ẩ':u'a',
			u'e':u'e', u'é':u'e', u'è':u'e', u'ẹ':u'e', u'ẽ':u'e', u'ẻ':u'e',
			u'ê':u'e', u'ế':u'e', u'ề':u'e', u'ệ':u'e', u'ễ':u'e', u'ể':u'e',
			u'i':u'i', u'í':u'i', u'ì':u'i', u'ị':u'i', u'ĩ':u'i', u'ỉ':u'i',
			u'o':u'o', u'ó':u'o', u'ò':u'o', u'ọ':u'o', u'õ':u'o', u'ỏ':u'o',
			u'ô':u'o', u'ố':u'o', u'ồ':u'o', u'ộ':u'o', u'ỗ':u'o', u'ổ':u'o',
			u'ơ':u'o', u'ớ':u'o', u'ờ':u'o', u'ợ':u'o', u'ỡ':u'o', u'ở':u'o',
			u'u':u'u', u'ú':u'u', u'ù':u'u', u'ụ':u'u', u'ũ':u'u', u'ủ':u'u',
			u'ư':u'u', u'ứ':u'u', u'ừ':u'u', u'ự':u'u', u'ữ':u'u', u'ử':u'u',
			u'y':u'y', u'ý':u'y', u'ỳ':u'y', u'ỵ':u'y', u'ỹ':u'y', u'ỷ':u'y',
			u'd':u'd', u'đ':u'đ'}


def accent2bare(str):
	s = u''
	for c in str.lower():
		try:
			s += conv_dict[c]
		except:
			s += c
	return s