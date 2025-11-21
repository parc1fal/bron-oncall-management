"""
Slack client for managing user groups.
"""

from typing import Set
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.config import config

import ssl

# TODO: Remove this in production
ssl._create_default_https_context = ssl._create_unverified_context


class SlackClient:

    def __init__(self):
        self.client = WebClient(token=config.slack_bot_token)
        self.usergroup_id = config.slack_user_group_id
        self.channel_id = config.slack_channel_id

    def get_usergroup_members(self) -> Set[str]:
        response = self.client.usergroups_users_list(usergroup=self.usergroup_id)
        return set(response.get("users", []))

    def update_usergroup_members(self, user_ids: Set[str]):
        self.client.usergroups_users_update(
            usergroup=self.usergroup_id,
            users=list(user_ids),
        )

    def post_message(self, text: str):
        self.client.chat_postMessage(
            channel=self.channel_id,
            text=text,
        )
