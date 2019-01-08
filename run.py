# -*- encoding: utf-8 -*-

from flask import Flask, request
from flask import jsonify
from event_detection import demo
from master import master
from multiprocessing import Process
from sklearn.externals import joblib


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
			u'd':u'd', u'đ':u'd'}


def accent2bare(data):
    s = u''
    for c in data.lower():
        try:
            s += conv_dict[c]
        except:
            s += c
    return s



m = master()
handle = Process(target=m.run)
handle.start()



def get_long_events(event_name, trending_json):
    long_event = None
    for event in trending_json[u'content']:
        if event[u'event_name'] != event_name:
            continue
        long_event = event[u'long_event']
        break
    return long_event


def build_flow_event(long_event):
    flow = [u' | '.join([long_event[u'date'], long_event[u'event_name']])]
    for child in long_event[u'child_events']:
        flow.append(u' | '.join([child[u'date'], child[u'event_name']]))
    return u'\n'.join(flow)


def build_trending_domain(trending_titles, docs_trending, contentId2publisher, trending_json):
    # build json content
    trending = []
    for k, title in trending_titles.items():
        event = {}
        docs = docs_trending[k]
        event_name = title.split(u' == ')[1]
        event.update({u'title': event_name + u' - %d docs' % (len(docs))})
        sub_title = []
        for name in docs:
            try:
                sub_title.append({u'title': u' - '.join([name.split(u' == ')[1],
                                                          u'Báo ' + contentId2publisher[name.split(u' == ')[0]]]),
                                  u'contentId': name.split(u' == ')[0]})
            except:
                sub_title.append({u'title': name.split(u' == ')[1],
                                  u'contentId': name.split(u' == ')[0]})
        # to do at here
        long_event = get_long_events(event_name, trending_json)
        flow_event = build_flow_event(long_event)

        event.update({u'subTitles': sub_title, u'flowOfEvent': flow_event})
        trending.append(event)
    return trending


def reformat_trending_json(trending_json):
    new_trending_json = {}
    for event in trending_json[u'hot_events']:
        domain = event[u'domain']
        new_trending_json.update({domain : event})
    return new_trending_json


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
    try:
        trending_titles = joblib.load(m.trending_titles_file)
        docs_trending = joblib.load(m.docs_trending_file)
        contentId2publisher = joblib.load(m.contentId2publisher_file)
        trending_json = joblib.load(m.trending_json_file)
        trending_json = reformat_trending_json(trending_json)
        result = []
        for domain in trending_titles.keys():
            json_content = {}
            json_content.update({u'domain' : domain, u'id' : accent2bare(domain.replace(u' ', u'-').lower())})
            trending_domain = build_trending_domain(trending_titles[domain],
                                                    docs_trending[domain],
                                                    contentId2publisher,
                                                    trending_json[domain])
            json_content.update({u'content' : trending_domain})
            result.append(json_content)

        # import json
        # from io import open
        # with open('trending_sample.json', 'w', encoding='utf-8') as fp:
        #     trending_sample = json.dumps(result, ensure_ascii=False, encoding='utf-8')
        #     fp.write(unicode(trending_sample))

        return jsonify(result)
    except Exception as e:
        print(e.message)
        return jsonify([])


@app.route('/get', methods = ['GET', 'POST'])
def get_content():
    contentId = request.form['contentId']
    content = demo.get_summary_and_content(contentId)
    return jsonify(content)




if __name__ == '__main__':
    app.run('0.0.0.0', port=11113)