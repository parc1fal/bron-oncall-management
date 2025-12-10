"""
Script to extract all names from Google Sheets and list all Slack users
to help create the name_mapping.json file
"""

import ssl

# TODO: Remove this in production
ssl._create_default_https_context = ssl._create_unverified_context

from google.oauth2 import service_account
from googleapiclient.discovery import build
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")

# Configuration from .env
SERVICE_ACCOUNT_FILE = "credentials/service-account.json"
IMPERSONATE_USER = os.getenv("IMPERSONATE_USER")
SHEET_ID = os.getenv("SHEET_ID")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Sheet tab names
SHEET_TABS = ["@support.guards", "@support.dev"]


def get_sheets_service():
    """Initialize Google Sheets API service"""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES, subject=IMPERSONATE_USER
    )
    return build("sheets", "v4", credentials=credentials)


def extract_names_from_sheet(service, sheet_id, tab_name):
    """Extract all unique names from a specific sheet tab"""
    try:
        print(f"\n📖 Reading sheet tab: {tab_name}")
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=f"'{tab_name}'!A:Z")  # Read all columns
            .execute()
        )

        values = result.get("values", [])
        if not values:
            print(f"  ⚠️  No data found in {tab_name}")
            return set()

        names = set()

        # Skip header row (row 0), process data rows
        for row_idx, row in enumerate(values[1:], start=2):
            # Skip first column (dates), process remaining columns
            for col_idx, cell in enumerate(row[1:], start=1):
                if cell and cell.strip():  # Non-empty cell
                    # Clean up the cell value
                    name = cell.strip()
                    # Skip time ranges or other non-name patterns
                    if ":" not in name and "-" not in name:
                        names.add(name)

        print(f"  ✓ Found {len(names)} unique names")
        return names

    except Exception as e:
        print(f"  ❌ Error reading {tab_name}: {e}")
        return set()


def get_slack_users(token):
    """Get all users from Slack workspace"""
    try:
        print("\n👥 Fetching Slack users...")
        client = WebClient(token=token)

        response = client.users_list()
        users = response["members"]

        # Filter out bots and deleted users
        real_users = []
        for user in users:
            if not user.get("deleted", False) and not user.get("is_bot", False):
                real_users.append(
                    {
                        "id": user["id"],
                        "real_name": user.get("real_name", ""),
                        "display_name": user.get("profile", {}).get("display_name", ""),
                        "email": user.get("profile", {}).get("email", ""),
                    }
                )

        print(f"  ✓ Found {len(real_users)} real users (excluding bots)")
        return real_users

    except SlackApiError as e:
        print(f"  ❌ Slack API Error: {e.response['error']}")
        return []
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def main():
    print("=" * 60)
    print("Name Extraction Tool for Mapping")
    print("=" * 60)

    # Get names from Google Sheets
    print("\n📊 Extracting names from Google Sheets...")

    sheets_service = get_sheets_service()
    all_sheet_names = set()

    for tab in SHEET_TABS:
        names = extract_names_from_sheet(sheets_service, SHEET_ID, tab)
        all_sheet_names.update(names)

    # Get users from Slack
    print("\n💬 Fetching users from Slack...")
    slack_users = get_slack_users(SLACK_BOT_TOKEN)

    # Output results
    print("\n" + "=" * 60)
    print("📋 RESULTS")
    print("=" * 60)

    print("\n🔹 UNIQUE NAMES FROM GOOGLE SHEETS:")
    print("-" * 60)
    for name in sorted(all_sheet_names):
        print(f"{name}")

    print(f"\nTotal: {len(all_sheet_names)} unique names")

    print("\n\n🔹 SLACK USERS (User ID → Name):")
    print("-" * 60)
    slack_users_sorted = sorted(slack_users, key=lambda x: x["real_name"])
    for user in slack_users_sorted:
        print(f"{user['id']} → {user['real_name']}")
        if user["display_name"] and user["display_name"] != user["real_name"]:
            print(f"  (Display name: {user['display_name']})")
        if user["email"]:
            print(f"  (Email: {user['email']})")

    print(f"\nTotal: {len(slack_users)} users")

    print("\n" + "=" * 60)
    print("✅ DONE! Use the lists above to create your name mapping.")
    print("=" * 60)


if __name__ == "__main__":
    main()
