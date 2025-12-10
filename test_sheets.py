from src.sheets_parser import SheetsParser

parser = SheetsParser()
now_oncall = parser.get_all_current_oncall()
print(now_oncall)
