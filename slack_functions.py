"""
This module is used to send messages to a slack webhook
"""

import urllib2
from urllib import urlencode
from os import getenv
from settings import Slack as options

class Slack(object):
    def send_message(self, message):
        """
        Send a message to the Slack webhook
        
        Args:
            message: The String message to be sent
        """
        if options['ENABLED']:
            data = urlencode({"payload": '{"username": "tangerine", "text": "'+message+'", "icon_emoji": ":tangerine:"}'})
            opener = urllib2.build_opener(urllib2.HTTPHandler())
            req = urllib2.Request(options['SLACK_WEBHOOK'])
            opener.open(req, data.encode('utf-8'))