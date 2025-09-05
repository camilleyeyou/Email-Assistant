# Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- Git (optional)
- Modern web browser
- Email account with IMAP access

### Installation Steps

#### 1. Download/Clone Project
```bash
# Option 1: Clone with Git
git clone <repository-url>
cd email-assistant

# Option 2: Download and extract ZIP
# Extract to email-assistant folder
```

#### 2. Create Project Structure
```bash
mkdir -p backend frontend docs tests scripts
```

#### 3. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify activation (should show venv in prompt)
which python  # Should point to venv directory
```

#### 4. Install Dependencies
```bash
# Navigate to backend directory
cd backend

# Install required packages
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

#### 5. Create Configuration Files
```bash
# Create .env file (optional)
cp .env.example .env

# Edit .env with your settings (optional)
nano .env
```

#### 6. Start the Backend Server
```bash
# From backend directory
python app.py

# You should see:
# INFO: Uvicorn running on http://0.0.0.0:8000
```

#### 7. Start the Frontend
```bash
# Open new terminal
cd frontend

# Option 1: Simple HTTP server
python -m http.server 3000

# Option 2: Open directly in browser
# Double-click index.html
```

#### 8. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 File Structure

After setup, your project should look like:

```
email-assistant/
├── backend/
│   ├── app.py                 # Main FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── email_assistant.db     # SQLite database (auto-created)
│   └── .env                   # Environment variables (optional)
├── frontend/
│   └── index.html            # Web application
├── docs/
│   ├── README.md             # Documentation index
│   ├── SETUP.md              # This file
│   ├── EMAIL_SETUP.md        # Email configuration guide
│   ├── API.md                # API documentation
│   └── TROUBLESHOOTING.md    # Common issues
├── venv/                     # Virtual environment
├── .gitignore               # Git ignore rules
└── README.md               # Project overview
```

## ⚙️ Configuration

### Environment Variables (.env file)
```env
# Database
DATABASE_URL=sqlite:///./email_assistant.db

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Backend Configuration
The backend automatically:
- Creates SQLite database on first run
- Sets up CORS for frontend connection
- Configures API routes and documentation

### Frontend Configuration
The frontend connects to:
- Backend API at `http://localhost:8000`
- Uses Tailwind CSS from CDN
- Alpine.js for reactivity

## 🔧 Development Setup

### IDE Configuration

#### VS Code Setup
1. Install Python extension
2. Select interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose: `./venv/bin/python` (or `.\venv\Scripts\python.exe` on Windows)
4. Install recommended extensions:
   - Python
   - Pylance
   - HTML/CSS/JS support

#### PyCharm Setup
1. Open project folder
2. Go to Settings → Project → Python Interpreter
3. Add interpreter from `venv` folder
4. Configure code style and formatting

### Development Commands
```bash
# Start backend with auto-reload
cd backend
uvicorn app:app --reload --port 8000

# Run tests (when available)
cd tests
python -m pytest

# Format code
black backend/app.py

# Check code quality
pylint backend/app.py
```

## 🐳 Docker Setup (Optional)

### Using Docker Compose
```bash
# Build and start containers
docker-compose up --build

# Stop containers
docker-compose down
```

### Manual Docker Build
```bash
# Build backend image
cd backend
docker build -t email-assistant-backend .

# Run backend container
docker run -p 8000:8000 email-assistant-backend

# Serve frontend with nginx
cd frontend
docker run -p 3000:80 -v $(pwd):/usr/share/nginx/html nginx:alpine
```

## 🌐 Production Deployment

### Backend Deployment
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or use uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Deployment
- Build optimized version with build tools
- Serve with nginx, Apache, or CDN
- Update backend URL in production

### Security Considerations
- Use HTTPS in production
- Set strong SECRET_KEY
- Enable authentication
- Configure firewall rules
- Use environment variables for secrets

## 📊 Database Setup

### SQLite (Default)
- Automatically created on first run
- Stored in `backend/email_assistant.db`
- No additional setup required

### PostgreSQL (Production)
```bash
# Install PostgreSQL driver
pip install psycopg2

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost/email_assistant
```

### MySQL (Alternative)
```bash
# Install MySQL driver
pip install mysqlclient

# Update DATABASE_URL in .env
DATABASE_URL=mysql://user:password@localhost/email_assistant
```

## 🔍 Verification

### Test Backend
```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Test endpoint
curl http://localhost:8000/api/dashboard
```

### Test Frontend
1. Open http://localhost:3000
2. Check browser console (F12) for errors
3. Verify connection indicator shows "Connected"
4. Test navigation between tabs

### Test Email Processing
1. Add email account in Accounts tab
2. Click "Process" button
3. Check for success messages
4. Verify emails appear in Emails tab

## 🆘 Common Setup Issues

### Python Version Issues
```bash
# Check Python version
python --version  # Should be 3.7+

# Use specific Python version
python3.9 -m venv venv
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Port Conflicts
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
uvicorn app:app --port 8001
```

### Permission Issues
```bash
# Fix permissions (macOS/Linux)
chmod +x scripts/*.py
sudo chown -R $USER:$USER email-assistant/

# Run as administrator (Windows)
# Right-click terminal → "Run as administrator"
```

## 📚 Next Steps

After successful setup:
1. Read [EMAIL_SETUP.md](EMAIL_SETUP.md) to configure email accounts
2. Check [API.md](API.md) for API documentation
3. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
4. Start processing your emails!

## 💡 Tips

- Always activate virtual environment before working
- Keep requirements.txt updated when adding packages
- Use version control (Git) for your changes
- Backup your database regularly
- Monitor logs for errors and performance