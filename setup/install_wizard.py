import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import ctypes
import json
import shutil
import subprocess
import threading
import time
from PIL import Image, ImageTk

# Force Taskbar Icon Persistence early
try:
    myappid = 'watchdog.security.installer.v3'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

# ---------------------------------------------------------------------------
# CONSTANTS & PATHS
# ---------------------------------------------------------------------------
APP_NAME = "WatchDog Setup"
INSTALL_DIR = r"C:\Program Files\WatchDog"
EXECUTABLE_NAME = "monitor.exe"
SOURCE_PAYLOAD_NAME = "monitor_payload.exe"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("650x520") # More compact height
        self.resizable(False, False)
        
        # Icon Setup
        try:
            icon_path = get_resource_path("app_icon.ico")
            if not os.path.exists(icon_path):
                 icon_path = os.path.join(os.getcwd(), "setup", "app_icon.ico")
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path) 
        except Exception as e:
            print(f"Icon load error: {e}")

        # Style Configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Professional Color Palette
        bg_color = "#ffffff"
        accent_color = "#0078D7"
        text_color = "#333333"
        
        self.configure(bg=bg_color)
        
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=text_color, font=("Segoe UI", 10))
        
        # Standard TTK Button (for secondary)
        style.configure("TButton", font=("Segoe UI", 10), background="#e1e1e1")
        
        style.configure("Header.TLabel", font=("Segoe UI", 24, "bold"), foreground=accent_color, background=bg_color)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 12), foreground="#666666", background=bg_color)
        style.configure("Warning.TLabel", font=("Segoe UI", 10), foreground="#d9534f", background=bg_color)
        
        style.configure("TLabelframe", background=bg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_color, font=("Segoe UI", 12, "bold"))
        
        # Custom Entry Style with Padding (Left: 10, Top: 5, Right: 5, Bottom: 5)
        style.configure("Padded.TEntry", padding=(10, 5, 5, 5))

        # Main Container - Tightened vertical padding to move content up
        self.container = ttk.Frame(self, padding="40 10")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (WelcomePage, ConfigPage, InstallPage, SuccessPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        # Grid configuration
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.show_frame("WelcomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def get_config_data(self):
        return self.frames["ConfigPage"].get_data()

class WelcomePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Content Frame
        content = ttk.Frame(self)
        content.pack(fill="both", expand=True)

        # Header
        label = ttk.Label(content, text="WatchDog Security", style="Header.TLabel")
        label.pack(pady=(20, 10), anchor="center")
        
        # Subheader / Description
        desc_text = (
            "Advanced Anti-Theft Protection for Windows.\n"
            "Runs silently, Capture intruders & Alerts you instantly."
        )
        ttk.Label(content, text=desc_text, style="SubHeader.TLabel", justify="center").pack(pady=(0, 20), anchor="center")

        # Feature List Container (Centered Block)
        features_frame = ttk.Frame(content)
        features_frame.pack(pady=5, anchor="center")
        
        # Inner-align text to left, but the frame itself is centered
        features = [
            ("🛡️", "Secure Background Service"),
            ("📸", "Instant Camera Capture"),
            ("📱", "Telegram Remote Control")
        ]
        
        for i, (icon, text) in enumerate(features):
            # Icon Column
            lbl = ttk.Label(features_frame, text=icon, font=("Segoe UI", 12), width=3, anchor="center")
            lbl.grid(row=i, column=0, padx=(0, 10), pady=3)
            # Text Column
            ttk.Label(features_frame, text=text, font=("Segoe UI", 11)).grid(row=i, column=1, sticky="w", pady=3)

        # Branding Graphic (Filling the empty space)
        try:
            branding_path = get_resource_path("branding.png")
            if not os.path.exists(branding_path):
                branding_path = os.path.join(os.getcwd(), "setup", "branding.png")
            
            if os.path.exists(branding_path):
                img = Image.open(branding_path)
                # Resize to fit nicely (maintaining aspect ratio)
                img.thumbnail((200, 120)) 
                self.branding_img = ImageTk.PhotoImage(img)
                branding_lbl = ttk.Label(content, image=self.branding_img)
                branding_lbl.pack(pady=10)
        except Exception as e:
            print(f"Branding load error: {e}")

        # Bottom Action Area - Moved up
        action_area = ttk.Frame(self)
        action_area.pack(side="bottom", fill="x", pady=(0, 15))

        # Admin Check
        if not is_admin():
            warn_msg = "⚠️ Administrator privileges required"
            ttk.Label(action_area, text=warn_msg, style="Warning.TLabel").pack(side="left", padx=10)
            
            # Standard tk.Button for reliability
            btn = tk.Button(action_area, text="Relaunch as Admin", command=self.relaunch_admin,
                            font=("Segoe UI", 10), bg="#e1e1e1", padx=15, pady=5)
            btn.pack(side="right")
        else:
            # Standard tk.Button for "Primary" action
            btn = tk.Button(action_area, text="Get Started  →", 
                            command=lambda: controller.show_frame("ConfigPage"),
                            font=("Segoe UI", 11, "bold"), bg="#0078D7", fg="white", 
                            activebackground="#0063b1", activeforeground="white",
                            relief="flat", padx=20, pady=8, cursor="hand2")
            btn.pack(side="right")

    def relaunch_admin(self):
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

class ConfigPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        ttk.Label(self, text="Configuration", style="Header.TLabel").pack(pady=(5, 2), anchor="w")
        ttk.Label(self, text="Connect your Telegram Bot to receive security alerts.", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 15))

        # Form Area
        form_frame = ttk.LabelFrame(self, text=" Telegram Credentials ", padding=15)
        form_frame.pack(fill="x", pady=5)

        # Token
        ttk.Label(form_frame, text="Bot Token:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,5))
        self.token_entry = ttk.Entry(form_frame, width=60, font=("Consolas", 12), style="Padded.TEntry")
        self.token_entry.pack(fill="x", pady=(0, 15))

        # Chat ID
        ttk.Label(form_frame, text="Chat ID:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,5))
        self.chat_id_entry = ttk.Entry(form_frame, width=60, font=("Consolas", 12), style="Padded.TEntry")
        self.chat_id_entry.pack(fill="x", pady=(0, 15))
        
        # Test Button (Regular standard button)
        self.test_btn = tk.Button(form_frame, text="📡 Test Connection", command=self.test_connection,
                                  font=("Segoe UI", 10), bg="#f0f0f0", padx=15, pady=5)
        self.test_btn.pack(anchor="e", pady=5)

        # Navigation Area - Moved up
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side="bottom", fill="x", pady=(0, 15))
        
        # Secondary Button
        bk_btn = tk.Button(nav_frame, text="← Back", command=lambda: controller.show_frame("WelcomePage"),
                           font=("Segoe UI", 11), bg="#e1e1e1", relief="flat", padx=25, pady=10, cursor="hand2")
        bk_btn.pack(side="left")
        
        # Primary Button
        next_btn = tk.Button(nav_frame, text="Install Now", 
                            command=self.validate_and_proceed,
                            font=("Segoe UI", 12, "bold"), bg="#0078D7", fg="white",
                            activebackground="#0063b1", activeforeground="white",
                            relief="flat", padx=40, pady=10, cursor="hand2")
        next_btn.pack(side="right")

    def test_connection(self):
        token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()
        
        if not token or not chat_id:
            messagebox.showwarning("Missing Info", "Please enter both Token and Chat ID first.")
            return

        self.test_btn.config(state="disabled", text="Testing...")
        
        def run_test():
            try:
                import requests
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                data = {"chat_id": chat_id, "text": "🔔 WatchDog Installer: Connection Successful!"}
                resp = requests.post(url, json=data, timeout=5)
                
                if resp.status_code == 200:
                    self.after(0, lambda: messagebox.showinfo("Success", "Test Message Sent! Check your Telegram."))
                else:
                    self.after(0, lambda: messagebox.showerror("Failed", f"Telegram Error: {resp.text}"))
            except Exception as e:
                 self.after(0, lambda: messagebox.showerror("Connection Error", str(e)))
            finally:
                 self.after(0, lambda: self.test_btn.config(state="normal", text="📡 Test Connection"))

        threading.Thread(target=run_test, daemon=True).start()

    def get_data(self):
        return {
            "bot_token": self.token_entry.get().strip(),
            "chat_id": self.chat_id_entry.get().strip()
        }

    def validate_and_proceed(self):
        data = self.get_data()
        if not data["bot_token"] or not data["chat_id"]:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        self.controller.show_frame("InstallPage")
        self.controller.frames["InstallPage"].start_install()

class InstallPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Header
        label = ttk.Label(self, text="Installing WatchDog...", style="Header.TLabel")
        label.pack(pady=(10, 20))

        # Progress Status
        self.status_var = tk.StringVar(value="Initializing...")
        status_label = ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 11))
        status_label.pack(anchor="w", pady=5)

        # Progress Bar (Thicker appearance via layout or just better padding)
        self.progress = ttk.Progressbar(self, orient="horizontal", length=450, mode="determinate")
        self.progress.pack(pady=(0, 20), ipady=5)

        # Terminal-style Log
        log_frame = ttk.LabelFrame(self, text=" System Log ", padding=5)
        log_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=12, width=60, 
                               font=("Consolas", 9), state="disabled",
                               bg="#0c0c0c", fg="#00ff00", # Terminal Look
                               relief="flat", highlightthickness=0)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", "> " + message + "\n") # > Prefix for terminal feel
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.status_var.set(message)
        self.update_idletasks()

    def start_install(self):
        threading.Thread(target=self.run_installation, daemon=True).start()

    def run_installation(self):
        try:
            self.progress['value'] = 0
            
            # 1. Prepare Directory
            self.log(f"Creating directory: {INSTALL_DIR}")
            if not os.path.exists(INSTALL_DIR):
                os.makedirs(INSTALL_DIR)
            time.sleep(0.5) # Pace: Pause
            self.progress['value'] = 20

            # 2. Extract Files
            self.log("Copying service executable...")
            src_exe = get_resource_path(SOURCE_PAYLOAD_NAME)
            if not os.path.exists(src_exe):
                # Fallback for dev mode
                src_exe = os.path.join(os.getcwd(), "dist", SOURCE_PAYLOAD_NAME)
            
            if not os.path.exists(src_exe):
                raise Exception(f"Source file not found: {src_exe}")

            dest_exe = os.path.join(INSTALL_DIR, EXECUTABLE_NAME)
            shutil.copy2(src_exe, dest_exe)
            
            # Copy Uninstaller
            self.log("Copying uninstaller...")
            try:
                src_uninstall = get_resource_path("uninstall.exe")
                if not os.path.exists(src_uninstall):
                    # Fallback
                    src_uninstall = os.path.join(os.getcwd(), "dist", "uninstall.exe")
                
                if os.path.exists(src_uninstall):
                    dest_uninstall = os.path.join(INSTALL_DIR, "uninstall.exe")
                    shutil.copy2(src_uninstall, dest_uninstall)
                else:
                    self.log("Warning: uninstall.exe not found in bundle.")
            except Exception as e:
                self.log(f"Warning: Failed to copy uninstaller: {e}")

            self.progress['value'] = 40
            time.sleep(0.6) # Pace: Pause after copying files

            # 3. Create Config
            self.log("Generating configuration...")
            config_data = self.controller.get_config_data()
            full_config = {
                "telegram": config_data,
                "security": {
                    "failed_attempt_threshold": 2,
                    "event_id": 4625,
                    "check_interval_seconds": 0.1
                },
                "camera": {"device_index": 0}
            }
            
            with open(os.path.join(INSTALL_DIR, "config.json"), "w") as f:
                json.dump(full_config, f, indent=4)
            time.sleep(0.8) # Pace: Pause
            self.progress['value'] = 60

            # 4. Cleanup Old Tasks
            self.log("Stopping old services...")
            subprocess.run(["taskkill", "/F", "/IM", EXECUTABLE_NAME], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["schtasks", "/Delete", "/TN", "AntiTheft_Service", "/F"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["schtasks", "/Delete", "/TN", "AntiTheft_Commander", "/F"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(0.4) # Pace: Pause
            self.progress['value'] = 70

            # 5. Create Tasks
            self.log("Registering System Service...")
            self.create_service_task(dest_exe)
            
            self.log("Registering User Commander...")
            self.create_commander_task(dest_exe)
            time.sleep(0.8) # Pace: Pause
            self.progress['value'] = 90

            # 6. Start Tasks
            self.log("Starting services...")
            subprocess.run(["schtasks", "/Run", "/TN", "AntiTheft_Service"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["schtasks", "/Run", "/TN", "AntiTheft_Commander"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(1.0) # Pace: Final completion pause
            self.progress['value'] = 100
            self.log("Installation Complete!")
            time.sleep(1)
            self.controller.show_frame("SuccessPage")

        except Exception as e:
            messagebox.showerror("Installation Failed", str(e))
            self.log(f"Error: {e}")

    def create_service_task(self, exe_path):
        # Use XML to avoid quoting/parsing issues with spaces in paths
        xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>WatchDog Security Service (System)</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
      <Arguments>--service</Arguments>
      <WorkingDirectory>{os.path.dirname(exe_path)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        
        xml_path = os.path.join(os.environ['TEMP'], "wd_service.xml")
        with open(xml_path, "w", encoding="utf-16") as f:
            f.write(xml_content)
            
        try:
            cmd = ['schtasks', '/Create', '/TN', 'AntiTheft_Service', '/XML', xml_path, '/F']
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)

    def create_commander_task(self, exe_path):
        # Current User, Logon Trigger
        # We need to get the current user ID for the task principal?
        # Actually for a user task, simpler XML or interactive creation might be better,
        # but XML allows us to specify "RunLevel Highest" easily.
        
        # NOTE: When running as Admin installer, "S-1-5-32-544" (Admins) or similar might be context.
        # But we want it to run for the LOGGED ON USER.
        # <GroupId>S-1-5-32-545</GroupId> (Users) doesn't work well for specific logon.
        # For simplicity in this wizard, we'll configure it to run for the *User who installs it* 
        # (assuming they are the owner) OR use the generic LogonTrigger for "Any User".
        
        xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>WatchDog User Agent (Commander)</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <GroupId>S-1-5-32-545</GroupId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
      <Arguments>--commander</Arguments>
      <WorkingDirectory>{os.path.dirname(exe_path)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''

        xml_path = os.path.join(os.environ['TEMP'], "wd_commander.xml")
        with open(xml_path, "w", encoding="utf-16") as f:
            f.write(xml_content)
            
        try:
            cmd = ['schtasks', '/Create', '/TN', 'AntiTheft_Commander', '/XML', xml_path, '/F']
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)

class SuccessPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Main Container for this page
        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=20)

        # Success Header (Larger & Green)
        # We create a specific label here to override style strictly if needed, 
        # but using the style with an override font work well.
        lbl = ttk.Label(content, text="Installation Complete!", font=("Segoe UI", 26, "bold"), foreground="#28a745")
        lbl.pack(pady=(10, 5))

        # Subheader
        ttk.Label(content, text="WatchDog Security is active and protecting your system.", 
                 font=("Segoe UI", 14), foreground="#555555").pack(pady=(0, 15))

        # Status Checklist Frame
        status_frame = ttk.LabelFrame(content, text=" System Status ", padding=15)
        status_frame.pack(fill="x", pady=5)

        checklist = [
            ("✅", "System Service Installed", "Running (Auto-Start)"),
            ("✅", "Security Monitor Active", "Listening for Events"),
            ("✅", "Telegram Connection", "Configured & Ready")
        ]

        for i, (icon, title, status) in enumerate(checklist):
             # Icon
             ttk.Label(status_frame, text=icon, font=("Segoe UI", 14)).grid(row=i, column=0, padx=10, pady=8)
             # Title
             ttk.Label(status_frame, text=title, font=("Segoe UI", 12, "bold")).grid(row=i, column=1, sticky="w", padx=5)
             # Status Detail
             ttk.Label(status_frame, text=status, font=("Segoe UI", 11), foreground="#666666").grid(row=i, column=2, sticky="w", padx=10)

        # Next Steps Section
        steps_frame = ttk.Frame(content)
        steps_frame.pack(fill="x", pady=10)
        
        ttk.Label(steps_frame, text="👉 Next Steps:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        steps_text = (
            "1. Lock your screen (Win + L).\n"
            "2. Enter a wrong password to trigger the alarm.\n"
            "3. Check your Telegram for the photo alert."
        )
        ttk.Label(steps_frame, text=steps_text, font=("Segoe UI", 12), justify="left").pack(anchor="w", padx=20)

        # Close Button (Bottom) - Modern Flat Dark Style
        tk.Button(self, text="Close", command=lambda: sys.exit(),
                 font=("Segoe UI", 11, "bold"), 
                 bg="#333333", fg="white", 
                 activebackground="#555555", activeforeground="white",
                 relief="flat", padx=40, pady=10, cursor="hand2").pack(side="bottom", pady=20)

if __name__ == "__main__":
    if not is_admin():
        # Re-run admin check in GUI class, but basic check here
        pass
    
    app = InstallerApp()
    app.mainloop()
