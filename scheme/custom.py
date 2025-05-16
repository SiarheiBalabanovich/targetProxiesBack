from fastapi.param_functions import Form
from typing_extensions import Annotated, Doc


class OAuth2PasswordRequestForm:

    def __init__(
        self,
        email: Annotated[
            str,
            Form(),
            Doc(
                """
                `email` string. The OAuth2 spec requires the exact field name
                `email`.
                """
            ),
        ],
        password: Annotated[
            str,
            Form(),
            Doc(
                """
                `password` string. The OAuth2 spec requires the exact field name
                `password".
                """
            ),
        ],
    ):
        self.email = email
        self.password = password
