# -*- coding: utf-8 -*-

"""
Slackython Library
~~~~~~~~~~~~~~~~~~~~~

Slackython is a Slack notification library, written in Python.

Basic use:
   >>> from slackython import Slackython
   >>> notificator = Slackython('https://hooks.slack.com/services/../../..')
   >>> notificator.send_message('Status: Working', title='Slackython')

For more complex or complete use is recommended using a list of the ids of the
supervisors of slack in the following way:
   >>> notificator = Slackython('...', ['U0AAABBBC', 'U0AAABBBD'])

That allow to send critical messages with a corresponding tag for each user.

The recommended way to use Slackython is defining it on one file (ex. utils.py)
and then calling a getter of the singleton instance.
   >>> notificator = Slackython('...', ['...'])
   >>> def get_slack_logger():
   >>>    return notificator


:copyright: (c) 2018 by Michel Llorens.
:license: MIT, see LICENSE for more details.
"""


import copy
import json
import logging
from enum import Enum

import requests


logger = logging.getLogger('slackython')


class NotificationLevel(Enum):
    NORMAL = "#00C853"
    INFORMATION = "#FFD600"
    CRITICAL = "#d50000"


class Slackython(object):
    def __init__(self, webhook, slack_supervisors=None):
        """
        Constructor for the slack notificator.
        :param webhook: A valid slack webhook url
        :param slack_supervisors: optional list of ids of slack users.
        """

        self.webhook_url = webhook

        self.slack_supervisors = list()
        if slack_supervisors is not None:
            self.slack_supervisors = slack_supervisors

        self.base_template = {
            "attachments": [
            ]
        }
        self.attachment_template = {
            "text": "",
            "color": ""
        }

    def _send_to_webhook(self, data, retries=3):
        """
        Private method to send data to the slack webhook.
        :param data: Slack payload
        :param retries: Number of retries
        :return:
        """
        for retry in range(retries):
            try:
                response = requests.post(
                    self.webhook_url,
                    data=json.dumps(data),
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    logger.info("Success response")
                    break
                else:
                    logger.info("Response status {}.\nRetrying".format(
                        response.status_code
                    ))
            except requests.exceptions.Timeout:
                logger.error("Request timeout.")
            except requests.exceptions.TooManyRedirects:
                logger.error("Request too many redirects.")
            except requests.exceptions.RequestException as e:
                logger.error("Requests connection error.")
                logger.error(e)

    def _generate_message_slack(
            self, message, level, title=None, tagged_members=None
    ):
        """
        Private method to generate the structure of the slack payload.
        :param message: String message
        :param level: NotificationLevel
        :param title: Optional string title
        :param tagged_members: Optional list of slack user id
        :return:
        """
        data = copy.deepcopy(self.base_template)
        if title is not None:
            data['text'] = title

        event = copy.deepcopy(self.attachment_template)
        event["text"] = message
        event["color"] = level.value
        data["attachments"].append(event)

        if tagged_members is not None:
            for member in tagged_members:
                tagged_event = copy.deepcopy(self.attachment_template)
                tagged_event["text"] = "<@{}>".format(member)
                tagged_event["color"] = level.value
                data["attachments"].append(tagged_event)

        return data

    def send_message(self, message, title=None, tagged_members=None):
        """
        Send a normal message
        :param message: String message
        :param title: Optional string title
        :param tagged_members: Optional list of slack user id
        :return:
        """
        data = self._generate_message_slack(
            message, NotificationLevel.NORMAL, title, tagged_members
        )

        logger.info("Sending message {}".format(message))
        self._send_to_webhook(data)

    def send_information(self, message, title=None, tagged_members=None):
        """
        Send a information message
        :param message: String message
        :param title: Optional string title
        :param tagged_members: Optional list of slack user id
        :return:
        """
        data = self._generate_message_slack(
            message, NotificationLevel.INFORMATION, title, tagged_members
        )
        logger.info("Sending information {}".format(message))
        self._send_to_webhook(data)

    def send_error(self, message, title=None, tagged_members=None):
        """
        Send a error or critical message
        :param message: String message
        :param title: Optional string title
        :param tagged_members: Optional list of slack user id
        :return:
        """
        tagged_members_list = tagged_members
        if tagged_members_list is None:
            tagged_members_list = self.slack_supervisors

        data = self._generate_message_slack(
            message, NotificationLevel.CRITICAL, title, tagged_members_list
        )

        logger.info("Sending error {}".format(message))
        self._send_to_webhook(data)
