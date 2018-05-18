# -*- encoding: utf-8 -*-

from flask import Flask, request
from flask import jsonify
from event_detection import demo
from master import master
from threading import Thread
from sklearn.externals import joblib




m = master()
handle = Thread(target=m.run)
handle.start()



def build_trending_domain(trending_titles, docs_trending):
    # build json content
    trending = []
    for k, title in trending_titles.items():
        event = {}
        docs = docs_trending[k]
        event.update({u'title': title.split(u' == ')[1] + u' - %d docs' % (len(docs))})
        # sub_title = []
        sub_title = [{u'title': name.split(u' == ')[1]} for name in docs]
        event.update({u'subTitles': sub_title})
        trending.append(event)
    return trending


app = Flask(__name__, static_url_path='',
            static_folder='static',
            template_folder='templates')


# prevent cached responses
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/', methods = ['GET'])
def homepage():
    return app.send_static_file('event.html')


@app.route('/update', methods = ['GET', 'POST'])
def update():
    trending_titles = joblib.load(m.trending_titles_file)
    docs_trending = joblib.load(m.docs_trending_file)
    result = []
    for domain in trending_titles.keys():
        json_content = {}
        json_content.update({u'domain' : domain, u'id' : domain.replace(u' ', u'-').lower()})
        trending_domain = build_trending_domain(trending_titles[domain], docs_trending[domain])
        json_content.update({u'content' : trending_domain})
        result.append(json_content)
    #result = json.dumps(result, ensure_ascii=False, encoding='utf-8')
    return jsonify(result)


@app.route('/get', methods = ['GET', 'POST'])
def get_content():
    return {}
    title = request.form['title']
    demo.load_document_content(dataset, documents_content)
    content = demo.get_document_by_title(title, documents_content)
    return jsonify(content)




if __name__ == '__main__':
    app.run('0.0.0.0', port=11113)