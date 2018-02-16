# coding=utf-8
import importlib.util
import os


class ConfigError(Exception):
    pass


class Node:
    def __init__(self, config):
        self.config = config

    def process(self, input_data):
        raise NotImplementedError()


class InfoPipe:
    node_types = {}

    def __init__(self, config):
        self.config = config

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
            self.nodes[n['name']] = InfoPipe.node_types[n['type']](n)

    def run(self):
        outputs = {}

        def process_node(node):
            if node.config['name'] in outputs.keys():
                return outputs[node.config['name']]
            if node.config['name'] not in self.nodes:
                print('Unknown node "{}"'.format(node.config['name']))
                return []
            out = self.nodes[node.config['name']].process(
                sum([process_node(self.nodes[d]) for d in node.config['depend']], []) if 'depend' in node.config else []
            )
            outputs[node.config['name']] = out

        for n in self.nodes.values():
            process_node(n)
