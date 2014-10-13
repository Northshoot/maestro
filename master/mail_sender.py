'''
Created on 23 juin 2013
Function to write a e-mail
@author: dgourillon
'''


import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os
import time

gmail_user = "mail.ccmd@gmail.com"
gmail_pwd = "dgourillon"

# Function to write an e-mail
def mail(to, subject, text, attach):
    bool_done = False
    while (not bool_done):
        try :
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = to
            msg['Subject'] = subject

    	    msg.attach(MIMEText(text))

    	    part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attach, 'rb').read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition',
               'attachment; filename="%s"' % os.path.basename(attach))
            msg.attach(part)

            mailServer = smtplib.SMTP("smtp.gmail.com", 587)
            mailServer.ehlo()
            mailServer.starttls()
            mailServer.ehlo()
            mailServer.login(gmail_user, gmail_pwd)
            mailServer.sendmail(gmail_user, to, msg.as_string())
            # Should be mailServer.quit(), but that crashes...
            mailServer.close()
	    bool_done = True
	except Exception as e:
	    print 'mail server not ready => ', str(e)
	    time.sleep(5)
