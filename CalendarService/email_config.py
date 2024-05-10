from fastapi_mail import ConnectionConfig
import os
from dotenv import load_dotenv
from string import Template

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME =os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_USERNAME"),
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp-mail.outlook.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

template = Template(
    """
    <p>
    Hello $client_name,<br>
    The keycode for opening the door is <span style="font:bold">$key</span>.<br>
    <br>
    Hope you enjoy your stay from $begin_time to $end_time!<br>
    <br>
    PropertEase
    </p> 
    """
)