import ctypes
import json
import logging

import pyotp
from pywinauto import Application

logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

PARAM_CONFIG_FILENAME = 'ODISAuth_config.json'
PROVIDE_CREDENTIALS_BUTTON_TITLE = 'ВХОД ПО ЛОГИНУ / ПАРОЛЮ'
USE_TOTP_BUTTON_TITLE = 'ВХОД С TOTP'
CHECK_TOTP_BUTTON_TITLE = 'ПРОВЕРИТЬ'


class ODISAuth:
    def __init__(self):
        self.login = None
        self.password = None
        self.totp_secure = None

    def load_config(self):
        try:
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
            if is_admin is False:
                raise ValueError('admin rights required')

            try:
                with open(PARAM_CONFIG_FILENAME, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f'file {PARAM_CONFIG_FILENAME} wasnt found in the current path'
                )

            self.login = config.get('ODIS_LOGIN')
            self.password = config.get('ODIS_PASSWORD')
            self.totp_secure = config.get('TOTP_SECURE')
            availability_dict = dict(
                ODIS_LOGIN=self.login,
                ODIS_PASSWORD=self.password,
                TOTP_SECURE=self.totp_secure
            )
            unavailable_params = [k for k, v in availability_dict.items() if v is None]
            if unavailable_params:
                if len(unavailable_params) == 1:
                    raise ValueError(
                        f'param {unavailable_params[0]} is unfilled'
                    )
                else:
                    raise ValueError(
                        f'params {unavailable_params} are unfilled'
                    )
        except Exception as e:
            logging.error(str(e))
            return

    def run_login(self):
        try:
            app = Application(backend='uia').connect(title_re='Offboard Diagnostic Information System.*')
            window = app.window(title_re='Offboard Diagnostic Information System.*')

            username_field = window.child_window(auto_id='username', control_type='Edit')
            password_field = window.child_window(auto_id='password', control_type='Edit')
            login_button = window.child_window(title=PROVIDE_CREDENTIALS_BUTTON_TITLE, control_type='Button')
        except Exception:
            logging.error('ODIS login fields are not found')
            return
        username_field.set_text(self.login)
        password_field.set_text(self.password)
        login_button.click()

        try:
            totp_button = window.child_window(title=USE_TOTP_BUTTON_TITLE, control_type='Button')
        except Exception:
            logging.error(f'invalid credentials provided in {PARAM_CONFIG_FILENAME}')
            return
        totp_button.click()

        try:
            otp_field = window.child_window(auto_id='otp', control_type='Edit')
            check_otp_button = window.child_window(title=CHECK_TOTP_BUTTON_TITLE, control_type='Button')
        except Exception:
            logging.error('OTP parameters are not found on the screen')
            return
        try:
            current_totp_value = pyotp.TOTP(self.totp_secure).now()
        except Exception as error:
            logging.error(f'invalid TOTP secret: {error}')
            return
        otp_field.set_text(current_totp_value)
        check_otp_button.click()


if __name__ == '__main__':
    odis_auth = ODISAuth()
    odis_auth.load_config()
    odis_auth.run_login()
