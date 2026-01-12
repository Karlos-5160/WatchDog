import threading
import time
import requests
import json
import os
import ctypes
import sys
from datetime import datetime

# Global configuration
BOT_TOKEN = None
CHAT_ID = None
CAPTURES_DIR = None

def init_commander(config, captures_dir):
    global BOT_TOKEN, CHAT_ID, CAPTURES_DIR
    BOT_TOKEN = config['telegram']['bot_token']
    CHAT_ID = str(config['telegram']['chat_id'])
    CAPTURES_DIR = captures_dir

def send_reply(text):
    """Send text reply to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_photo(photo_path, caption=None):
    """Send photo to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": CHAT_ID}
            if caption:
                data["caption"] = caption
            requests.post(url, data=data, files=files, timeout=20)
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")

def execute_command(command_text):
    """Parse and execute commands"""
    cmd = command_text.lower().strip().split()
    if not cmd:
        return

    action = cmd[0]
    print(f"[CMD] Received command: {action}")

    if action == "/ping":
        send_reply("🏓 Pong! WatchDog is watching. System is online.")

    elif action == "/capture":
        # Lazy import to save RAM
        try:
            from service.camera import capture_intruder_file
        except ImportError:
            from camera import capture_intruder_file
        
        send_reply("📸 Capturing photo...")
        filepath = capture_intruder_file(CAPTURES_DIR, prefix="cmd_")
        if filepath:
            send_photo(filepath, "📸 Remote capture requested")
            try:
                os.remove(filepath)
            except:
                pass
        else:
            send_reply("❌ Camera unavailable")

    elif action == "/screen":
        send_reply("🖥️ Taking screenshot...")
        try:
            import pyautogui
            timestamp = int(time.time())
            filename = f"screen_{timestamp}.png"
            filepath = os.path.join(CAPTURES_DIR, filename)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            send_photo(filepath, "🖥️ Desktop Screenshot")
            os.remove(filepath)
        except Exception as e:
            send_reply(f"❌ Screenshot failed: {e}")

    elif action == "/lock":
        send_reply("🔒 Locking workstation...")
        try:
            ctypes.windll.user32.LockWorkStation()
            send_reply("✅ System locked.")
        except Exception as e:
            send_reply(f"❌ Lock failed: {e}")

    elif action == "/msg":
        # Usage: /msg Hello Thief
        message = " ".join(cmd[1:])
        if message:
            send_reply(f"📢 Displaying message: '{message}'")
            # Run detached to not block
            cmd_line = f'mshta "javascript:code(close((new ActiveXObject("WScript.Shell")).Popup("{message}",0,"WatchDog Alert",48+4096)))"'
            threading.Thread(target=os.system, args=(cmd_line,)).start()
        else:
            send_reply("⚠️ Usage: /msg [Your Message]")
            
    elif action == "/help":
        help_text = (
            "🛡️ *WatchDog Command Center*\n\n"
            "• /ping - Check status\n"
            "• /capture - Take photo\n"
            "• /screen - Screenshot\n"
            "• /lock - Lock PC\n"
            "• /msg [text] - Show popup"
        )
        send_reply(help_text)

def start_commander_loop():
    """Main polling loop using Long Polling"""
    offset = 0
    print("[*] Commander Service Started (Low-RAM Polling Mode)")
    
    session = requests.Session()
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {
                "offset": offset,
                "timeout": 30  # Wait up to 30s for new message (Low CPU/RAM)
            }
            
            response = session.get(url, params=params, timeout=40)
            result = response.json()

            if result.get("ok"):
                for update in result.get("result", []):
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        message = update["message"]
                        user_id = str(message.get("from", {}).get("id"))
                        text = message.get("text", "")
                        
                        # Security: Only accept commands from OWNER
                        if user_id == CHAT_ID and text.startswith("/"):
                            # Run usage intensive tasks in thread
                            threading.Thread(target=execute_command, args=(text,)).start()
                            
        except Exception as e:
            # Silent error handling with backoff
            time.sleep(5)
            
        time.sleep(0.5)
