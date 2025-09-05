#!/usr/bin/env python3
"""
Email Assistant FastAPI Backend - Production Ready
Uses config.py for all configuration management
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any

# Import configuration first
try:
    from config import (
        settings, 
        get_cors_config, 
        get_logging_config,
        validate_production_settings
    )
    print("✅ Configuration loaded successfully")
except ImportError as e:
    print(f"❌ Configuration import error: {e}")
    exit(1)

# Configure logging using config
logging.basicConfig(**get_logging_config())
logger = logging.getLogger(__name__)

# Validate production settings
if settings.is_production:
    try:
        validate_production_settings()
        logger.info("✅ Production settings validated")
    except ValueError as e:
        logger.error(f"❌ Production validation failed: {e}")
        if not settings.DEBUG:
            exit(1)

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Request, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.security import HTTPBearer
    from pydantic import BaseModel, EmailStr
    logger.info("✅ FastAPI imports successful")
except ImportError as e:
    logger.error(f"❌ FastAPI import error: {e}")
    exit(1)

# Rate limiting (optional)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_ENABLED = True
    logger.info("✅ Rate limiting enabled")
except ImportError:
    RATE_LIMITING_ENABLED = False
    logger.warning("⚠️ Rate limiting disabled (slowapi not installed)")

# Error tracking (optional)
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastAPIIntegration
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastAPIIntegration(auto_enable=True)],
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.ENVIRONMENT
        )
        logger.info("✅ Sentry error tracking enabled")
    except ImportError:
        logger.warning("⚠️ Sentry not available (sentry-sdk not installed)")

# Standard library imports
import email
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
import re
import json
import sqlite3
import hashlib
import os
from pathlib import Path

# App lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database: {settings.DATABASE_URL.split('://')[0]}")
    
    # Initialize database
    init_db()
    
    yield
    
    # Shutdown
    logger.info(f"🛑 {settings.APP_NAME} shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan
)

# Security middleware
if not settings.is_development:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.TRUSTED_HOSTS
    )

# CORS middleware
cors_config = get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Rate limiting middleware
if RATE_LIMITING_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security (optional API key)
security = HTTPBearer(auto_error=False) if settings.API_KEY else None

async def verify_api_key(token: Optional[str] = Depends(security)):
    """Verify API key if configured"""
    if settings.API_KEY:
        if not token or token.credentials != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return token

# Database initialization
def init_db():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect('email_assistant.db')
        c = conn.cursor()
        
        # Create tables
        c.execute('''CREATE TABLE IF NOT EXISTS emails
                     (id TEXT PRIMARY KEY, subject TEXT, sender TEXT, content TEXT,
                      category TEXT, priority INTEGER, processed_at TIMESTAMP,
                      action_items TEXT, deadlines TEXT, sentiment TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS email_accounts
                     (id INTEGER PRIMARY KEY, email TEXT, password TEXT, 
                      imap_server TEXT, smtp_server TEXT, user_id TEXT)''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

# Pydantic models
class EmailAccount(BaseModel):
    email: EmailStr
    password: str
    imap_server: str = settings.GMAIL_IMAP_SERVER
    smtp_server: str = settings.GMAIL_SMTP_SERVER

class EmailData(BaseModel):
    subject: str
    sender: str
    content: str
    received_at: datetime

class ProcessedEmail(BaseModel):
    id: str
    subject: str
    sender: str
    content: str
    category: str
    priority: int
    action_items: List[str]
    deadlines: List[Dict[str, Any]]
    sentiment: str
    suggested_response: Optional[str] = None

# Email processor class (same as before but with config integration)
class EmailProcessor:
    def __init__(self):
        self.categories = {
            'urgent': ['urgent', 'asap', 'immediately', 'deadline', 'critical'],
            'meeting': ['meeting', 'call', 'conference', 'zoom', 'teams'],
            'project': ['project', 'task', 'deliverable', 'milestone'],
            'invoice': ['invoice', 'payment', 'billing', 'receipt'],
            'personal': ['personal', 'family', 'friend'],
            'newsletter': ['newsletter', 'unsubscribe', 'marketing'],
            'support': ['support', 'help', 'issue', 'problem', 'bug']
        }
        
        # Use config settings
        self.max_content_length = settings.MAX_EMAIL_CONTENT_LENGTH
        self.max_subject_length = settings.MAX_SUBJECT_LENGTH
        
    def categorize_email(self, content: str, subject: str) -> str:
        # Truncate content if too long
        content = content[:self.max_content_length]
        subject = subject[:self.max_subject_length]
        
        text = (content + " " + subject).lower()
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            category_scores[category] = score
            
        if max(category_scores.values()) == 0:
            return 'general'
        
        return max(category_scores, key=category_scores.get)
    
    def extract_action_items(self, content: str) -> List[str]:
        action_patterns = [
            r'(?:please|can you|could you|need to|should|must|have to)\s+([^.!?]*)',
            r'(?:action item|todo|task):\s*([^.!?\n]*)',
            r'(?:follow up|complete|finish|deliver)\s+([^.!?]*)'
        ]
        
        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, content.lower())
            actions.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(actions))[:5]  # Limit to 5 most relevant actions
    
    def extract_deadlines(self, content: str) -> List[Dict[str, Any]]:
        deadline_patterns = [
            r'(?:by|due|deadline|before)\s+(\w+day|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{1,2}\s+\w+|\w+\s+\d{1,2})',
            r'(\w+day)\s+(?:at|by)\s+(\d{1,2}:\d{2})',
            r'(?:end of|eod)\s+(\w+day|\w+)',
        ]
        
        deadlines = []
        for pattern in deadline_patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                if isinstance(match, tuple):
                    deadline_text = ' '.join(match)
                else:
                    deadline_text = match
                
                deadlines.append({
                    'text': deadline_text,
                    'extracted_at': datetime.now().isoformat(),
                    'priority': 'high' if any(word in deadline_text for word in ['urgent', 'asap', 'immediately']) else 'medium'
                })
        
        return deadlines[:3]  # Limit to 3 most relevant deadlines
    
    def analyze_sentiment(self, content: str) -> str:
        positive_words = ['thank', 'great', 'excellent', 'good', 'pleased', 'happy']
        negative_words = ['urgent', 'problem', 'issue', 'concern', 'disappointed', 'angry']
        
        content_lower = content.lower()
        positive_score = sum(1 for word in positive_words if word in content_lower)
        negative_score = sum(1 for word in negative_words if word in content_lower)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def calculate_priority(self, category: str, sentiment: str, has_deadlines: bool) -> int:
        base_priority = {
            'urgent': 5,
            'support': 4,
            'meeting': 4,
            'project': 3,
            'invoice': 3,
            'personal': 2,
            'newsletter': 1,
            'general': 2
        }.get(category, 2)
        
        if sentiment == 'negative':
            base_priority += 1
        if has_deadlines:
            base_priority += 1
            
        return min(base_priority, 5)
    
    def generate_response_template(self, category: str, sentiment: str, action_items: List[str]) -> str:
        if not settings.ENABLE_RESPONSE_GENERATION:
            return ""
            
        templates = {
            'urgent': "Thank you for your urgent message. I understand the importance and will prioritize this accordingly.",
            'meeting': "Thank you for the meeting invitation/request. I'll check my calendar and get back to you shortly.",
            'support': "Thank you for reaching out. I'll look into this issue and provide an update as soon as possible.",
            'invoice': "Thank you for the invoice/billing information. I'll process this accordingly.",
            'project': "Thank you for the project update. I'll review the details and respond with any questions or next steps."
        }
        
        base_response = templates.get(category, "Thank you for your email. I'll review this and get back to you soon.")
        
        if action_items:
            base_response += f"\n\nI note the following action items:\n" + "\n".join([f"- {item}" for item in action_items[:3]])
        
        return base_response

processor = EmailProcessor()

# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Health check endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": f"{settings.APP_NAME} API is running",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "dashboard": "/api/dashboard",
            "emails": "/api/emails",
            "accounts": "/api/accounts",
            "health": "/health",
            "docs": "/docs" if settings.ENABLE_DOCS else None
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        conn = sqlite3.connect('email_assistant.db')
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# Account management endpoints
@app.post("/api/accounts", response_model=dict)
async def add_email_account(
    account: EmailAccount, 
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Add an email account for processing"""
    try:
        # Test connection with timeout
        imap = imaplib.IMAP4_SSL(account.imap_server)
        imap.sock.settimeout(settings.IMAP_CONNECTION_TIMEOUT)
        imap.login(account.email, account.password)
        imap.logout()
        
        # Store account (in production, encrypt passwords!)
        conn = sqlite3.connect('email_assistant.db')
        c = conn.cursor()
        c.execute('''INSERT INTO email_accounts (email, password, imap_server, smtp_server, user_id)
                     VALUES (?, ?, ?, ?, ?)''',
                  (account.email, account.password, account.imap_server, account.smtp_server, "user1"))
        conn.commit()
        account_id = c.lastrowid
        conn.close()
        
        logger.info(f"Email account added successfully: {account.email}")
        return {
            "status": "success", 
            "account_id": account_id, 
            "message": "Email account added successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to add email account {account.email}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to add account: {str(e)}")

