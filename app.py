#!/usr/bin/env python3
# coding=utf-8

import random
import sqlite3
import string
from functools import wraps
from os.path import isfile

from flask import Flask, jsonify, g, request, render_template

from config import DB_PATH, KEY_LEN
from graph.graph import Graph
from sqlitestore import SqliteStore

app = Flask(__name__)


def rnd_str(length: int) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def require_key(route):
    @wraps(route)
    def wrap(*args, **kwargs):
        user = request.path.split('/', 2)[1]
        key = request.values.get('key', None)
        if not key:
            return jsonify({'error': 'No key provided.'}), 403
        g._store = SqliteStore(db(), user, key)
        _, _key, g._config = g._store.get_config()
        if _ is None:
            return jsonify({'error': "User '{}' doesn't exist.".format(user)}), 403
        if key != _key:
            return jsonify({'error': "Incorrect key.".format(user)}), 403
        return route(*args, **kwargs)

    return wrap


def db():
    if not getattr(g, '_db', None):
        create = not isfile(DB_PATH)
        g._db = sqlite3.connect(DB_PATH)
        if create:
            SqliteStore(g._db, None).create_tables()
    return g._db


@app.teardown_appcontext
def teardown_db(ex):
    db = getattr(g, '_db', None)
    if db:
        db.close()


@app.route('/')
def root():
    return render_template('index.html')


@app.route('/<user>/nodes', methods=['GET'])
@require_key
def nodes(user: str):
    return jsonify(g._store.get_node_names())


@app.route('/<user>/nodes/<node>', methods=['GET'])
@require_key
def output(user: str, node: str):
    return jsonify(g._store.get_output(node))


@app.route('/<user>/config', methods=['GET', 'POST'])
@require_key
def config(user: str):
    if request.method == 'GET':
        return jsonify(g._config)
    else:
        if not request.json:
            return jsonify({'error': 'Did not receive any JSON.'})
        try:
            Graph(request.json, g._store)  # validate config
            g._store.save_config(request.json)
        except Exception as ex:
            print(str(ex))
            return jsonify({"error": "Invalid config."}), 400
        return jsonify({"success": True})


@app.route('/register/<user>', methods=['GET'])
def register(user: str):
    key = rnd_str(KEY_LEN)
    store = SqliteStore(db(), user, key)
    u, k, c = store.get_config()
    if u:
        return jsonify({'error': "User '{}' already exists.".format(u)})
    store.save_config(c or {})
    return jsonify({'user': user, 'key': key})


if __name__ == '__main__':
    app.run(debug=True)
