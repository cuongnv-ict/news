# -*- encoding: utf-8 -*-

from flask import Flask, request
from flask import jsonify
from event_detection import demo
from text_classification import my_map
from master import master
from threading import Thread



m = master()
handle = Thread(target=m.run)
handle.start()

app = Flask(__name__, static_url_path='',
            static_folder='static',
            template_folder='templates')


@app.route('/', methods = ['GET'])
def homepage():
    return app.send_static_file('event.html')


@app.route('/update', methods = ['GET', 'POST'])
def update():
    return jsonify(m.trending_jsons[my_map.label2name[7]])


@app.route('/get', methods = ['GET', 'POST'])
def get_content():
    title = request.form['title']
    content = demo.get_document_by_title(title, m.documents[my_map.label2name[7]])
    return jsonify(content)


if __name__ == '__main__':
    app.run('0.0.0.0', port=11111)