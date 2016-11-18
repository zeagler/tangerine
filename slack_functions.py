"""
This module is used to send messages to a slack webhook
"""

from urllib.request import build_opener, HTTPHandler, Request
from urllib.parse import urlencode

from settings import settings

class Slack(object):
    def send_message(self, message):
        """
        Send a message to the Slack webhook
        
        Args:
            message: The String message to be sent
        """
        if settings['slack_enabled'] == "true":
            data = urlencode({"payload": '{"username": "tangerine", "text": "'+message+'", "icon_emoji": ":tangerine:"}'})
            opener = build_opener(HTTPHandler())
            req = Request(settings['slack_webhook'])
            opener.open(req, data.encode('utf-8'))