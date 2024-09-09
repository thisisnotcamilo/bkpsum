#! /bin/python3

# @thisisnotcamilo

import os
import pytz
import smtplib
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(service, folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents and name starts with 'RO_'",
        pageSize=1000,
        fields="nextPageToken, files(id, name, modifiedTime)"
    ).execute()
    return results.get('files', [])

def format_email_summary(files):
    now = datetime.now(pytz.utc)
    seven_days_ago = now - timedelta(days=7)
    
    recent_files = []
    older_files = []
    
    for file in files:
        modified_time = datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00'))
        if modified_time > seven_days_ago:
            recent_files.append(file)
        else:
            older_files.append(file)
    
    summary = "Here's the weekly summary of the router backups:\n\n"
    
    if older_files:
        summary += "# Files not updated recently:\n"
        for file in older_files:
            modified_time = datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00'))
            summary += f"- {file['name']} (Last modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S %Z')})\n"
        summary += "\nPlease review these files as they haven't been updated in the last 7 days.\n\n"

    summary += "---\n\n"

    if recent_files:
        summary += "# Recently updated files (Last 7 Days):\n"
        for file in recent_files:
            modified_time = datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00'))
            summary += f"- {file['name']} (Last modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S %Z')})\n"
        summary += "\n"
    
    return summary

def send_email(subject, body, sender_email, sender_password, receiver_email):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"An error occurred while sending the email: {e}")

def main():
    service = get_drive_service()
    
    folder_id = os.getenv("FOLDER_ID")
    
    files = list_files_in_folder(service, folder_id)
    
    if not files:
        logger.warning("No router backups found.")
    else:
        email_body = format_email_summary(files)
        
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        receiver_email = os.getenv("RECEIVER_EMAIL")
        subject = os.getenv("SUBJECT_EMAIL")
        
        send_email(subject, email_body, sender_email, sender_password, receiver_email)

if __name__ == "__main__":
    main()
