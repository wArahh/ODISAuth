import ctypes
import json
import logging
import os
import sys
import time

import pyotp
import win32api
import win32event
import winerror
from pywinauto import Application
from pywinauto.timings import Timings

sys.stderr = open(os.devnull, 'w')
sys.stdout = open(os.devnull, 'w')
ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8007)

logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

Timings.window_find_timeout = 30
Timings.after_click_wait = 1

PARAM_CONFIG_FILENAME = 'ODISAuth_config.json'
PROVIDE_CREDENTIALS_BUTTON_TITLE = 'ВХОД ПО ЛОГИНУ / ПАРОЛЮ'
USE_TOTP_BUTTON_TITLE = 'ВХОД С TOTP'
CHECK_TOTP_BUTTON_TITLE = 'ПРОВЕРИТЬ'

MUTEX_NAME = "Global\\ODISAuthMutex"


class ODISAuth:
    def __init__(self):
        self.login = None
        self.password = None
        self.totp_secure = None
        self.mutex = None

    def create_mutex(self):
        self.mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            logging.error('already running')
            return False
        return True

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
            return False

    def run_login(self):
        try:
            app = Application(backend='uia').connect(title_re='Offboard Diagnostic Information System.*')
            window = app.window(title_re='Offboard Diagnostic Information System.*')
        except Exception:
            logging.error('ODIS is not running')
            return False

        try:
            username_field = window.child_window(auto_id='username', control_type='Edit')
            password_field = window.child_window(auto_id='password', control_type='Edit')
            login_button = window.child_window(title=PROVIDE_CREDENTIALS_BUTTON_TITLE, control_type='Button')

            username_field.set_text(self.login)
            password_field.set_text(self.password)
            login_button.click()
        except Exception:
            logging.error('ODIS login fields are not found')
            return False

        try:
            totp_button = window.child_window(title=USE_TOTP_BUTTON_TITLE, control_type='Button')

            totp_button.click()
        except Exception:
            logging.error('TOTP button is not found')
            return False

        try:
            otp_field = window.child_window(auto_id='otp', control_type='Edit')
            check_otp_button = window.child_window(title=CHECK_TOTP_BUTTON_TITLE, control_type='Button')

            totp = pyotp.TOTP(self.totp_secure)
            remaining_time = totp.interval - (int(time.time()) % totp.interval)
            if remaining_time < 5:
                time.sleep(remaining_time + 1)

            otp_field.set_text(totp.now())
            check_otp_button.click()
        except Exception:
            logging.error('OTP parameters are not found on the screen')
            return False


if __name__ == '__main__':
    odis_auth = ODISAuth()
    try:
        if odis_auth.create_mutex() is False:
            sys.exit(1)

        if odis_auth.load_config() is False:
            sys.exit(1)

        if odis_auth.run_login() is False:
            sys.exit(1)
    finally:
        if odis_auth.mutex:
            win32api.CloseHandle(odis_auth.mutex)
