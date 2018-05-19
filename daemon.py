#!/usr/bin/env python3
# coding=utf-8

from entrypoint2 import entrypoint
from graph import Graph
import sqlite3
import json
import config

@entrypoint
def main(daemonize=False, interval_minutes=5):
    with sqlite3.connect(config.DB_PATH) as db:
        def upd():
            with open(config.CFG_PATH) as c:
                ip = Graph(json.load(c), db)
                ip.update()
        if daemonize:
            from apscheduler.schedulers.blocking import BlockingScheduler
            sched = BlockingScheduler()
            sched.add_job(upd, 'interval', minutes=interval_minutes, max_instances=1)
            sched.start()
        else:
            upd()
