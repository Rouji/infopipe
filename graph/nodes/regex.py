import re

from ..graph import Node, Graph


@Graph.register('regex')
class RegexFilter(Node):
    def __init__(self, config):
        super().__init__(config)
        self.config_schema['properties']['regex'] = {'type': 'string'}
        self.config_schema['required'].append('regex')

        self.re = re.compile(self.config['regex'])

    def process(self, input_data):
        return [
            d for d in input_data
            if self.re.search(d['title'])
               or (d['content'] and self.re.search(d['content']))
        ]
