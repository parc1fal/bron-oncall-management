"""
Simple test script to verify Slack API access and retrieve user group IDs
"""

import ssl
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the config directory
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# TODO: Remove this in production
ssl._create_default_https_context = ssl._create_unverified_context

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    print(f"❌ Looking for .env file at: {env_path}")
    print(f"   File exists: {env_path.exists()}")
    raise ValueError("SLACK_BOT_TOKEN environment variable is not set")


def test_slack_access():
    try:
        print("🔐 Initializing Slack client...")
        client = WebClient(token=SLACK_BOT_TOKEN)

        print("\n✓ Testing API connection...")
        response = client.auth_test()
        print(f"✅ Connected to workspace: {response['team']}")
        print(f"   Bot user: {response['user']}")
        print(f"   Bot ID: {response['user_id']}")

        print("\n📋 Fetching user groups...")
        usergroups = client.usergroups_list()

        if usergroups["usergroups"]:
            print(f"\n✅ Found {len(usergroups['usergroups'])} user groups:")
            for group in usergroups["usergroups"]:
                print(f"\n  Name: @{group['handle']}")
                print(f"  ID: {group['id']}")
                print(f"  Description: {group.get('description', 'N/A')}")
        else:
            print(
                "\n⚠️  No user groups found. You may need to create @support.guards and @support.dev"
            )

        print("\n✅ SUCCESS! Slack API access working!")

    except SlackApiError as e:
        print(f"\n❌ Slack API Error: {e.response['error']}")
        print("\nTroubleshooting:")
        print("1. Check your SLACK_BOT_TOKEN is correct")
        print("2. Verify the bot is installed to your workspace")
        print(
            "3. Check bot permissions include: usergroups:read, chat:write, users:read"
        )
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    print("=== Slack API Access Test ===\n")
    test_slack_access()
