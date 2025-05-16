import base64
import string
import random
import logging

from config.logging_conf import setup_logging
from exceptions.otp import WrongOTPException, NotFoundOTPException, SendOtpException
from logic.utils.redis.main import Redis
from logic.utils.email.message import send_email
from config.settings import FRONT_HOST
logger = logging.getLogger(__name__)
setup_logging(__name__)


class OTP:
    OTP_LENGTH = 6

    def __init__(self, email, key='otp'):
        self.email = email
        self.key = email + ':' + key

    def encrypt_verify(self, code_auth):
        # Соединяем email и код через разделитель "::"
        data = f"{self.email}::{code_auth}"
        # Кодируем строку в Base64
        encoded = base64.urlsafe_b64encode(data.encode()).decode()
        return encoded

    @staticmethod
    async def generate_otp(length: int = OTP_LENGTH) -> str:
        """
        Generates an OTP of specified length
        """
        return ''.join(random.choices(string.digits, k=length))

    def create_link(self, code: str):
        encoded = str(self.encrypt_verify(code))
        return f"{FRONT_HOST}/registration?verify={encoded}"

    async def save_otp(self, otp: str = None) -> bool:
        """
        Saves the OTP in Redis and returns True if successful.
        """
        if otp is None:
            otp = await self.generate_otp()

        try:

            await Redis.save(self.key, otp, time_expired=60 * 5)
            logger.debug(f"{self.email}: OTP - saved")
            return True
        except Exception as e:
            logger.error(f"{self.email}: error on saving OTP - {e}", exc_info=True)
            return False

    async def verify_otp(self, otp: str) -> bool:
        """
        Verifies the provided OTP against the one in Redis.
        """
        actual_otp = await Redis.get(self.key)
        if actual_otp:
            if str(actual_otp) == str(otp):
                logger.debug(f"{self.email}: OTP - confirmed")
                return True
            else:
                raise WrongOTPException
        else:
            logger.debug(f"{self.email}: OTP - not found")
            raise NotFoundOTPException

    async def send_otp(self, code=None):
        """
        Sends otp to recipient.
        """
        if code is None:
            code = await self.generate_otp()

        link = self.create_link(code)
        email_body = {
            "subject": "Verification code",
            "message": f'Your verification link: <a href="{link}">Verify</b>',
            "recipient": self.email
        }

        try:
            send_email(**email_body)

        except Exception as e:
            logger.error(f"{self.email} failed to send otp. Error - {e}")
            raise SendOtpException

