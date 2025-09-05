# Troubleshooting Guide

## 🚨 Common Issues

### Backend Connection Issues

#### Issue: "Backend server not running"
**Symptoms:**
- Red "Offline" indicator in top-right
- No data loading in dashboard
- Console error: "Backend connection failed"

**Solutions:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend if not running
cd backend
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
python app.py
```

#### Issue: Port already in use
**Error:** `OSError: [Errno 48] Address already in use`

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 [PID]  # Mac/Linux
taskkill /PID [PID] /F  # Windows

# Or use different port
uvicorn app:app --port 8001
```

### Email Account Issues

#### Issue: "Invalid credentials"
**Symptoms:**
- Account addition fails
- Error message about authentication

**Solutions:**
1. **Use App Password, not regular password**
   ```
   ❌ Wrong: your-regular-password
   ✅ Correct: abcd-efgh-ijkl-mnop (16-char app password)
   ```

2. **Verify 2FA is enabled**
   - Gmail: [Account Security](https://myaccount.google.com/security)
   - Outlook: [Security Settings](https://account.microsoft.com/security)

3. **Regenerate App Password**
   - Delete old app password
   - Create new one
   - Update in Email Assistant

#### Issue: "Connection timeout"
**Symptoms:**
- Long loading times
- Eventually fails with timeout error

**Solutions:**
1. **Check server settings**
   ```
   Gmail:
   IMAP: imap.gmail.com:993
   SMTP: smtp.gmail.com:587
   
   Outlook:
   IMAP: outlook.office365.com:993
   SMTP: smtp-mail.outlook.com:587
   ```

2. **Verify network connectivity**
   ```bash
   # Test IMAP connection
   telnet imap.gmail.com 993
   
   # Test SMTP connection
   telnet smtp.gmail.com 587
   ```

3. **Check firewall/antivirus**
   - Allow Python through firewall
   - Temporarily disable antivirus email protection

### Import/Installation Issues

#### Issue: FastAPI imports not found
**Symptoms:**
- Import errors in IDE
- Module not found errors

**Solutions:**
1. **Verify virtual environment**
   ```bash
   # Check if venv is activated
   which python  # Should point to venv
   
   # Activate if needed
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Reinstall packages**
   ```bash
   pip install --force-reinstall fastapi uvicorn
   ```

3. **IDE configuration**
   - VS Code: Ctrl+Shift+P → "Python: Select Interpreter"
   - PyCharm: Settings → Project → Python Interpreter

#### Issue: "No module named 'email'" or similar
**Error:** Built-in modules not found

**Solution:**
```bash
# This indicates Python path issues
# Recreate virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Issues

#### Issue: Database locked
**Error:** `sqlite3.OperationalError: database is locked`

**Solutions:**
```bash
# Stop all instances of the app
pkill -f "python app.py"

# Remove lock if it exists
rm -f backend/email_assistant.db-wal
rm -f backend/email_assistant.db-shm

# Restart app
python app.py
```

#### Issue: Corrupted database
**Symptoms:**
- Data not loading
- SQL errors in console

**Solutions:**
```bash
# Backup current database
cp backend/email_assistant.db backend/email_assistant.db.backup

# Reset database (will lose data)
rm backend/email_assistant.db

# Restart app (will recreate database)
python app.py
```

### Frontend Issues

#### Issue: Tailwind styles not loading
**Symptoms:**
- Unstyled appearance
- Console errors about CSS

**Solutions:**
1. **Check CDN connection**
   ```javascript
   // In browser console
   fetch('https://cdn.tailwindcss.com')
   ```

2. **Use local development server**
   ```bash
   # Instead of opening file directly
   cd frontend
   python -m http.server 3000
   ```

#### Issue: JavaScript errors
**Symptoms:**
- Functionality not working
- Console errors

**Solutions:**
1. **Check browser console (F12)**
   - Look for specific error messages
   - Check Network tab for failed requests

2. **Clear browser cache**
   - Hard refresh: Ctrl+Shift+R (Ctrl+Shift+F5 on Windows)
   - Clear browser cache and cookies

## 🔍 Debugging Tools

### Backend Debugging
```bash
# Verbose logging
uvicorn app:app --log-level debug

# Test API endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/api/dashboard
```

### Frontend Debugging
```javascript
// In browser console
// Check if Alpine.js is loaded
window.Alpine

// Check backend connection
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
```

### Database Debugging
```bash
# Connect to SQLite database
sqlite3 backend/email_assistant.db

# Check tables
.tables

# Check data
SELECT * FROM emails LIMIT 5;
SELECT * FROM email_accounts;
```

## 📊 Performance Issues

### Slow Email Processing
**Symptoms:**
- Long processing times
- Timeouts during email fetch

**Solutions:**
1. **Reduce batch size**
   ```python
   # In app.py, modify limit parameter
   @app.post("/api/process-emails/{account_id}")
   async def process_emails(account_id: int, limit: int = 5):  # Reduced from 10
   ```

2. **Check email server limits**
   - Gmail: 15 requests/second
   - Outlook: 10 requests/second

### High Memory Usage
**Solutions:**
1. **Process emails in smaller batches**
2. **Clear processed emails periodically**
3. **Restart backend service regularly**

## 🛠️ System Requirements

### Minimum Requirements
- Python 3.7+
- 2GB RAM
- 1GB disk space
- Internet connection

### Recommended
- Python 3.9+
- 4GB RAM
- SSD storage
- Stable broadband connection

## 📞 Getting Help

### Before Asking for Help
1. Check this troubleshooting guide
2. Search browser console for errors
3. Verify all steps in setup guide
4. Test with minimal configuration

### Information to Include
- Operating system and version
- Python version (`python --version`)
- Error messages (exact text)
- Steps to reproduce
- Browser and version (for frontend issues)

### Useful Commands for Diagnostics
```bash
# System information
python --version
pip list
which python

# Check running processes
ps aux | grep python  # Linux/Mac
tasklist | findstr python  # Windows

# Check network connectivity
ping google.com
telnet imap.gmail.com 993

# Backend logs
tail -f backend/logs/app.log  # If logging to file
```

## 🔄 Reset Procedures

### Complete Reset
```bash
# Stop all processes
pkill -f "python app.py"

# Remove virtual environment
rm -rf venv

# Remove database
rm -f backend/email_assistant.db

# Start fresh
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd backend && python app.py
```

### Data-Only Reset
```bash
# Keep accounts, remove processed emails
rm -f backend/email_assistant.db
# Restart app to recreate tables
```

### Account-Only Reset
```bash
# SQLite command to remove accounts
sqlite3 backend/email_assistant.db "DELETE FROM email_accounts;"
```