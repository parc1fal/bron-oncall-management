"""
Main script for on-call bot.
Fetches current on-call from Google Sheets and updates Slack user group if changed.
"""

from src.config import config
from src.sheets_parser import SheetsParser
from src.slack_client import SlackClient


def main():
    parser = SheetsParser()
    slack = SlackClient()

    oncall = parser.get_all_current_oncall()
    new_ids = {config.get_slack_user_id(name) for name in oncall.values()}

    current_ids = slack.get_usergroup_members() - {config.bot_uid}

    if current_ids == new_ids:
        print("No change needed")
        return

    slack.update_usergroup_members(new_ids | {config.bot_uid})

    names = list(oncall.values())
    slack.post_message(f"On-call updated: {names[0]} (guards), {names[1]} (dev)")

    uid_to_name = {v: k for k, v in config.name_mapping.items()}
    current_names = [uid_to_name.get(uid, uid) for uid in current_ids]

    # test message to @egor.kuzmichev
    slack.client.chat_postMessage(
        channel="U09LW8UT3SN",
        text=f"TEST - On-call change:\nBefore: {current_names}\nAfter: {names}",
    )

    print(f"Updated on-call: {oncall}")


if __name__ == "__main__":
    main()