@app.get("/api/accounts")
async def get_email_accounts(api_key: Optional[str] = Depends(verify_api_key)):
    """Get all email accounts"""
    try:
        conn = sqlite3.connect('email_assistant.db')
        c = conn.cursor()
        c.execute("SELECT id, email, imap_server, smtp_server FROM email_accounts")
        accounts = [
            {
                "id": row[0], 
                "email": row[1], 
                "imap_server": row[2], 
                "smtp_server": row[3]
            } 
            for row in c.fetchall()
        ]
        conn.close()
        return accounts
        
    except Exception as e:
        logger.error(f"Failed to fetch email accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch accounts")

# Email processing endpoints
def apply_rate_limit(endpoint_name: str):
    """Apply rate limiting if enabled"""
    if RATE_LIMITING_ENABLED:
        if endpoint_name == "process_emails":
            return limiter.limit(f"{settings.EMAIL_PROCESS_RATE_LIMIT}/minute")
        elif endpoint_name == "general":
            return limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
    return lambda f: f

@app.post("/api/process-emails/{account_id}")
@apply_rate_limit("process_emails")
async def process_emails(
    request: Request,
    account_id: int, 
    limit: int = None,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Fetch and process emails from specified account"""
    if not settings.ENABLE_EMAIL_PROCESSING:
        raise HTTPException(status_code=503, detail="Email processing is disabled")
    
    # Apply batch size limits
    if limit is None:
        limit = settings.EMAIL_BATCH_SIZE
    limit = min(limit, settings.MAX_EMAIL_BATCH_SIZE)
    
    try:
        # Get account details
        conn = sqlite3.connect('email_assistant.db')
        c = conn.cursor()
        c.execute("SELECT email, password, imap_server FROM email_accounts WHERE id = ?", (account_id,))
        account = c.fetchone()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        email_addr, password, imap_server = account
        logger.info(f"Processing emails for account: {email_addr}")
        
        # Connect to email server with timeout
        imap = imaplib.IMAP4_SSL(imap_server)
        imap.sock.settimeout(settings.IMAP_CONNECTION_TIMEOUT)
        imap.login(email_addr, password)
        imap.select('INBOX')
        
        # Search for recent emails
        status, messages = imap.search(None, 'UNSEEN')
        email_ids = messages[0].split()[-limit:]  # Get last N emails
        
        processed_emails = []
        
        for email_id in email_ids:
            try:
                status, msg_data = imap.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email content
                subject = email_message['Subject'] or "No Subject"
                sender = email_message['From'] or "Unknown Sender"
                
                # Truncate subject if too long
                subject = subject[:settings.MAX_SUBJECT_LENGTH]
                
                # Get email body
                content = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                # Truncate content if too long
                content = content[:settings.MAX_EMAIL_CONTENT_LENGTH]
                
                # Process email
                email_hash = hashlib.md5(f"{sender}{subject}{content[:100]}".encode()).hexdigest()
                
                category = processor.categorize_email(content, subject)
                action_items = processor.extract_action_items(content)
                deadlines = processor.extract_deadlines(content)
                sentiment = processor.analyze_sentiment(content)
                priority = processor.calculate_priority(category, sentiment, len(deadlines) > 0)
                suggested_response = processor.generate_response_template(category, sentiment, action_items)
                
                processed_email = ProcessedEmail(
                    id=email_hash,
                    subject=subject,
                    sender=sender,
                    content=content[:500] + "..." if len(content) > 500 else content,
                    category=category,
                    priority=priority,
                    action_items=action_items,
                    deadlines=deadlines,
                    sentiment=sentiment,
                    suggested_response=suggested_response
                )
                
                # Store in database
                c.execute('''INSERT OR REPLACE INTO emails 
                             (id, subject, sender, content, category, priority, processed_at, 
                              action_items, deadlines, sentiment)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (email_hash, subject, sender, content, category, priority,
                           datetime.now().isoformat(), json.dumps(action_items),
                           json.dumps(deadlines), sentiment))
                
                processed_emails.append(processed_email)
                
            except Exception as e:
                logger.error(f"Error processing individual email: {e}")
                continue  # Skip this email and continue with others
        
        conn.commit()
        conn.close()
        imap.logout()
        
        logger.info(f"Successfully processed {len(processed_emails)} emails for {email_addr}")
        return {
            "status": "success",
            "processed_count": len(processed_emails),
            "emails": processed_emails
        }
        
    except Exception as e:
        logger.error(f"Error processing emails for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing emails: {str(e)}")

# Email retrieval endpoints
@app.get("/api/emails")
@apply_rate_limit("general")
async def get_processed_emails(
    request: Request,
    category: Optional[str] = None, 
    priority: Optional[int] = None,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Get processed emails with optional filtering"""
    try:
        conn = sqlite3.connect('email_assistant.db')
        c = conn.cursor()
        
        query = "SELECT * FROM emails WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if priority:
            query += " AND priority >= ?"
            params.append(priority)
        
        query += " ORDER BY processed_at DESC"
        
        c.execute(query, params)
        emails = []
        
        for row in c.fetchall():
            emails.append({
                "id": row[0],
                "subject": row[1],
                "sender": row[2],
                "content": row[3],
                "category": row[4],
                "priority": row[5],
                "processed_at": row[6],
                "action_items": json.loads(row[7]) if row[7] else [],
                "deadlines": json.loads(row[8]) if row[8] else [],
                "sentiment": row[9]
            })
        
        conn.close()
        return emails
        
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail="Error fetching emails")

