# Email Account Setup Guide

## 🔐 Gmail Setup (Recommended)

### Prerequisites
- Gmail account
- 2-Factor Authentication enabled

### Step 1: Enable 2-Factor Authentication
1. Visit [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **2-Step Verification**
3. Follow the setup wizard to enable 2FA
4. Verify with your phone or authenticator app

### Step 2: Generate App Password
1. Return to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **App passwords**
3. Select app: **Mail**
4. Select device: **Other (Custom name)**
5. Enter name: `Email Assistant`
6. Click **Generate**
7. **Important**: Copy the 16-character password immediately

### Step 3: Add to Email Assistant
```
Email Address: your.email@gmail.com
Password: [16-character app password]
IMAP Server: imap.gmail.com
SMTP Server: smtp.gmail.com
```

## 📧 Microsoft Outlook/Hotmail

### App Password Setup
1. Go to [Microsoft Account Security](https://account.microsoft.com/security)
2. Click **Advanced security options**
3. Under **App passwords**, click **Create a new app password**
4. Select **Email** and generate password

### Configuration
```
Email Address: your.email@outlook.com
Password: [App password]
IMAP Server: outlook.office365.com
SMTP Server: smtp-mail.outlook.com
```

## 🟡 Yahoo Mail

### App Password Setup
1. Go to [Yahoo Account Security](https://login.yahoo.com/account/security)
2. Click **Generate app password**
3. Select **Other App** and enter "Email Assistant"
4. Copy the generated password

### Configuration
```
Email Address: your.email@yahoo.com
Password: [App password]
IMAP Server: imap.mail.yahoo.com
SMTP Server: smtp.mail.yahoo.com
```

## 🏢 Corporate/Custom Email

### Common Configurations

#### Exchange Server
```
IMAP Server: mail.company.com
SMTP Server: smtp.company.com
Port (IMAP): 993
Port (SMTP): 587
```

#### cPanel/Shared Hosting
```
IMAP Server: mail.yourdomain.com
SMTP Server: mail.yourdomain.com
Port (IMAP): 993
Port (SMTP): 465 or 587
```

### Getting Server Information
Contact your IT administrator for:
- IMAP/SMTP server addresses
- Port numbers
- SSL/TLS requirements
- Authentication methods

## 🔧 Server Settings Reference

### Standard Ports
- **IMAP SSL**: 993
- **SMTP SSL**: 465
- **SMTP STARTTLS**: 587

### Security Settings
- **Encryption**: SSL/TLS (recommended)
- **Authentication**: Normal password or OAuth2

## ⚠️ Common Issues

### "Invalid Credentials"
- ✅ Use App Password, not regular password
- ✅ Copy entire password without spaces
- ✅ Verify 2FA is enabled

### "Connection Timeout"
- ✅ Check server addresses
- ✅ Verify firewall/antivirus settings
- ✅ Try different network connection

### "Authentication Failed"
- ✅ Regenerate App Password
- ✅ Check email provider's security settings
- ✅ Verify account isn't locked

## 🛡️ Security Best Practices

### App Password Management
- Use unique passwords for each application
- Store passwords securely
- Revoke unused passwords regularly
- Never share App Passwords

### Account Security
- Keep 2FA enabled
- Monitor account activity
- Use strong primary passwords
- Regular security reviews

## 📱 Mobile Provider Settings

### Common Mobile Carriers
Most mobile carriers use standard email protocols. Check with your provider:

#### Verizon
```
IMAP: incoming.verizon.net
SMTP: outgoing.verizon.net
```

#### AT&T
```
IMAP: imap.mail.att.net
SMTP: smtp.mail.att.net
```

## 🔍 Testing Your Setup

### Verification Steps
1. Add account in Email Assistant
2. Look for "Account added successfully!" message
3. Click "Process" button
4. Check for processed emails
5. Verify categorization works

### Debug Information
If setup fails, check browser console (F12) for:
- Network errors
- Authentication failures
- Server connection issues

## 📞 Provider Support Links

- [Gmail Help](https://support.google.com/gmail)
- [Outlook Help](https://support.microsoft.com/en-us/outlook)
- [Yahoo Help](https://help.yahoo.com/kb/mail)

## 💡 Pro Tips

1. **Test with small batches** first
2. **Label App Passwords** clearly
3. **Keep backup access** methods
4. **Monitor email processing** logs
5. **Update passwords** periodically