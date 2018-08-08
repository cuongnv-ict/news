# -*- coding: utf-8 -*-
__author__ = 'nobita'

from normalization import normalization
from flask import Flask, request
import HTMLParser


nor = normalization()

app = Flask(__name__, static_url_path='',
            static_folder='static',
            template_folder='templates')

@app.route('/', methods = ['GET'])
def homepage():
    return app.send_static_file('index.html')


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/acronym', methods=['POST'])
def process_request():
    data = request.form['data']
    data = HTMLParser.HTMLParser().unescape(data)
    result = nor.run(data)
    return result


if __name__ == '__main__':
    app.run('0.0.0.0', port=9449)
