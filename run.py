# -*- encoding: utf-8 -*-

from flask import Flask, request, jsonify
from master import master
import json



m = master()



def build_json_trending(trending_titles, docs_trending):
    # build json content
    trending = []
    for k, title in trending_titles.items():
        event = {}
        docs = docs_trending[k]
        event.update({u'title' : title, u'ndocs' : u'%d' % (len(docs))})
        # sub_title = []
        sub_title = [{u'title' : name} for name in docs]
        event.update({u'subTitles' : sub_title})
        trending.append(event)
    return trending


def parser_json_data(stories):
    list_stories = json.loads(stories)
    return [obj['content'] for obj in list_stories]


app = Flask(__name__, static_url_path='',
            static_folder='static',
            template_folder='templates')


@app.route('/get_trending', methods = ['POST'])
def get_content():
    stories = request.form['stories']
    stories = parser_json_data(stories)
    trending_titles, docs_trending = m.run(stories)
    result = []
    for domain in trending_titles.keys():
        json_content = {}
        json_content.update({u'domain': domain, u'id': domain.replace(u' ', u'-').lower()})
        trending_domain = build_json_trending(trending_titles[domain], docs_trending[domain])
        json_content.update({u'content': trending_domain})
        result.append(json_content)
    # result = json.dumps(result, ensure_ascii=False, encoding='utf-8')
    return jsonify(result)




if __name__ == '__main__':
    app.run('0.0.0.0', port=11110)