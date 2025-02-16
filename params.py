"""Parameters file for Shipping Bot"""

import setup  # pylint: disable=unused-import, wrong-import-order
import os



service_token = os.getenv("SERVICE_TOKEN")
app_env = os.getenv("APP_ENV", "prod")

class Params:
    """Shipping Bot Parameters"""

    class SQL:
        """SQL Parameters for Shipping Bot"""

        username = os.getenv("MYSQL_USERNAME")
        password = os.getenv("MYSQL_PASSWORD")
        server = os.getenv("MYSQL_SERVER")
        port = os.getenv("MYSQL_PORT")
        database = os.getenv("MYSQL_DATABASE")

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

        server = os.getenv("EMAIL_SERVER")
        email = os.getenv("EMAIL")
        username = email
        from_email = os.getenv("FROM_EMAIL")
        password = os.getenv("EMAIL_PASSWORD")
        port = os.getenv("EMAIL_PORT")

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

        client_id = os.getenv("PAYPAL_CLIENT_ID")
        secret = os.getenv("PAYPAL_SECRET")


if __name__ == "__main__":
    print(
        """Error: This file is a module to be imported and has no functions
          to be ran directly."""
    )
    print(Params.Email.username)
