"""
This module is used to send messages to a slack webhook
"""

import urllib2
from urllib import urlencode
from os import getenv

class Slack(object):
    def __init__(self):
        """Setup the slack integration"""
        setattr(self, "webhook", getenv('SLACK_WEBHOOK', ""))
        if self.webhook:
            print "Setting up slack notifications"
            setattr(self, "slack_enabled", True)
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
            opener = urllib2.build_opener(urllib2.HTTPHandler())
            req = urllib2.Request(self.webhook)
            opener.open(req, data.encode('utf-8'))