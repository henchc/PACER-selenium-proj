def send_email(email_address, password, recipient, subject, body):
    '''
    send email using gmail
    http://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python
    '''
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

    import csv
    with open('distlogin.csv', 'r', encoding="utf-8") as f:
        reader = csv.reader(f)
        distlogin_csv = list(reader)

    email_address = distlogin_csv[0][0]
    email_password = distlogin_csv[0][1]

    send_email(email_address,
               email_password,
               email_address,
               "stopped",
               "Python stopped.")
