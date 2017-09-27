from datetime import datetime
from scrapy import signals
from slacker import Slacker
from scrapy.exceptions import NotConfigured


class SlackStats(object):

    def __init__(self, slack_api_token, channel, bot):
        self.slack = Slacker(slack_api_token)
        self.channel = channel
        self.bot = bot
        self.start = datetime.now()
        self.finish = None

    @classmethod
    def from_crawler(cls, crawler):
        slack_api_token = crawler.settings.getlist('SLACK_API_TOKEN')
        channel = crawler.settings.getlist('SLACK_CHANNEL')
        bot = crawler.settings.getlist('SLACK_BOT')
        if (not slack_api_token or not channel or not bot):
            raise NotConfigured
        ext = cls(slack_api_token, channel, bot)
        crawler.signals.connect(ext.start_stats, signal=signals.spider_opened)
        crawler.signals.connect(ext.finish_stats, signal=signals.stats_spider_closed)
        return ext

    def start_stats(self, spider):
        attachments = [
            {
                'title': 'Crawl {} started at {}'.format(spider.name, str(self.start)),
                'fallback': 'Crawler started',
                'color': 'good',
            }
        ]
        self.slack.chat.post_message(channel=str(self.channel[0]),
                                     text=None, icon_emoji=':+1:',
                                     username=self.bot[0],
                                     attachments=attachments)

    def finish_stats(self, spider):
        spider_stats = spider.crawler.stats.get_stats()
        if spider_stats['finish_reason'] == 'finished':
            color = 'good'
            emoji = ':white_check_mark:'
        else:
            color = 'bad'
            emoji = ':no_entry_sign:'
        fields = [{"title": k[k.find('/') + 1:],
                   "value": str(v),
                   "short": True} for k, v in spider_stats.items()]
        self.finish = datetime.now()
        attachments = [
            {
                'title': 'Crawl {} finished at {} in {}'.format(spider.name, str(self.finish), str(self.finish - self.start)),
                'fallback': 'Crawler finished',
                'color': color,
                'mrkdwn_in': ['text', 'pretext'],
                'fields': fields
            }
        ]
        self.slack.chat.post_message(channel=str(self.channel[0]), text=None,
                                     icon_emoji=emoji, username=self.bot[0],
                                     attachments=attachments)
        return
