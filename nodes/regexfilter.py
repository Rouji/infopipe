from infopipe import Node, InfoPipe
import re


@InfoPipe.register('regex')
class RegexFilter(Node):
    def __init__(self, config):
        super().__init__(config)
        self.re = re.compile(config['regex'])

    def process(self, input_data):
        return [
            d for d in input_data
            if self.re.match(d['title'])
            or (d['content'] and self.re.match(d['content']))
        ]
