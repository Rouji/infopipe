from graph import Node, Graph
import feedparser
import dateutil.parser
from datetime import datetime
import calendar
from concurrent import futures


@Graph.register('rssreader')
class RSSReader(Node):
    def __init__(self, config):
        super().__init__(config)
        self.config_schema['properties']['feeds'] = {
            'type': 'array', 'items': {'type': 'string'}
        }
        self.config_schema['required'].append('feeds')

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
            'timestamp': calendar.timegm(date.timetuple()),
            'content': content or ''
        }

    def process(self, input_data):
        def parse_feed(feed):
            parsed = feedparser.parse(feed)
            if 'entries' not in parsed:
                return []
            return [self.entry_to_output(e) for e in parsed['entries']]
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            futs = [executor.submit(parse_feed, f) for f in self.config['feeds']]
            feeds = [fut.result() for fut in futures.as_completed(futs)]
            return [entry for feed in feeds for entry in feed]
