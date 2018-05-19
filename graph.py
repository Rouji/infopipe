# coding=utf-8
from importlib.util import spec_from_file_location, module_from_spec
import json
import os
import sys
from jsonschema import validate


class Node:
    def __init__(self, config):
        self.config_schema = {
            'type': 'object',
            'properties': {
                'type': {'type': 'string'},
                'name': {'type': 'string'},
                'depend': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'default': []
                }
            },
            'required': ['type', 'name']
        }

        self.config = config

    def process(self, input_data):
        raise NotImplementedError()


class Graph(object):
    node_types = {}
    config_schema = {
        'type': 'object',
        'properties': {
            'nodes': {'type': 'array', 'items': {'type': 'object'}},
        },
        'required': ['nodes']
    }

    output_schema = {
        'type': 'object',
        'properties':
        {
            'source': {'type': 'string'},
            'id': {'type': 'string'},
            'title': {'type': 'string'},
            'timestamp': {'type': 'number'},
            'content': {'type': 'string', 'default': ''},
            'link': {'type': 'string'},
            'author': {'type': 'string'},
            'tags': {'type': 'array', 'items': {'type': 'string'}}
        },
        'required': ['source', 'id', 'title', 'timestamp']
    }

    def __init__(self, config, sqlitedb):
        self.config = config
        validate(config, Graph.config_schema)

        self.db = sqlitedb

        # create table
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS node_output(
                time TIMESTAMP DEFAULT current_timestamp,
                node TEXT,
                uid TEXT,
                output TEXT,
                UNIQUE(node, uid) ON CONFLICT REPLACE);""")
        self.db.commit()

        self.nodes = {}

        self.load_types('nodes')
        self.instantiate_nodes(self.config['nodes'])

    @classmethod
    def register(cls, name):
        def reg(node_type):
            cls.node_types[name] = node_type
            return node_type

        return reg

    def load_types(self, path):
        for f in [f for f in os.listdir(path) if f.endswith('.py')]:
            name = f.rsplit('.py', 1)[0]
            spec = spec_from_file_location('graph.nodes.' + name,
                                           os.path.join(path, f))
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)

    def instantiate_nodes(self, nodes):
        for n in nodes:
            if n['type'] not in Graph.node_types:
                raise RuntimeError('Unknown node type "{}"'.format(n['type']))
            new = Graph.node_types[n['type']](n)
            validate(new.config, new.config_schema)
            self.nodes[n['name']] = new

    def update(self):
        outputs = {}

        def process_node(node):
            name = node.config['name']
            if name in outputs.keys():
                return outputs[name]
            if name not in self.nodes:
                print(f'Unknown node "{name}"', file=sys.stderr)
                return []

            depend_out = [
                process_node(self.nodes[dep])
                for dep
                in node.config.get('depend', [])
            ]
            out = self.nodes[name].process(
                sum([dep for dep in depend_out if dep], [])
            )
            if not out or len(out) < 1:
                return

            res = self.db.execute(
                """SELECT uid
                FROM node_output
                WHERE node = ?;""",
                (node.config['name'],)
            )
            rows = res.fetchall()
            ids = {}
            if rows:
                ids = {r[0] for r in rows}
            new = [n for n in out if n['id'] not in ids]
            outputs[name] = new
            # print(f'node: {name}, new: {len(new)}')
            for n in new:
                validate(n, Graph.output_schema)
            if len(new) > 0:
                self.db.executemany(
                    """INSERT INTO node_output(node, uid, output)
                    VALUES(?, ?, ?);""",
                    [(name, n['id'], json.dumps(n)) for n in new])
                self.db.commit()

        for n in self.nodes.values():
            process_node(n)

    def node_names(self):
        return list(self.nodes.keys())

    def get_output(self, node: str, limit: int = 100):
        res = self.db.execute(
            """SELECT output
            FROM node_output
            WHERE node = ?
            ORDER BY time DESC
            LIMIT ?;""",
            (node, limit)
        )
        rows = res.fetchall()
        if not rows:
            return None
        return '[' + ','.join([r[0] for r in rows]) + ']'
