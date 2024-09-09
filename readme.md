`bkpsum` brings you the weekly summary of your backups status.

1. Create .env file:
```
# gdrive folder id to monitor
FOLDER_ID="" 

# email configuration
SENDER_EMAIL="mail@gmail.com"
SENDER_PASSWORD="password"
RECEIVER_EMAIL="example@domain.com"
SUBJECT_EMAIL="Backup Monitor - Summary of backups in Google Drive"
```

2. Then:
```sh
$ python3 -m venv env
$ . env/bin/activate
$ pip3 install -r requirements.txt
$ python3 bkpsum.py
```
