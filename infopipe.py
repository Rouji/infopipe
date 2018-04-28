# coding=utf-8
import importlib.util
import os
from schema import Schema, SchemaVal
import sqlite3
import json
from datetime import datetime


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S')
        return json.JSONEncoder.default(obj)


class ConfigError(Exception):
    pass


class Node:
    def __init__(self, config):
        self.config_schema = Schema()
        self.config_schema.add_vals({
            'type': SchemaVal(True),
            'name': SchemaVal(True),
            'depend': SchemaVal(False, default=[])
        })
        self.config = config

    def conf(self, name: str):
        return self.config_schema.get(self.config, name)

    def process(self, input_data):
        raise NotImplementedError()


class InfoPipe:
    node_types = {}
    config_schema = Schema()
    config_schema.add_vals({
        'db': SchemaVal(True, default='data.db'),
        'nodes': SchemaVal(True, default=[])
    })

    output_schema = Schema()
    output_schema.add_vals({
        'source': SchemaVal(True, vartype=str),
        'id': SchemaVal(True, vartype=str),
        'title': SchemaVal(True, vartype=str),
        'date': SchemaVal(True, vartype=datetime),
        'content': SchemaVal(False, vartype=str, default=''),
        'link': SchemaVal(False, vartype=str),
        'author': SchemaVal(False, vartype=str),
        'tags': SchemaVal(False, vartype=list, default=[])
    })

    def __init__(self, config):
        self.config = config
        InfoPipe.config_schema.validate(config)

        self.db = sqlite3.connect(self.config['db'])
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS node_output(
                time TIMESTAMP DEFAULT current_timestamp,
                node TEXT,
                uid TEXT,
                output TEXT,
                UNIQUE(node, uid) ON CONFLICT REPLACE);""")
        self.db.commit()

        self.nodes = {}

        self.load_types('nodes')
        self.instantiate_nodes()

    @classmethod
    def register(cls, name):
        def reg(node_type):
            cls.node_types[name] = node_type
            return node_type

        return reg

    def load_types(self, path):
        for f in [f for f in os.listdir(path) if f.endswith('.py')]:
            name = f.rsplit('.py', 1)[0]
            spec = importlib.util.spec_from_file_location('infopipe.' + name, os.path.join(path, f))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

    def instantiate_nodes(self):
        for n in self.config['nodes']:
            if n['type'] not in InfoPipe.node_types:
                raise RuntimeError('Unknown node type "{}"'.format(n['type']))
            new = InfoPipe.node_types[n['type']](n)
            new.config_schema.validate(new.config)
            self.nodes[n['name']] = new

    def update(self):
        outputs = {}

        def process_node(node):
            name = node.conf('name')
            if name in outputs.keys():
                return outputs[name]
            if name not in self.nodes:
                print(f'Unknown node "{name}"')
                return []

            depend_out = [process_node(self.nodes[dep]) for dep in node.conf('depend')]
            out = self.nodes[name].process(
                sum([dep for dep in depend_out if dep], [])
            )
            if not out or len(out) < 1:
                return

            res = self.db.execute('SELECT uid FROM node_output WHERE node = ?;', (node.config['name'],))
            rows = res.fetchall()
            ids = {}
            if rows:
                ids = {r[0] for r in rows}
            new = [n for n in out if n['id'] not in ids]
            outputs[name] = new
            print(f'node: {name}, new: {len(new)}')
            for n in new:
                InfoPipe.output_schema.validate(n)
            if len(new) > 0:
                self.db.executemany('INSERT INTO node_output(node, uid, output) VALUES(?, ?, ?);',
                                    [(name, n['id'], json.dumps(n, cls=DateTimeEncoder)) for n in new])
                self.db.commit()

        for n in self.nodes.values():
            process_node(n)

    def node_names(self):
        return self.nodes.keys()

    def get_output(self, node: str, limit: int = 100):
        res = self.db.execute('SELECT output FROM node_output WHERE node = ? ORDER BY time DESC LIMIT ?;', (node, limit))
        rows = res.fetchall()
        if not rows:
            return None
        return '[' + ','.join([r[0] for r in rows]) + ']'
