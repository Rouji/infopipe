from infopipe import Node, InfoPipe


@InfoPipe.register('txtgenerator')
class TxtGenerator(Node):
    def process(self, input_data):
        with open(self.config['path'], 'w') as f:
            for d in input_data:
                f.write(d['title'] + "\n" + d['link'] + "\n\n")
