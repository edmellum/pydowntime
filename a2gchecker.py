#!/usr/bin/env python
"""
Author: David Mellum
Checks a list of websites to see if they are up.
If one is down an email is sent to the recievers set in the script.
A flatfile and JSON is used to store wether the site was down last time the
check was done so as to avoid spamming the email recievers.
Run this as a cron job at regular intervals.
"""

# You can change this. It's safe. No really. It is.
targets = ["example.com"]

email_recipients = ["contact@example.com"]

error_limit = 4

smtp_server = "mail.example.com"
email_address = "downtime@example.com"
email_subject = "Website downtime"

db_location = "a2gchecker.db"

DEBUG = False

# OK now stop editing or you'll get electrocuted.

if DEBUG == True:
    email_recipients = ["debug@example.com"]
    targets.append("example.com/500")

import urllib2
import json
import smtplib
import time
from email.mime.text import MIMEText

def db_reset(db_path):
    """Make a new DB file with an empty JSON object in it.
    This will overwrite any already existing files too.
    
    >>> db_reset("testdatabase.db")
    """
    
    file = open(db_path, "w")
    file.write("{}")
    file.close()

def log(message, severity="notice", log_path="a2gchecker.log"):
    """Adds the supplied message to a logfile formatted as JSON for readability and parseability.
    
    Does not use append mode, so a crash or weird error could asplode the log file.
    
    >>> log("User did something naughty.", "naughtylist.log")
    """
    try:
        file = open(log_path, "r")
    # If file doesn't exist create a new one.
    except IOError:
        file = open(log_path, "w")
        file.write("[]")
        file.close()
        file = open(log_path, "r")

    try:
        json_log = json.loads(file.read())
    # Reset file to a simple JSON array if the current JSON is unparseable.
    except ValueError:
        file.close()
        file = open(log_path, "w")
        file.write("[]")
        file.close()
        file = open(log_path, "r")
        json_log = json.loads(file.read())
    
    file.close()
    
    entry = [
        time.strftime("%a %b %d %H:%M:%S %Y"),
        severity,
        message
    ]
    
    print entry
    
    json_log.append(entry)
    
    json_log = json.dumps(json_log, indent=4)
    
    file = open(log_path, "w")
    file.write(json_log)
    file.close()

def send_mails(subject, body, recievers):
    """Sends emails to the supplied recievers with the supplied subject and body.
    
    For now the "From" email address is hardcoded.
    
    >>> send_emails("Check out these HILARIOUS pics!", "LOL these cats are so funneh.", ["billy@aol.com", "hollar@garry.com"])
    """
    mail = MIMEText(body)
    mail["Subject"] = subject
    mail["From"] = email_address
    
    s = smtplib.SMTP()
    s.connect(smtp_server)
    for reciever in recievers:
        mail["to"] = reciever
        s.sendmail(email_address, reciever, mail.as_string())
    s.quit()

def main():

    try:
        file = open(db_location, "r")
    except IOError:
        db_reset(db_location)
        file = open(db_location, "r")
    
    try:
        json_file = json.loads(file.read())
    except ValueError:
        file.close()
        db_reset(db_location)
        file = open(db_location, "r")
        json_file = json.loads(file.read())
    
    file.close()
    
    for target in targets:
        try:
            pingaling = urllib2.urlopen("http://"+target)
            
            if not target in json_file or json_file[target] > 0:
                json_file[target] = 0
            
        except (urllib2.HTTPError, urllib2.URLError), e:
            
            msg = "Kunne ikke finne " + target
            if hasattr(e, "code"):
                msg += ' HTTP error code: "' + str(e.code) + " " + e.msg + '"'
            elif hasattr(e, "reason"):
                msg += ' Reason: "' + str(e.reason) + '"'
            
            if not target in json_file:
                json_file[target] = 1
                
                log(msg, 1)
            
            elif json_file[target] >= 0:
                json_file[target] += 1
                
                log(msg, json_file[target])
            
            if json_file[target] == error_limit:
                
                log(msg, error_limit)
                send_mails(email_subject, msg, email_recipients)
            
    file = open("a2gchecker.db", "w")
    file.write(json.dumps(json_file))
    file.close()

if __name__ == "__main__":
    main()
