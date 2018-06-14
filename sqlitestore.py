import json

from graph.graph import OutputStore


class SqliteStore(OutputStore):
    def __init__(self, sqlite_conn, user=None, key=None):
        self.conn = sqlite_conn
        self.user = user
        self.key = key

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS config(
            user TEXT PRIMARY KEY COLLATE NOCASE,
            key TEXT,
            config TEXT);""")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS node_output(
            user TEXT COLLATE NOCASE,
            time TIMESTAMP DEFAULT current_timestamp,
            node TEXT,
            uid TEXT,
            output TEXT,
            UNIQUE(user, node, uid) ON CONFLICT REPLACE);""")
        self.conn.commit()

    def store_output(self, node, data):
        stored = self.conn.execute("""
            SELECT uid
            FROM node_output
            WHERE user = ?
            AND node = ?;""",
                                   (self.user, node))
        stored = {s[0] for s in stored} if stored else set()
        new_data = [d for d in data if d['id'] not in stored]
        if not new_data:
            return []

        self.conn.executemany("""
            INSERT INTO node_output(user, node, uid, output)
            VALUES(?, ?, ?, ?);""",
                              [(self.user, node, d['id'], json.dumps(d)) for d in new_data])
        self.conn.commit()
        return new_data

    def get_output(self, node, count=None):
        res = self.conn.execute("""
            SELECT output
            FROM node_output
            WHERE user = ?
            AND node = ? {};""".format('LIMIT ' + count if count else ''), (self.user, node))
        return [json.loads(r[0]) for r in res]

    def get_node_names(self):
        res = self.conn.execute('SELECT DISTINCT node FROM node_output WHERE user = ?;', (self.user,))
        return [r[0] for r in res]

    def get_config(self):
        res = self.conn.execute('SELECT user, key, config FROM config WHERE user = ?;', (self.user,))
        r = res.fetchone()
        if not r:
            return None, None, None
        return (r[0], r[1], json.loads(r[2]))

    def get_users(self):
        res = self.conn.execute('SELECT user, key, config FROM config;')
        for r in res:
            yield (r[0], r[1], json.loads(r[2]))

    def save_config(self, config):
        self.conn.execute('REPLACE INTO config(user, key, config) VALUES(?, ?, ?);',
                          (self.user, self.key, json.dumps(config)))
        self.conn.commit()
