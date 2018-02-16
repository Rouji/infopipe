from infopipe import Node, InfoPipe


@InfoPipe.register('passthrough')
class Passthrough(Node):
    def __init__(self, config):
        super().__init__(config)

    def process(self, input_data):
        return input_data
