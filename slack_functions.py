"""
This module is used to send messages to a slack webhook
"""

from urllib import urlencode
import urllib2
import os

class Slack(object):
    def __init__(self):
        """Setup the slack integration"""
        webhook = os.getenv('SLACK_WEBHOOK', "")
        if webhook:
            print "Setting up slack notifications"
            setattr(self, "slack_enabled", True)
            setattr(self, "opener", urllib2.build_opener(urllib2.HTTPHandler()))
            setattr(self, "req", urllib2.Request(webhook))
        else:
            print "SLACK_WEBHOOK is not set, Slack notifications will be disabled"
            setattr(self, "slack_enabled", False)

    def send_message(self, message):
        """
        Send a message to the Slack webhook
        
        Args:
            message: The String message to be sent
        """
        if self.slack_enabled:
            data = urlencode({"payload": '{"username": "tangerine", "text": "'+message+'", "icon_emoji": ":tangerine:"}'})
            self.opener.open(self.req, data.encode('utf-8'))