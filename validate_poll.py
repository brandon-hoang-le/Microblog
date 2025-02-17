import smtplib
import greenstalk
import configparser
import requests
import re
import sqlite_utils
import json

config = configparser.ConfigParser()
config.read("./etc/users.ini")
client = greenstalk.Client(('127.0.0.1', 11300),watch="polls")

def getUserEmail(db, username):
        email_user_generator= db["users"].rows_where("username = :username", {"username": username}, select='email_address')
        email_user_dict = next(email_user_generator)
        email_user = email_user_dict["email_address"]
        return email_user

def post_loop():
    client.use("polls")
    dbfile = config["sqlite"]["dbfile"]
    db = sqlite_utils.Database(dbfile)
    while True:
        try:
            job = client.reserve()
            body = json.loads(job.body)
            validate = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", body["text"])

            if len(validate) != 0:
                validate = validate[0]
                split = validate.rsplit('/')
                id = split[len(split)-1]
                if (split[len(split)-2] == "polls"):
                    r = requests.get("http://localhost:8000/polls/" + id)
                    print(r.status_code)
                    if r.status_code != 200:
                        msg = "Invalid poll"
                        # python3 -m smtpd -n -c DebuggingServer localhost:1025
                        fromaddr = "test@gmail.com"
                        toaddrs = getUserEmail(db, body["username"])
                        server = smtplib.SMTP('localhost', 1025)
                        server.set_debuglevel(1)
                        server.sendmail(fromaddr, toaddrs, msg)
                        server.quit()
        except:
            None
        client.delete(job)

if __name__ == "__main__":
    post_loop()

