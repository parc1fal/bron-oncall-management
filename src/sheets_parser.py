"""
Google Sheets parser for fetching current on-call staff.
"""

from datetime import datetime, time, timedelta
from typing import Optional, List, Tuple
import pytz

from google.oauth2 import service_account
from googleapiclient.discovery import build

from src.config import config


# Time slots: column -> (start, end)
GUARDS_SLOTS = {
    1: (time(9, 0), time(13, 30)),
    2: (time(13, 30), time(18, 0)),
    3: (time(18, 0), time(9, 0)),
}

DEV_SLOTS = {
    1: (time(3, 0), time(6, 0)),
    2: (time(6, 0), time(3, 0)),
}


def is_time_between(begin: time, end: time, check: time) -> bool:
    """Check if check time falls within begin-end range."""
    if begin < end:
        return begin <= check <= end
    else:
        # Crosses midnight
        return check >= begin or check <= end


def find_column(slots: dict, check_time: time) -> Tuple[Optional[int], bool]:
    """
    Find which column matches the current time.

    Returns:
        (column_index, use_previous_day)
    """
    for col, (begin, end) in slots.items():
        if is_time_between(begin, end, check_time):
            overnight = begin > end
            use_previous_day = overnight and check_time <= end
            return col, use_previous_day
    return None, False


class SheetsParser:

    def __init__(self):
        self.sheet_id = config.google_sheet_id
        self.tz = pytz.timezone(config.timezone)
        self.service = self._build_service()

    def _build_service(self):
        """Build Google Sheets API service with domain-wide delegation."""
        credentials = service_account.Credentials.from_service_account_file(
            config.google_credentials_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
            subject=config.impersonate_user,
        )
        return build("sheets", "v4", credentials=credentials)

    def _get_sheet_data(self, sheet_name: str) -> List[List]:
        """Fetch all data from a sheet."""
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=f"'{sheet_name}'!A:D")
            .execute()
        )
        return result.get("values", [])

    def _find_row_for_date(self, rows: List[List], target_date) -> Optional[int]:
        """Find the row index for a specific date."""
        for idx, row in enumerate(rows):
            if not row:
                continue
            cell = row[0]
            if isinstance(cell, str):
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        if datetime.strptime(cell, fmt).date() == target_date:
                            return idx
                    except ValueError:
                        continue
        return None

    def get_current_oncall(self, sheet_name: str) -> Optional[str]:
        """Get the name of the person currently on call for a given sheet."""
        now = datetime.now(self.tz)

        slots = GUARDS_SLOTS if sheet_name == "@support.guards" else DEV_SLOTS

        col, use_previous_day = find_column(slots, now.time())

        if col is None:
            return None

        lookup_date = now.date() - timedelta(days=1) if use_previous_day else now.date()

        rows = self._get_sheet_data(sheet_name)
        row_idx = self._find_row_for_date(rows, lookup_date)

        if row_idx is None:
            return None

        row = rows[row_idx]
        if len(row) <= col:
            return None

        name = row[col]
        return name.strip() if name else None

    def get_all_current_oncall(self) -> dict:
        """Get all currently on-call personnel across both sheets."""
        return {
            sheet_name: self.get_current_oncall(sheet_name)
            for sheet_name in config.sheet_names
        }
