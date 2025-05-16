from dataclasses import dataclass
from logic.requester.base import Requestor


@dataclass
class GoogleTokenRequestor(Requestor):
    url: str = 'https://oauth2.googleapis.com/token'
    method: str = "post"
