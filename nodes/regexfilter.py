from infopipe import Node, InfoPipe
from schema import SchemaVal
import re


@InfoPipe.register('regex')
class RegexFilter(Node):
    def __init__(self, config):
        super().__init__(config)
        self.config_schema.add_vals({'regex': SchemaVal(True)})
        self.re = re.compile(self.conf('regex'))

    def process(self, input_data):
        return [
            d for d in input_data
            if self.re.match(d['title'])
            or (d['content'] and self.re.match(d['content']))
        ]
