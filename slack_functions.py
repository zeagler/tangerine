"""
This module is used to send messages to a slack webhook
"""

from urllib import urlencode
import urllib2
import os

def open_slack_webhook():
    """Setup the global variables used in this module"""
    global opener, req, payload, enabled
    
    webhook = os.getenv('SLACK_WEBHOOK', "")
    if webhook:
        print "Setting up slack notifications"
        enabled = True
        opener = urllib2.build_opener(urllib2.HTTPHandler())
        req = urllib2.Request(webhook)
    else:
        print "SLACK_WEBHOOK is not set, Slack notifications will be disabled"
        enabled = False

def send_message(message):
    """
    Send a message to the Slack webhook
    
    Args:
        message: The String message to be sent
    """
    if enabled:
        data = urlencode({"payload": '{"username": "tangerine", "text": "'+message+'", "icon_emoji": ":tangerine:"}'})
        opener.open(req, data.encode('utf-8'))