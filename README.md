# 🔑 ODISAuth

**Open-source script for automated ODIS Online authentication**

Automates ODIS login using `pywinauto`, supporting **username/password and 2FA (TOTP)** authentication.

---

## ⚙️ System Requirements
- ODIS software installed
- Windows operating system

---

## 📥 Installation & Usage

1. **Download** the `ODISAuth.exe` file from this repository
2. **Configure** the `ODISAuth_config.json` file:
   ```json
   {
       "ODIS_LOGIN": "your_username",
       "ODIS_PASSWORD": "your_password",
       "TOTP_SECURE": "your_totp_key"
   }
   ```
3. **Run** the `ODISAuth.exe` file as administrator, when you see the online login window.

---

## 🔑 How to Get TOTP_SECURE
1. **Log** in to your personal account at grp.volkswagenag.com
2. **Locate** your TOTP key (in base32 format)
3. **Copy** it into the TOTP_SECURE field in the config file
