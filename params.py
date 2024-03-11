"""Parameters file for Shipping Bot"""

import setup  # pylint: disable=unused-import, wrong-import-order
import os
from dotenv import load_dotenv
from infisical_api import infisical_api


load_dotenv()
service_token = os.getenv("SERVICE_TOKEN")
app_env = os.getenv("APP_ENV")
creds = infisical_api(
    service_token=service_token, infisical_url="https://creds.kumpeapps.com"
)


class Params:
    """Shipping Bot Parameters"""

    class SQL:
        """SQL Parameters for Shipping Bot"""

        username = creds.get_secret(  # pylint: disable=no-member
            "USERNAME", environment=app_env, path="/MYSQL/"
        ).secretValue
        password = creds.get_secret(  # pylint: disable=no-member
            "PASSWORD", environment=app_env, path="/MYSQL/"
        ).secretValue
        server = creds.get_secret(  # pylint: disable=no-member
            "SERVER", environment=app_env, path="/MYSQL/"
        ).secretValue
        port = creds.get_secret(  # pylint: disable=no-member
            "PORT", environment=app_env, path="/MYSQL/"
        ).secretValue
        database = "BOT_Data"

        def dict():  # pylint: disable=no-method-argument
            """returns as dictionary"""
            return {
                "username": Params.SQL.username,
                "password": Params.SQL.password,
                "server": Params.SQL.server,
                "port": Params.SQL.port,
                "database": Params.SQL.database,
            }

    class Email:
        """Email Parameters"""

        server = creds.get_secret(  # pylint: disable=no-member
            "SERVER", environment=app_env, path="/EMAIL/"
        ).secretValue
        email = creds.get_secret(  # pylint: disable=no-member
            "EMAIL", environment=app_env, path="/EMAIL/"
        ).secretValue
        username = email
        from_email = creds.get_secret(  # pylint: disable=no-member
            "FROM_EMAIL", environment=app_env, path="/EMAIL/"
        ).secretValue
        password = creds.get_secret(  # pylint: disable=no-member
            "PASSWORD", environment=app_env, path="/EMAIL/"
        ).secretValue
        port = creds.get_secret(  # pylint: disable=no-member
            "PORT", environment=app_env, path="/EMAIL/"
        ).secretValue

        def dict():  # pylint: disable=no-method-argument
            """returns as dictionary"""
            return {
                "username": Params.Email.username,
                "email": Params.Email.email,
                "from_email": Params.Email.from_email,
                "password": Params.Email.password,
                "server": Params.Email.server,
                "port": Params.Email.port,
            }

    class PayPal:
        """PayPal Parameters"""

        client_id = creds.get_secret(  # pylint: disable=no-member
            "CLIENT_ID", environment=app_env, path="/PAYPAL/"
        ).secretValue
        secret = creds.get_secret(  # pylint: disable=no-member
            "SECRET", environment=app_env, path="/PAYPAL/"
        ).secretValue


if __name__ == "__main__":
    print(
        """Error: This file is a module to be imported and has no functions
          to be ran directly."""
    )
    print(Params.Email.username)
