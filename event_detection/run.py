# -*- encoding: utf-8 -*-
from flask import Flask, request
from flask import jsonify
from detect_event import event_detection
import demo


app = Flask(__name__, static_url_path='',
            static_folder='static',
            template_folder='templates')


event = event_detection('thời sự', 'dataset/thời sự', num_topics=100)
documents, trending_json = event.run_demo()

@app.route('/', methods = ['GET'])
def homepage():
    return app.send_static_file('event.html')


@app.route('/update', methods = ['GET', 'POST'])
def update():
    return jsonify(trending_json)


@app.route('/get', methods = ['GET', 'POST'])
def get_content():
    title = request.form['title']
    content = demo.get_document_by_title(title, documents)
    return jsonify(content)


if __name__ == '__main__':
    app.run('0.0.0.0', port=11111)