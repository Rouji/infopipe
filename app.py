#!/usr/bin/env python3
# coding=utf-8

import sqlite3
from flask import Flask, jsonify, g, request
from graph import Graph
from config import CFG_PATH, DB_PATH
import json

app = Flask(__name__)


def db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
    return db


def ip():
    ip = getattr(g, '_ip', None)
    if ip is None:
        with open(CFG_PATH) as c:
            ip = g._ip = Graph(json.load(c), db())
    return ip


@app.teardown_appcontext
def teardown_db(ex):
    db = getattr(g, '_db', None)
    if db is not None:
        db.close()


@app.route('/nodes', methods=['GET'])
def nodes():
    return jsonify(ip().node_names())


@app.route('/output/<name>', methods=['GET'])
def node(name: str):
    out = ip().get_output(name)
    if out is None:
        return '', 404
    return app.response_class(
        response=out,
        status=200,
        mimetype='application/json; charset=utf-8'
    )


@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'GET':
        with open(CFG_PATH) as conf:
            return app.response_class(
                response=conf.read(),
                status=200,
                mimetype='application/json; charset=utf-8'
            )
    else:
        data = request.get_data()
        print(data)
        try:
            Graph(json.loads(data), db())  # validate config
            with open(CFG_PATH, 'w') as conf:
                conf.write(data)
        except Exception as ex:
            return str(ex), 400


if __name__ == '__main__':
    app.run()
