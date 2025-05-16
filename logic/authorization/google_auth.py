from dataclasses import dataclass
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest

from logic.requester.google import GoogleTokenRequestor
from config.settings import (
    CLIENT_ID,
    CLIENT_SECRET,
    GOOGLE_REDIRECT_URL,
)


@dataclass
class OauthService:
    @staticmethod
    async def get_google_token(code: str):
        data = {
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': GOOGLE_REDIRECT_URL,
            'grant_type': 'authorization_code',
        }
        requestor = GoogleTokenRequestor(params=data)
        response = await requestor()
        return response.get('id_token')

    async def get_user_google(self, code: str):
        id_token_value = await self.get_google_token(code)
        if id_token_value:
            try:
                google_user = {
                    "user": id_token.verify_oauth2_token(
                        id_token=id_token_value,
                        request=GoogleRequest(),
                        audience=CLIENT_ID,
                    )
                }
            except ValueError as e:
                google_user = {
                    "error": f"Invalid id_token: {str(e)}"
                }

            return google_user
        return {
            "error": "Missing id_token in response."
        }

    async def get_token_from_google_callback(self, code: str):
        google_user_response = await self.get_user_google(code)

        if google_user := google_user_response.get("user"):
            return google_user

        return {
            "token_error": google_user_response.get("error"),
        }
