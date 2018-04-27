from infopipe import Node, InfoPipe
from schema import SchemaVal


@InfoPipe.register('txtgenerator')
class TxtGenerator(Node):
    def __init__(self, config):
        super().__init__(config)
        self.config_schema.add_vals({'path': SchemaVal(True)})

    def process(self, input_data):
        with open(self.config['path'], 'w') as f:
            for d in input_data:
                f.write(d['title'] + "\n" + d['link'] + "\n\n")
