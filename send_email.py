def send_email(email_address, password, recipient, subject, body):
***REMOVED***
    send email using gmail
    http://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python
***REMOVED***
    import smtplib

    FROM = email_address
    TO = recipient if isinstance(recipient, list) else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    # SMTP_SSL Example
    server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server_ssl.ehlo()  # optional, called by login()
    server_ssl.login(email_address, password)
    # ssl server doesn't support or need tls, so don't call
    # server_ssl.starttls()
    server_ssl.sendmail(FROM, TO, message)
    # server_ssl.quit()
    server_ssl.close()
    print('successfully sent email')

if __name__ == "__main__":

    ***REMOVED***
    ***REMOVED***
    ***REMOVED***
    ***REMOVED***

    ***REMOVED***
    ***REMOVED***

    send_email(email_address,
               email_password,
               email_address,
               "stopped",
               "Python stopped.")
