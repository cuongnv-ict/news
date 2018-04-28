# -*- encoding: utf-8 -*-
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import warnings



class crawler:
    def __init__(self):
        self.ids = {}
        self.list_stories = []
        self.new_stories = []
        self.domain = 'http://baomoi.com'
        warnings.filterwarnings("ignore", category=UserWarning, module='bs4')


    def is_exist(self, doc_id):
        try:
            _ = self.ids[doc_id]
            return True
        except:
            self.ids.update({doc_id : True})
            return False


    def get_homepage(self):
        homepage = requests.get('https://baomoi.com/')
        return homepage.content


    def parser_hompage(self, homepage):
        bs = BeautifulSoup(homepage)
        list_stories = bs.find_all('div', {'class' : 'story__meta'})
        for story in list_stories:
            source = story.find_all('a', {'class' : 'cache', 'target' : '_blank'})
            self.parser_resultset(source)
            # get related stories
            relate = story.find_all('a', {'class' : 'relate'})
            for r in relate:
                href = r.attrs['href']
                self.parser_related(href)


    def parser_related(self, relate):
        r = requests.get(self.domain + relate).content
        bs = BeautifulSoup(r)
        list_related = bs.find_all('div', {'class' : 'story__meta'})
        for story in list_related:
            source = story.find_all('a', {'class' : 'cache', 'target' : '_blank'})
            self.parser_resultset(source)


    def parser_resultset(self, source):
        for s in source:
            href = s.attrs['href']
            doc_id = self.get_id(href)
            if '/c/' not in href or self.is_exist(doc_id):
                continue
            content = self.get_content(href)
            if content.strip() == u'':
                continue
            self.new_stories.append(content)
            self.list_stories.append(content)


    def get_id(self, href):
        name = os.path.basename(href)
        return os.path.splitext(name)[0]


    def get_content(self, href):
        url_href = self.domain + href
        source = requests.get(url_href).content
        bs = BeautifulSoup(source)
        content = self.get_content_baomoi(bs)
        return content


    def get_content_baomoi(self, bs):
        article = []
        title = bs.find_all('h1', {'class' : 'article__header'})
        article.append(u'\n'.join([t.text for t in title]).strip())
        print('title: %s' % (article[0]))
        description = bs.find_all('div', {'class' : 'article__sapo'})
        article.append(u'\n'.join([t.text for t in description]).strip())
        body = bs.find_all('p', {'class' : 'body-text'})
        article.append(u'\n'.join([t.text for t in body]).strip())
        return u'\n'.join(article)


    def remove_old_documents(self):
        del self.list_stories[:]
        del self.new_stories[:]
        self.ids.clear()


    def run(self):
        del self.new_stories[:]
        homepage = self.get_homepage()
        self.parser_hompage(homepage)
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('[%s] - There are %d new documents' % (date, len(self.new_stories)))



if __name__ == '__main__':
    c = crawler()
    c.run()