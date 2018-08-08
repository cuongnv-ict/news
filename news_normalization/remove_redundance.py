# -*- encoding: utf-8 -*-

import unicodedata


# http://www.bongda.com.vn/goc-nhin-premier-league-tai-sao-cac-doi-bong-nho-muon-choi-lon-d456880.html
def normalize_ending_mark(content):
    return content.replace(u'./.', u'.')


def is_image_caption(str):
    lower = str.lower()
    if u'ảnh : ' in lower or u'nguồn : ' in  lower:
        return True
    return False


def normalize(content):
    content = unicodedata.normalize('NFKC', content)