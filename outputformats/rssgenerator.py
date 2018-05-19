from schema import SchemaVal
from infopipe import Node, InfoPipe, ConfigError
from datetime import datetime
import html
import hashlib


@InfoPipe.register('rssgenerator')
class RSSGenerator(Node):
    header = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
    <title type="text">{title}</title>
    <id>{link}</id>
    <link rel="self" href="{link}"/>
    <subtitle type="text">{description}</subtitle>
    <updated>{date}</updated>
    """
    item = """
    <entry>
        <id>{guid}</id>
        <title>{title}</title>
        <link rel="alternate" href="{link}"/>
        <content type="html">{content}</content>
        <updated>{date}</updated>
    </entry>
    """
    footer = """
    </feed>
    """
    dateformat = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, config):
        super().__init__(config)
        self.config_schema.add_vals({'path': SchemaVal(True)})
        if 'path' not in config:
            raise ConfigError('rssgenerator config requires "path" value')

    def process(self, input_data):
        with open(self.config['path'], 'w') as f:
            now = datetime.now().strftime(RSSGenerator.dateformat)
            vals = {
                'title': html.escape(self.config.get('title', self.config['name'])),
                'link': self.config.get('link', ''),
                'description': html.escape(self.config.get('description', '')),
                'date': now
            }
            f.write(RSSGenerator.header.format(**vals))

            for d in input_data:
                vals = {
                    'title': html.escape(d['title']),
                    'link': html.escape(d['link']),
                    'content': html.escape(d['content']) if 'content' in d and type(d['content']) is str else '',
                    'date': html.escape(d['date'].strftime(RSSGenerator.dateformat)),
                    'guid': d.get('id', self.config['name'] + '.' + hashlib.md5(d['title'].encode('utf-8')).hexdigest())
                }
                f.write(RSSGenerator.item.format(**vals))
            f.write(RSSGenerator.footer)

