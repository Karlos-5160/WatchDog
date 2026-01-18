import os
import subprocess
import shutil
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")

MONITOR_SPEC = os.path.join(BASE_DIR, "monitor.spec")
INSTALLER_SCRIPT = os.path.join(BASE_DIR, "setup", "install_wizard.py")

def clean_build():
    print("[*] Cleaning build directories...")
    # Use ignore_errors=True to skip locked files (like the running monitor.exe)
    if os.path.exists(DIST_DIR): shutil.rmtree(DIST_DIR, ignore_errors=True)
    if os.path.exists(BUILD_DIR): shutil.rmtree(BUILD_DIR, ignore_errors=True)
    if not os.path.exists(DIST_DIR): os.makedirs(DIST_DIR)

def build_monitor():
    print("\n[1/2] Building Service Payload (monitor.exe)...")
    try:
        # Add icon manually for now or rely on spec. 
        # Note: Valid way to override spec icon is complex, so we skip icon for payload for now 
        # (It runs hidden anyway so icon matters less for the service)
        cmd = ["pyinstaller", "--clean", MONITOR_SPEC]
        subprocess.run(cmd, cwd=BASE_DIR, check=True)
        
        # Verify
        exe_path = os.path.join(DIST_DIR, "monitor_payload.exe")
        if os.path.exists(exe_path):
            print(f"[SUCCESS] Payload built: {exe_path}")
            return exe_path
        else:
            raise Exception("monitor_payload.exe not found after build")
    except Exception as e:
        print(f"[ERROR] Build failed: {e}")
        sys.exit(1)

def build_uninstaller():
    print("\n[1.5/3] Building Uninstaller (uninstall.exe)...")
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name", "uninstall",
        "--icon", "setup/app_icon.ico",
        "--clean",
        "--uac-admin",
        "setup/uninstall.py"
    ]
    subprocess.run(cmd, cwd=BASE_DIR, check=True)
    
    # Verify
    if not os.path.exists(os.path.join(DIST_DIR, "uninstall.exe")):
         raise Exception("uninstall.exe build failed")

def build_installer(payload_path):
    print("\n[3/3] Building Installer (WatchDog_Installer_v3.exe)...")
    
    # Calculate add-data separator (; for Windows)
    separator = ";" 
    
    # Path to uninstaller
    uninstall_path = os.path.join(DIST_DIR, "uninstall.exe")
    
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name", "WatchDog_Installer_v3",
        "--icon", "setup/app_icon.ico",
        "--add-data", f"{payload_path}{separator}.",
        "--add-data", f"{uninstall_path}{separator}.",
        "--add-data", f"setup/app_icon.ico{separator}.",
        "--add-data", f"setup/branding.png{separator}.",
        "--clean",
        "--uac-admin",
        INSTALLER_SCRIPT
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, cwd=BASE_DIR, check=True)
        
        setup_exe = os.path.join(DIST_DIR, "WatchDog_Installer_v3.exe")
        if os.path.exists(setup_exe):
            print(f"\n[SUCCESS] Installer created: {setup_exe}")
            print("You can now distribute this file.")
        else:
            raise Exception("WatchDog_Setup.exe not found")
            
    except Exception as e:
        print(f"[ERROR] Installer build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=== WatchDog Installer Builder ===")
    
    # 0. Clean
    clean_build()
    
    # 1. Build Payload First
    payload = build_monitor()

    # 2. Build Uninstaller
    build_uninstaller()
    
    # 3. Build Installer with Payload embedded
    build_installer(payload)
