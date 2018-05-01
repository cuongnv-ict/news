# -*- encoding: utf-8 -*-

from flask import Flask, request
from flask import jsonify
from event_detection import demo
from master import master
from threading import Thread
import os, json, time
from sklearn.externals import joblib




m = master()
handle = Thread(target=m.run)
handle.start()

domain = 'The thao'
dataset = os.path.join(m.text_clf.result_dir, domain)
documents_content = {}

# wait for master finish in the first running.
while True:
    try:
        _ = m.trending_titles[domain]
        break
    except:
        time.sleep(1)


def build_json_content(trending_titles, docs_trending):
    # build json content
    trending = []
    for k, title in trending_titles.items():
        event = {}
        event.update({u'title': u'topic ' + unicode(k) + u' - ' + title})
        # sub_title = []
        docs = docs_trending[k]
        sub_title = [{u'title': name} for name in docs]
        event.update({u'subTitles': sub_title})
        trending.append(event)
    trending_json = json.dumps(trending, ensure_ascii=False, encoding='utf-8')
    return trending_json


app = Flask(__name__, static_url_path='',
            static_folder='static',
            template_folder='templates')


@app.route('/', methods = ['GET'])
def homepage():
    return app.send_static_file('event.html')


@app.route('/update', methods = ['GET', 'POST'])
def update():
    trending_titles = joblib.load(m.trending_titles_file)
    docs_trending = joblib.load(m.docs_trending_file)
    trending_json = build_json_content(trending_titles[domain], docs_trending[domain])
    return jsonify(trending_json)


@app.route('/get', methods = ['GET', 'POST'])
def get_content():
    title = request.form['title']
    demo.load_document_content(dataset, documents_content)
    content = demo.get_document_by_title(title, documents_content)
    return jsonify(content)




if __name__ == '__main__':
    app.run('0.0.0.0', port=11111)