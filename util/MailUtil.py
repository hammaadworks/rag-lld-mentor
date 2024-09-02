from email.mime.text import MIMEText
from smtplib import SMTP

SMTP_HOST = 'xiaomiindia.mailmi.in'
SMTP_PORT = 465

USERNAME = "migpt@mailmi.in"
PASSWORD = ''.join(["Pa", "ss", "wo", "rd1"])
SENDER = "migpt@mailmi.in"

TEXT_SUBTYPE = 'plain'
SUBJECT = "Reset code for CSGPT Login"

CONTENT = "Your reset code is: {}"


def send_reset_code_mail(receiver: str, reset_code: str):
    try:
        msg = MIMEText(CONTENT.format(reset_code), TEXT_SUBTYPE)
        msg['Subject'] = SUBJECT
        msg['From'] = SENDER

        conn = SMTP(SMTP_HOST)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(SENDER, [receiver], msg.as_string())
        finally:
            conn.quit()
            print("Done")

    except Exception as e:
        print(f"Exception occurred in send_reset_code_mail>> {str(e)}")


if __name__ == "__main__":
    send_reset_code_mail("nasir@mailmi.in", "ABCDE")
