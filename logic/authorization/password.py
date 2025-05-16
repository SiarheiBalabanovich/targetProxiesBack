from logic.utils.redis.main import Redis
from logic.utils.email.message import send_email
from logic.utils.authorization.password import PasswordManager

from exceptions.email import SendingEmailException, BaseAppException


class RecoverPassword:
    def __init__(self, email):
        self.email = email

    async def send_recover_url(self):
        link, uid = PasswordManager.generate_link_recover()

        await Redis.save(str(uid), self.email, 60 * 60 * 24)

        body_email = {
            "subject": f"We received a request to reset the password for the TargetedProxies account associated with {self.email}",
            "message": f'<a href="{link}">Reset your password</a>. Link will be active for 24 hours',
            "recipient": self.email
        }
        try:
            send_email(**body_email)
        except Exception as e:
            raise SendingEmailException

    @staticmethod
    async def verify_user(uid):
        user_mail = await Redis.get(uid)

        if user_mail is None:
            raise BaseAppException(status_code=404, detail="Link not found (expired or wrong)")

        return user_mail
