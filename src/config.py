"""
Configuration loader for the on-call bot.
Loads environment variables and configuration files.
"""

import os
import json
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv


load_dotenv("config/.env")


class Config:
    """Configuration class for the on-call bot."""

    def __init__(self):
        self.google_sheet_id = self._get_env("GOOGLE_SHEET_ID")
        self.google_credentials_path = self._get_env("GOOGLE_CREDENTIALS_PATH")
        self.impersonate_user = self._get_env("IMPERSONATE_USER")

        self.slack_bot_token = self._get_env("SLACK_BOT_TOKEN")
        self.slack_user_group_id = self._get_env("SLACK_USER_GROUP_ID")
        self.slack_channel_id = self._get_env("SLACK_CHANNEL_ID")

        self.check_interval_minutes = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))

        self.timezone = "Europe/London"
        self.sheet_names = ["@support.guards", "@support.dev"]
        self.name_mapping = self._load_name_mapping()
        self.bot_uid = self._get_env("BOT_UID")

    @staticmethod
    def _get_env(key: str) -> str:
        """Get environment variable or raise error if not found."""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Environment variable {key} is not set")
        return value

    def _load_name_mapping(self) -> Dict[str, str]:
        """Load name mapping from JSON file."""

        docker_path = Path("/app/config/name_mapping.json")
        local_path = Path(__file__).parent.parent / "config" / "name_mapping.json"

        if docker_path.exists():
            mapping_path = docker_path
        elif local_path.exists():
            mapping_path = local_path
        else:
            raise FileNotFoundError(
                f"name_mapping.json not found at {docker_path} or {local_path}"
            )

        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        print(f"Loaded name mapping from {mapping_path}")
        return mapping

    def get_slack_user_id(self, name: str) -> str:
        """Get Slack user ID for a given name."""
        if name not in self.name_mapping:
            raise ValueError(f"Name '{name}' not found in name_mapping.json")
        return self.name_mapping[name]


config = Config()
