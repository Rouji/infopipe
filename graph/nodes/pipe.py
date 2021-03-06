from ..graph import Node, Graph


@Graph.register('pipe')
class Passthrough(Node):
    def __init__(self, config):
        super().__init__(config)

    def process(self, input_data):
        return input_data
