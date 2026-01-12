# 🔒 WATCHDOG

A lightweight, hidden background service that captures photos of intruders attempting to access your Windows laptop with wrong passwords.

## ✨ Features

- 🚀 **Instant Detection** - Detects failed login attempts in 0.1 seconds
- 📸 **Fast Capture** - Takes photo in 0.5 seconds using webcam
- 👻 **Hidden Execution** - Runs completely invisible in background
- 🔄 **Auto-Restart** - Survives crashes with 999 retry attempts
- 📱 **Telegram Alerts** - Sends photos directly to your Telegram
- 🌐 **Offline Queue** - Saves photos when offline, uploads when connected
- 🔐 **Boot Protection** - Starts before login on every boot
- ⚡ **Zero Maintenance** - Set it and forget it

## 📋 Requirements

- Windows 10/11
- Python 3.7+
- Webcam
- Telegram Bot Token & Chat ID

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Telegram

```powershell
python setup/setup_gui.py
```

Enter your Telegram Bot Token and Chat ID when prompted.

### 3. Install as Startup Service

**Run as Administrator:**

```powershell
python setup/install_startup.py
```

Or use the PowerShell script:

```powershell
powershell -ExecutionPolicy Bypass -File "setup/setup.ps1"
```

### 4. Test It

Shut down your laptop, power it back on, and enter 2 wrong PINs at the lock screen. Check your Telegram!

## 📁 Project Structure

```
Anti-Theft/
├── service/
│   ├── monitor.py          # Main monitoring service
│   ├── camera.py           # Camera capture module
│   └── uploader.py         # Telegram upload module
├── setup/
│   ├── setup_gui.py        # Telegram configuration
│   ├── install_startup.py  # Automated installer
│   └── final_fix.ps1       # PowerShell installer
├── dist/
│   ├── monitor.exe         # Compiled executable (after build)
│   └── config.json         # Configuration file
├── config.json             # Main configuration
├── monitor.spec            # PyInstaller build spec
└── requirements.txt        # Python dependencies
```

## ⚙️ Configuration

Edit `config.json`:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "security": {
    "failed_attempt_threshold": 2,
    "event_id": 4625,
    "check_interval_seconds": 1
  },
  "camera": {
    "device_index": 0
  }
}
```

## 🔧 Management

Run these commands in **PowerShell as Administrator**.

### Start Monitor
Starts the service immediately.
```powershell
schtasks /Run /TN "AntiTheftMonitor"
```

### Stop Monitor
Stops the service immediately.
```powershell
schtasks /End /TN "AntiTheftMonitor"
Stop-Process -Name monitor -Force -ErrorAction SilentlyContinue
```

### Disable Startup
Prevents the monitor from starting automatically on boot.
```powershell
schtasks /Change /TN "AntiTheftMonitor" /DISABLE
```

### Enable Startup
Enables the monitor to start automatically on boot.
```powershell
schtasks /Change /TN "AntiTheftMonitor" /ENABLE
```

> **Note:** If you installed using `setup.ps1`, the task names are different:
> - **Service:** `AntiTheft_Service`
> - **Commander:** `AntiTheft_Commander`
>
> Replace `"AntiTheftMonitor"` with the appropriate task name in the commands above.

## 🛡️ How It Works

1. **Event Monitoring**: Monitors Windows Security Event Log for Event ID 4625 (failed login)
2. **Threshold Detection**: Triggers after 2 failed attempts (configurable)
3. **Photo Capture**: Uses OpenCV to capture webcam photo instantly
4. **Queue System**: Saves photos to `C:\ProgramData\AntiTheftCaptures\` if offline
5. **Upload Worker**: Background thread uploads queued photos when internet available
6. **Telegram Delivery**: Sends photo with alert message to your Telegram

## 📊 Performance

- **Event Detection**: 0.1 seconds
- **Photo Capture**: 0.5 seconds
- **Total Response**: ~1.5 seconds from wrong PIN to photo
- **Memory Usage**: ~50MB
- **CPU Usage**: <1% idle, ~5% during capture

## 🔐 Security Notes

- Runs as SYSTEM user with highest privileges
- Configuration stored in plain text (consider encrypting bot token)
- Photos stored temporarily in ProgramData (deleted after upload)
- No network activity except Telegram uploads

## 🐛 Troubleshooting

### Monitor not starting after shutdown?
- Disable Windows Fast Startup in Power Options
- Check Task Scheduler for errors
- Verify executable exists in `dist/` folder

### Not receiving Telegram messages?
- Verify bot token and chat ID in config.json
- Check internet connection
- Look for queued photos in `C:\ProgramData\AntiTheftCaptures\`

### Console window appearing?
- Rebuild with: `pyinstaller --clean monitor.spec`
- Ensure `console=False` in monitor.spec

## 📝 License

MIT License - Feel free to use and modify

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## ⚠️ Disclaimer

This software is for personal security purposes only. Ensure you comply with local laws regarding surveillance and photography. The author is not responsible for misuse.

## 📧 Support

For issues and questions, please open a GitHub issue or contact via Telegram.

---

**Made by drizzlehx**
