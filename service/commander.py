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
            send_reply(f"📢 Opening Notepad: '{message}'")
            
            def show_notepad_msg(msg):
                import subprocess
                try:
                    # Create a visible text file
                    file_path = os.path.join(CAPTURES_DIR, "MESSAGE_FROM_OWNER.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(msg)
                    
                    # Open Notepad without shell window
                    subprocess.Popen(["notepad.exe", file_path])
                except Exception as e:
                    print(f"[ERROR] Failed to open notepad: {e}")

            threading.Thread(target=show_notepad_msg, args=(message,)).start()
        else:
            send_reply("⚠️ Usage: /msg [Your Message]")
            
    elif action == "/locate":
        send_reply("📡 Scanning WiFi Spectrum & Geolocation...")
        
        def fetch_loc():
            import subprocess
            
            # 1. Scan Nearby WiFi Networks (Triangulation Data)
            wifi_list = []
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                output = subprocess.check_output(
                    ["netsh", "wlan", "show", "networks", "mode=bssid"], 
                    startupinfo=si, 
                    encoding="utf-8", 
                    errors="ignore"
                )
                
                current_ssid = "Unknown"
                for line in output.split("\n"):
                    line = line.strip()
                    if line.startswith("SSID"):
                        # Format: "SSID 1 : Name"
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            current_ssid = parts[1].strip()
                    elif line.startswith("BSSID"):
                        # Format: "BSSID 1 : 00:xx:..."
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            bssid = parts[1].strip()
                            wifi_list.append(f"📶 {current_ssid}\n   `{bssid}`")
                    elif line.startswith("Signal"):
                         # Add signal to last entry
                         if wifi_list:
                             parts = line.split(":", 1)
                             if len(parts) > 1:
                                 wifi_list[-1] += f" ({parts[1].strip()})"
            except Exception as e:
                wifi_list.append(f"Scan Error: {e}")

            # 2. Get IP & Geo
            try:
                info = requests.get("http://ip-api.com/json/", timeout=10).json()
                if info.get("status") == "success":
                    map_link = f"https://maps.google.com/?q={info['lat']},{info['lon']}"
                    
                    # Format WiFi Data (Top 8 strong signals)
                    wifi_report = "\n".join(wifi_list[:8]) if wifi_list else "No WiFi networks found."
                    
                    msg = (f"📍 *Detailed Location Report*\n"
                           f"--------------------------------\n"
                           f"🌍 *IP-Based Info*:\n"
                           f"   City: {info['city']}\n"
                           f"   ISP: {info['isp']}\n"
                           f"   IP: {info['query']}\n"
                           f"   🔗 [Google Maps]({map_link})\n\n"
                           f"📡 *Nearby WiFi (Triangulation Data)*:\n"
                           f"{wifi_report}\n\n"
                           f"_Copy BSSIDs to Wigle.net for precise coord_")
                    send_reply(msg)
                else:
                    send_reply(f"❌ Geo-IP Failed. WiFi Scan:\n" + "\n".join(wifi_list[:5]))
            except Exception as e:
                send_reply(f"❌ Err: {e}")
        
        threading.Thread(target=fetch_loc).start()

    elif action == "/stat" or action == "/stats":
        send_reply("📊 Fetching system statistics...")
        try:
            import psutil
            import platform
            
            # CPU
            cpu_freq = psutil.cpu_freq()
            freq_curr = f"{cpu_freq.current:.1f}Mhz" if cpu_freq else "N/A"
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory
            ram = psutil.virtual_memory()
            ram_total = f"{ram.total / (1024**3):.1f}GB"
            ram_used = f"{ram.used / (1024**3):.1f}GB"
            ram_percent = ram.percent
            
            # Disk
            disk = psutil.disk_usage('C:\\')
            disk_total = f"{disk.total / (1024**3):.1f}GB"
            disk_free = f"{disk.free / (1024**3):.1f}GB"
            
            # Battery
            battery = psutil.sensors_battery()
            batt_status = "N/A"
            if battery:
                plugged = "🔌 Plugged In" if battery.power_plugged else "🔋 On Battery"
                batt_status = f"{battery.percent}% ({plugged})"

            stats_msg = (
                f"📊 *System Statistics*\n"
                f"------------------------\n"
                f"💻 *System*: {platform.system()} {platform.release()}\n"
                f"🧠 *CPU*: {cpu_usage}% (Freq: {freq_curr})\n"
                f"💾 *RAM*: {ram_used} / {ram_total} ({ram_percent}%)\n"
                f"💿 *Disk (C:)*: {disk_free} free / {disk_total}\n"
                f"⚡ *Battery*: {batt_status}\n"
                f"⏱️ *Boot Time*: {datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_reply(stats_msg)
        except Exception as e:
            send_reply(f"❌ Failed to fetch stats: {e}")

    elif action == "/help":
        help_text = (
            "🛡️ *WatchDog Command Center*\n\n"
            "• /ping - Check status\n"
            "• /capture - Take photo\n"
            "• /screen - Screenshot\n"
            "• /locate - Get Location\n"
            "• /stat - System Statistics\n"
            "• /lock - Lock PC\n"
            "• /msg [text] - Show popup"
        )
        send_reply(help_text)

def set_bot_commands():
    """Update the command menu in Telegram to match available commands"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "ping", "description": "Check status"},
        {"command": "capture", "description": "Take photo"},
        {"command": "screen", "description": "Take screenshot"},
        {"command": "locate", "description": "Get location"},
        {"command": "stat", "description": "System statistics"},
        {"command": "lock", "description": "Lock PC"},
        {"command": "msg", "description": "Show message on screen"},
        {"command": "help", "description": "Show help"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=10)
    except:
        pass

def start_commander_loop():
    """Main polling loop using Long Polling"""
    set_bot_commands()
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
