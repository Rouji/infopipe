#!/usr/bin/env python3
# coding=utf-8

import json

from apscheduler.schedulers.blocking import BlockingScheduler
from entrypoint2 import entrypoint
from flask import Flask, jsonify

from infopipe import InfoPipe

sched = BlockingScheduler()
app = Flask(__name__)
ip: InfoPipe = None


@app.route('/', methods=['GET'])
def root():
    return jsonify(list(ip.node_names()))


@app.route('/<name>', methods=['GET'])
def node(name: str):
    return ip.get_output(name) or ''


@entrypoint
def main(config='config.json', daemon=False):
    global ip
    with open(config) as c:
        ip = InfoPipe(json.load(c))
    if daemon:
        @sched.scheduled_job('interval', minutes=1, max_instances=1)
        def daemon():
            ip.update()

        sched.start()
    else:
        app.run()
