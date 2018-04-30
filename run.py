# -*- encoding: utf-8 -*-

from flask import Flask, request
from flask import jsonify
from event_detection import demo
from text_classification import my_map
from master import master
from threading import Thread
import os, json, time



m = master()
handle = Thread(target=m.run)
handle.start()

domain = 'Chinh tri Xa hoi'
domain_label = my_map.name2label[domain]
dataset = os.path.join(m.text_clf.result_dir, domain)

while True:
    try:
        trending_titles = m.trending_titles[domain]
        docs_trending = m.docs_trending[domain]
        break
    except:
        time.sleep(1)

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

documents_content = demo.load_document_content(dataset)


app = Flask(__name__, static_url_path='',
            static_folder='static',
            template_folder='templates')

@app.route('/', methods = ['GET'])
def homepage():
    return app.send_static_file('event.html')


@app.route('/update', methods = ['GET', 'POST'])
def update():
    return jsonify(trending_titles)


@app.route('/get', methods = ['GET', 'POST'])
def get_content():
    title = request.form['title']
    content = demo.get_document_by_title(title, docs_trending)
    return jsonify(content)




if __name__ == '__main__':
    app.run('0.0.0.0', port=11111)