# Dashboard and analytics
@app.get("/api/dashboard")
@apply_rate_limit("general")
async def get_dashboard_stats(
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Get dashboard statistics"""
    if not settings.ENABLE_ANALYTICS:
        raise HTTPException(status_code=503, detail="Analytics is disabled")
    
    try:
        conn = sqlite3.connect('email_assistant.db')
        c = conn.cursor()
        
        # Total emails
        c.execute("SELECT COUNT(*) FROM emails")
        total_emails = c.fetchone()[0]
        
        # Category breakdown
        c.execute("SELECT category, COUNT(*) FROM emails GROUP BY category")
        categories = dict(c.fetchall())
        
        # Priority breakdown
        c.execute("SELECT priority, COUNT(*) FROM emails GROUP BY priority")
        priorities = dict(c.fetchall())
        
        # Recent activity (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        c.execute("SELECT COUNT(*) FROM emails WHERE processed_at > ?", (week_ago,))
        recent_activity = c.fetchone()[0]
        
        conn.close()
        
        return {
            "total_emails": total_emails,
            "categories": categories,
            "priorities": priorities,
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching dashboard statistics")

# Metrics endpoint (optional)
if settings.ENABLE_METRICS:
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus-style metrics endpoint"""
        try:
            conn = sqlite3.connect('email_assistant.db')
            c = conn.cursor()
            
            # Basic metrics
            c.execute("SELECT COUNT(*) FROM emails")
            total_emails = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM email_accounts")
            total_accounts = c.fetchone()[0]
            
            conn.close()
            
            metrics = [
                f"# HELP email_assistant_emails_total Total number of processed emails",
                f"# TYPE email_assistant_emails_total counter", 
                f"email_assistant_emails_total {total_emails}",
                f"# HELP email_assistant_accounts_total Total number of email accounts",
                f"# TYPE email_assistant_accounts_total gauge",
                f"email_assistant_accounts_total {total_accounts}",
            ]
            
            return "\n".join(metrics)
            
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            raise HTTPException(status_code=500, detail="Error generating metrics")

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn based on settings
    uvicorn_config = {
        "app": app,
        "host": settings.HOST,
        "port": settings.PORT,
        "log_level": settings.LOG_LEVEL.lower(),
        "access_log": settings.ACCESS_LOG,
        "reload": settings.DEV_RELOAD and settings.is_development,
    }
    
    logger.info(f"Starting {settings.APP_NAME} on {settings.HOST}:{settings.PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    uvicorn.run(**uvicorn_config)