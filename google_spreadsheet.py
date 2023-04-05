import sys
import time
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
GDOCS_OAUTH_JSON       = 'google-auth.json'
# Google Docs spreadsheet name.
GDOCS_SPREADSHEET_NAME = 'rpi-log'
FREQUENCY_SECONDS      = 3
worksheet = None
def login_open_sheet(oauth_key_file, spreadsheet):
    global worksheet
    """Connect to Google Docs spreadsheet and return the first worksheet."""
    try:
        scope =  ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, scope)
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet).sheet1
        return worksheet
    except Exception as ex:
        print('Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!')
        print('Google sheet login failed with error:', ex)
        sys.exit(1)

def submitLogtoSheet(commnad_string, submit_from):
    iteration = 0
    while True:
        # Login if necessary.
        global worksheet
        if worksheet is None:
            worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

        # Append/Insert the data in the spreadsheet, including a timestamp
        try:
            worksheet.insert_row((datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                  commnad_string, submit_from), 1)
        except:
            # Error appending data, most likely because credentials are stale.
            # Null out the worksheet so a login is performed at the top of the loop.
            print('Insert error, logging in again')
            worksheet = None
            iteration += 1
            if iteration == 3:
                return False
            time.sleep(FREQUENCY_SECONDS)
            continue
            
        print('Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME))
        return True