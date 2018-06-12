# coding=utf-8
from typing import List, Tuple, Union
from importlib.util import spec_from_file_location, module_from_spec
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


class OutputStore(object):
    def store_output(self, node: str, data: List[dict]) -> List[Tuple[str, str, dict]]:
        raise NotImplementedError()

    def get_output(self, node: str, count: Union[None, int] = None):
        raise NotImplementedError()

    def get_node_names(self):
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
        'properties': {
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

    def __init__(self, config: dict, output_store: OutputStore):
        self.config = config
        validate(config, self.config_schema)

        self.store = output_store

        self.nodes = {}

        self.load_types()
        self.instantiate_nodes(self.config['nodes'])

    @classmethod
    def register(cls, name):
        def reg(node_type):
            cls.node_types[name] = node_type
            return node_type

        return reg

    @staticmethod
    def load_types():
        path = os.path.join(os.path.dirname(__file__), 'nodes')
        for f in [f for f in os.listdir(path) if f.endswith('.py')]:
            name = f.rsplit('.py', 1)[0]
            spec = spec_from_file_location('graph.nodes.' + name,
                                           os.path.join(path, f))
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)

    def instantiate_nodes(self, nodes):
        for n in nodes:
            if n['type'] not in Graph.node_types:
                print('Unknown node type "{}"'.format(n['type']), file=sys.stderr)
                continue
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
                return []

            depend_out = [
                process_node(self.nodes[dep])
                for dep
                in node.config.get('depend', [])
            ]
            out = self.nodes[name].process(
                sum([dep for dep in depend_out if dep], [])
            )
            if not out:
                return
            outputs[name] = self.store.store_output(name, out)

        for n in self.nodes.values():
            process_node(n)
