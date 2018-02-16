from infopipe import Node, InfoPipe, ConfigError
import feedparser
import dateutil.parser
from datetime import datetime


@InfoPipe.register('rssreader')
class RSSReader(Node):
    def __init__(self, config):
        super().__init__(config)
        if 'feeds' not in config:
            raise ConfigError('rssreader config requires "feeds" array')

    def entry_to_output(self, entry):
        content = None
        try:
            content = entry['content'][0]['value']
        except Exception as ex:
            pass

        try:
            date = dateutil.parser.parse(entry['published'])
        except ValueError as ex:
            date = datetime.now()

        return {
            'source': self.config['name'],
            'id': entry['id'],
            'link': entry['link'],
            'title': entry['title'],
            'date': dateutil.parser.parse(entry['published']),
            'content': content
        }

    def process(self, input_data):
        def parse_feeds(feeds):
            for feed in feeds:
                parsed = feedparser.parse(feed)
                if 'entries' not in parsed:
                    continue
                for entry in parsed['entries']:
                    yield self.entry_to_output(entry)
        return list(parse_feeds(self.config['feeds']))
