#!/usr/bin/env python3
# coding=utf-8

import sqlite3

from entrypoint2 import entrypoint

from config import DB_PATH, UPDATE_INTERVAL
from graph.graph import Graph
from sqlitestore import SqliteStore


@entrypoint
def main(daemon=False):
    with sqlite3.connect(DB_PATH) as conn:
        def upd():
            for u, k, c in SqliteStore(conn).get_users():
                Graph(c, SqliteStore(conn, u, k)).update()

        if daemon:
            from apscheduler.schedulers.blocking import BlockingScheduler
            sched = BlockingScheduler()
            sched.add_job(upd, 'interval', minutes=UPDATE_INTERVAL or 15, max_instances=1)
            sched.start()
        else:
            upd()
