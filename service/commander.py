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
            import pyautogui
            timestamp = int(time.time())
            filename = f"cmd_screen_{timestamp}.png" # Prefix cmd_ to avoid monitor auto-upload
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

    elif action == "/help":
        help_text = (
            "🛡️ *WatchDog Command Center*\n\n"
            "• /ping - Check status\n"
            "• /capture - Take photo\n"
            "• /screen - Screenshot\n"
            "• /stat - System Status\n"
            "• /locate - Get Location\n"
            "• /lock - Lock PC\n"
            "• /msg [text] - Show popup"
        )
        send_reply(help_text)

    elif action == "/stat":
        send_reply("📊 Analyzing System Vital Signs...")
        
        def get_status():
            try:
                import shutil
                import subprocess
                import platform
                from datetime import datetime
                
                # Helper to run WMIC safely
                def wmic_get(property_cmd):
                    try:
                        si = subprocess.STARTUPINFO()
                        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        # Adding /value to ensure format "Key=Value"
                        # cmd string execution via shell=True for path compatibility
                        full_cmd = f"wmic {property_cmd} /value"
                        output = subprocess.check_output(full_cmd, startupinfo=si, shell=True).decode("utf-8", errors="ignore").strip()
                        
                        # Parsing "Key=Value" robustly
                        lines = [line.strip() for line in output.splitlines() if line.strip()]
                        for line in lines:
                            if "=" in line:
                                parts = line.split("=", 1)
                                if len(parts) == 2:
                                    return parts[1].strip()
                        return None
                    except:
                        return None

                # 1. System Info
                os_name = wmic_get("os get Caption")
                if not os_name:
                    os_name = f"{platform.system()} {platform.release()}"

                # 2. Boot Time
                boot_time = "Unknown"
                raw_boot = wmic_get("os get LastBootUpTime") # 20260116...
                if raw_boot and "." in raw_boot:
                    try:
                         # Parse YYYYMMDDHHMMSS
                        ts = raw_boot.split(".")[0]
                        dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
                        boot_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass

                # 3. CPU
                cpu_info = "Unknown"
                load = wmic_get("cpu get loadpercentage")
                freq = wmic_get("cpu get CurrentClockSpeed")
                if load or freq:
                    cpu_info = f"{load or '?'}% (Freq: {freq or '?'}Mhz)"

                # 4. RAM
                ram_info = "Unknown"
                visible_mem = wmic_get("os get TotalVisibleMemorySize")
                free_mem = wmic_get("os get FreePhysicalMemory")
                
                if visible_mem and free_mem:
                    try:
                        total_k = int(visible_mem)
                        free_k = int(free_mem)
                        used_k = total_k - free_k
                        
                        total_gb = round(total_k / 1024 / 1024, 1)
                        used_gb = round(used_k / 1024 / 1024, 1)
                        percent = round((used_k / total_k) * 100, 1)
                        ram_info = f"{used_gb}GB / {total_gb}GB ({percent}%)"
                    except:
                        pass

                # 5. Disk
                disk_info = "Unknown"
                try:
                    total, used, free = shutil.disk_usage("C:\\")
                    total_gb = round(total / (2**30), 1)
                    free_gb = round(free / (2**30), 1)
                    percent = round((used / total) * 100, 1)
                    disk_info = f"{free_gb}GB free / {total_gb}GB"
                except:
                    pass

                # 6. Battery
                battery_info = "N/A (Desktop/No Battery)"
                charge = wmic_get("path Win32_Battery get EstimatedChargeRemaining")
                status_code = wmic_get("path Win32_Battery get BatteryStatus")
                
                if charge:
                    status_text = "Unknown"
                    if status_code == "1": status_text = "🔋 On Battery"
                    elif status_code in ["2", "6", "7", "8", "9"]: status_text = "🔌 Plugged In"
                    
                    battery_info = f"{charge}% ({status_text})"

                # Construct Report
                report = (
                    f"📊 *System Statistics*\n"
                    f"------------------------\n"
                    f"💻 *System*: {os_name}\n"
                    f"🧠 *CPU*: {cpu_info}\n"
                    f"💾 *RAM*: {ram_info}\n"
                    f"💿 *Disk (C:)*: {disk_info}\n"
                    f"⚡ *Battery*: {battery_info}\n"
                    f"⏱️ *Boot Time*: {boot_time}"
                )
                send_reply(report)
                
            except Exception as e:
                send_reply(f"❌ Stat Error: {str(e)}")

        threading.Thread(target=get_status).start()

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
