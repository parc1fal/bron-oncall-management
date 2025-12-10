from src.slack_client import SlackClient

client = SlackClient()
members = client.get_usergroup_members()
print(members)
