"""Parameters file for Shipping Bot"""
import setup # pylint: disable=unused-import, wrong-import-order
import os
from dotenv import load_dotenv
import infisical


load_dotenv()
service_token = os.getenv('SERVICE_TOKEN')
app_env = os.getenv('APP_ENV')
creds = infisical.InfisicalClient(token=service_token, site_url='https://creds.kumpeapps.com')

class Params:
    """Shipping Bot Parameters"""
    class SQL:
        """SQL Parameters for Shipping Bot"""
        username = creds.get_secret("USERNAME", environment=app_env, path="/MYSQL/").secret_value
        password = creds.get_secret("PASSWORD", environment=app_env, path="/MYSQL/").secret_value
        server = creds.get_secret("SERVER", environment=app_env, path="/MYSQL/").secret_value
        port = creds.get_secret("PORT", environment=app_env, path="/MYSQL/").secret_value
        database = "BOT_Data"

        def dict(): # pylint: disable=no-method-argument
            """returns as dictionary"""
            return {
                'username': Params.SQL.username,
                'password': Params.SQL.password,
                'server': Params.SQL.server,
                'port': Params.SQL.port,
                'database': Params.SQL.database
            }


    class Email:
        """Email Parameters"""
        server = creds.get_secret("SERVER", environment=app_env, path="/EMAIL/").secret_value
        email = creds.get_secret("EMAIL", environment=app_env, path="/EMAIL/").secret_value
        username = email
        from_email = creds.get_secret(
            "FROM_EMAIL", environment=app_env, path="/EMAIL/"
            ).secret_value
        password = creds.get_secret("PASSWORD", environment=app_env, path="/EMAIL/").secret_value
        port = creds.get_secret("PORT", environment=app_env, path="/EMAIL/").secret_value

        def dict(): # pylint: disable=no-method-argument
            """returns as dictionary"""
            return {
                'username': Params.Email.username,
                'email': Params.Email.email,
                'from_email': Params.Email.from_email,
                'password': Params.Email.password,
                'server': Params.Email.server,
                'port': Params.Email.port
            }
    
    class PayPal:
        """PayPal Parameters"""
        client_id = creds.get_secret("CLIENT_ID", environment=app_env, path="/PAYPAL/").secret_value
        secret = creds.get_secret("SECRET", environment=app_env, path="/PAYPAL/").secret_value


if __name__ == "__main__":
    print("""Error: This file is a module to be imported and has no functions
          to be ran directly.""")
    print(Params.Email.username)
