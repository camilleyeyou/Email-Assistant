#!/usr/bin/env python3
"""
Email Assistant FastAPI Backend - Complete Railway Production Version
Serves both API and frontend from one Railway service with embedded HTML
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os

# Import configuration with error handling
try:
    from config import settings, get_cors_config, get_logging_config
    print("✅ Configuration loaded successfully")
except ImportError as e:
    print(f"❌ Configuration import error: {e}")
    exit(1)

# Configure logging using config (with fallback)
try:
    logging.basicConfig(**get_logging_config())
except:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

logger = logging.getLogger(__name__)

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Request, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, HTMLResponse
    from pydantic import BaseModel, EmailStr
    logger.info("✅ FastAPI imports successful")
except ImportError as e:
    logger.error(f"❌ FastAPI import error: {e}")
    exit(1)

# Rate limiting (optional - only if available)
RATE_LIMITING_ENABLED = False
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_ENABLED = True
    logger.info("✅ Rate limiting enabled")
except ImportError:
    logger.warning("⚠️ Rate limiting disabled (slowapi not installed)")

# Error tracking (optional - only if configured and available)
if hasattr(settings, 'SENTRY_DSN') and getattr(settings, 'SENTRY_DSN'):
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastAPIIntegration
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastAPIIntegration(auto_enable=True)],
            traces_sample_rate=getattr(settings, 'SENTRY_TRACES_SAMPLE_RATE', 0.1),
            environment=getattr(settings, 'ENVIRONMENT', 'development')
        )
        logger.info("✅ Sentry error tracking enabled")
    except ImportError:
        logger.warning("⚠️ Sentry not available (sentry-sdk not installed)")
else:
    logger.info("ℹ️ Sentry error tracking disabled")

# Standard library imports
import email
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import json
import sqlite3
import hashlib
from pathlib import Path

# Embedded Frontend HTML
FRONTEND_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        [x-cloak] { display: none !important; }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .glass { backdrop-filter: blur(16px); background: rgba(255, 255, 255, 0.1); }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div x-data="emailAssistant()" x-init="init()" class="min-h-screen">
        <!-- Navigation -->
        <nav class="gradient-bg text-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex items-center justify-between h-16">
                    <div class="flex items-center">
                        <i class="fas fa-envelope text-2xl mr-3"></i>
                        <h1 class="text-xl font-bold">Email Assistant</h1>
                    </div>
                    <div class="flex space-x-4">
                        <button 
                            @click="activeTab = 'dashboard'" 
                            :class="activeTab === 'dashboard' ? 'bg-white bg-opacity-20' : ''"
                            class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-white hover:bg-opacity-10">
                            <i class="fas fa-chart-pie mr-2"></i>Dashboard
                        </button>
                        <button 
                            @click="activeTab = 'emails'" 
                            :class="activeTab === 'emails' ? 'bg-white bg-opacity-20' : ''"
                            class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-white hover:bg-opacity-10">
                            <i class="fas fa-inbox mr-2"></i>Emails
                        </button>
                        <button 
                            @click="activeTab = 'accounts'" 
                            :class="activeTab === 'accounts' ? 'bg-white bg-opacity-20' : ''"
                            class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-white hover:bg-opacity-10">
                            <i class="fas fa-user-cog mr-2"></i>Accounts
                        </button>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Dashboard Tab -->
            <div x-show="activeTab === 'dashboard'" x-cloak>
                <div class="mb-8">
                    <h2 class="text-3xl font-bold text-gray-900 mb-2">Dashboard</h2>
                    <p class="text-gray-600">Email processing overview and analytics</p>
                </div>

                <!-- Stats Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
                        <div class="flex items-center justify-between">
                            <div>
                                <p class="text-sm font-medium text-gray-600">Total Emails</p>
                                <p class="text-3xl font-bold text-gray-900" x-text="stats.total_emails || 0"></p>
                            </div>
                            <div class="p-3 bg-blue-100 rounded-full">
                                <i class="fas fa-envelope text-blue-500"></i>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
                        <div class="flex items-center justify-between">
                            <div>
                                <p class="text-sm font-medium text-gray-600">Recent Activity</p>
                                <p class="text-3xl font-bold text-gray-900" x-text="stats.recent_activity || 0"></p>
                            </div>
                            <div class="p-3 bg-green-100 rounded-full">
                                <i class="fas fa-clock text-green-500"></i>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow-lg p-6 border-l-4 border-yellow-500">
                        <div class="flex items-center justify-between">
                            <div>
                                <p class="text-sm font-medium text-gray-600">High Priority</p>
                                <p class="text-3xl font-bold text-gray-900" x-text="(stats.priorities && stats.priorities['5']) || 0"></p>
                            </div>
                            <div class="p-3 bg-yellow-100 rounded-full">
                                <i class="fas fa-exclamation-triangle text-yellow-500"></i>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
                        <div class="flex items-center justify-between">
                            <div>
                                <p class="text-sm font-medium text-gray-600">Categories</p>
                                <p class="text-3xl font-bold text-gray-900" x-text="Object.keys(stats.categories || {}).length"></p>
                            </div>
                            <div class="p-3 bg-purple-100 rounded-full">
                                <i class="fas fa-tags text-purple-500"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Charts Section -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <!-- Category Distribution -->
                    <div class="bg-white rounded-xl shadow-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Email Categories</h3>
                        <div class="space-y-3">
                            <template x-for="[category, count] in Object.entries(stats.categories || {})" :key="category">
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-medium text-gray-700 capitalize" x-text="category"></span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-32 bg-gray-200 rounded-full h-2">
                                            <div class="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" 
                                                 :style="`width: ${(count / Math.max(...Object.values(stats.categories || {}))) * 100}%`"></div>
                                        </div>
                                        <span class="text-sm font-bold text-gray-900" x-text="count"></span>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Priority Distribution -->
                    <div class="bg-white rounded-xl shadow-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Priority Levels</h3>
                        <div class="space-y-3">
                            <template x-for="[priority, count] in Object.entries(stats.priorities || {})" :key="priority">
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-medium text-gray-700">
                                        Priority <span x-text="priority"></span>
                                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ml-2"
                                              :class="priority >= 4 ? 'bg-red-100 text-red-800' : priority >= 3 ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'">
                                            <span x-text="priority >= 4 ? 'High' : priority >= 3 ? 'Medium' : 'Low'"></span>
                                        </span>
                                    </span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-32 bg-gray-200 rounded-full h-2">
                                            <div :class="priority >= 4 ? 'bg-red-500' : priority >= 3 ? 'bg-yellow-500' : 'bg-green-500'" 
                                                 class="h-2 rounded-full" 
                                                 :style="`width: ${(count / Math.max(...Object.values(stats.priorities || {}))) * 100}%`"></div>
                                        </div>
                                        <span class="text-sm font-bold text-gray-900" x-text="count"></span>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Emails Tab -->
            <div x-show="activeTab === 'emails'" x-cloak>
                <div class="flex items-center justify-between mb-8">
                    <div>
                        <h2 class="text-3xl font-bold text-gray-900 mb-2">Email Management</h2>
                        <p class="text-gray-600">Process and manage your emails efficiently</p>
                    </div>
                    <button @click="processEmails()" 
                            :disabled="processing"
                            class="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-3 rounded-lg shadow-lg transition-all duration-200 disabled:opacity-50">
                        <i class="fas fa-sync-alt mr-2" :class="{'animate-spin': processing}"></i>
                        <span x-text="processing ? 'Processing...' : 'Process Emails'"></span>
                    </button>
                </div>

                <!-- Empty State -->
                <div x-show="emails.length === 0" class="text-center py-12">
                    <i class="fas fa-inbox text-gray-400 text-6xl mb-4"></i>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No emails found</h3>
                    <p class="text-gray-600">Add an email account and process some emails to see results.</p>
                </div>
            </div>

            <!-- Accounts Tab -->
            <div x-show="activeTab === 'accounts'" x-cloak>
                <div class="mb-8">
                    <h2 class="text-3xl font-bold text-gray-900 mb-2">Email Accounts</h2>
                    <p class="text-gray-600">Manage your email accounts for processing</p>
                </div>

                <!-- Add Account Form -->
                <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Add New Account</h3>
                    <form @submit.prevent="addAccount()" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                                <input type="email" x-model="newAccount.email" required
                                       class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Password</label>
                                <input type="password" x-model="newAccount.password" required
                                       class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">IMAP Server</label>
                                <input type="text" x-model="newAccount.imap_server" placeholder="imap.gmail.com"
                                       class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">SMTP Server</label>
                                <input type="text" x-model="newAccount.smtp_server" placeholder="smtp.gmail.com"
                                       class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                            </div>
                        </div>
                        <button type="submit" :disabled="addingAccount"
                                class="bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 text-white px-6 py-2 rounded-lg shadow-lg transition-all duration-200 disabled:opacity-50">
                            <i class="fas fa-plus mr-2" :class="{'animate-spin': addingAccount}"></i>
                            <span x-text="addingAccount ? 'Adding...' : 'Add Account'"></span>
                        </button>
                    </form>
                </div>

                <!-- Accounts List -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <template x-for="account in accounts" :key="account.id">
                        <div class="bg-white rounded-xl shadow-lg p-6">
                            <div class="flex items-center justify-between mb-4">
                                <div class="flex items-center space-x-3">
                                    <div class="p-3 bg-blue-100 rounded-full">
                                        <i class="fas fa-envelope text-blue-500"></i>
                                    </div>
                                    <div>
                                        <h3 class="font-semibold text-gray-900" x-text="account.email"></h3>
                                        <p class="text-sm text-gray-600" x-text="account.imap_server"></p>
                                    </div>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                        Active
                                    </span>
                                </div>
                            </div>
                            <div class="flex space-x-2">
                                <button @click="processAccountEmails(account.id)" 
                                        class="flex-1 bg-blue-50 hover:bg-blue-100 text-blue-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200">
                                    <i class="fas fa-sync-alt mr-1"></i>Process
                                </button>
                            </div>
                        </div>
                    </template>

                    <!-- Empty State -->
                    <div x-show="accounts.length === 0" class="col-span-full text-center py-12">
                        <i class="fas fa-user-plus text-gray-400 text-6xl mb-4"></i>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">No accounts configured</h3>
                        <p class="text-gray-600">Add an email account to start processing emails.</p>
                    </div>
                </div>
            </div>
        </main>

        <!-- Notifications -->
        <div x-show="notification.show" x-cloak 
             class="fixed top-4 right-4 bg-white rounded-lg shadow-lg p-4 border-l-4 z-50 transition-all duration-300"
             :class="notification.type === 'success' ? 'border-green-500' : 'border-red-500'">
            <div class="flex items-center">
                <i :class="notification.type === 'success' ? 'fas fa-check-circle text-green-500' : 'fas fa-exclamation-circle text-red-500'" class="mr-3"></i>
                <p class="text-sm font-medium text-gray-900" x-text="notification.message"></p>
            </div>
        </div>
    </div>

    <script>
        function emailAssistant() {
            return {
                // Configuration
                backendUrl: window.location.origin,
                
                // State
                activeTab: 'dashboard',
                stats: {},
                emails: [],
                accounts: [],
                processing: false,
                addingAccount: false,
                filters: {
                    category: '',
                    priority: ''
                },
                newAccount: {
                    email: '',
                    password: '',
                    imap_server: 'imap.gmail.com',
                    smtp_server: 'smtp.gmail.com'
                },
                notification: {
                    show: false,
                    message: '',
                    type: 'success'
                },

                async init() {
                    await this.fetchDashboardStats();
                    await this.fetchAccounts();
                    await this.fetchEmails();
                },

                async fetchDashboardStats() {
                    try {
                        const response = await fetch(`${this.backendUrl}/api/dashboard`);
                        this.stats = await response.json();
                    } catch (error) {
                        console.error('Error fetching dashboard stats:', error);
                    }
                },

                async fetchEmails() {
                    try {
                        const response = await fetch(`${this.backendUrl}/api/emails`);
                        this.emails = await response.json();
                    } catch (error) {
                        console.error('Error fetching emails:', error);
                    }
                },

                async fetchAccounts() {
                    try {
                        const response = await fetch(`${this.backendUrl}/api/accounts`);
                        this.accounts = await response.json();
                    } catch (error) {
                        console.error('Error fetching accounts:', error);
                    }
                },

                async addAccount() {
                    this.addingAccount = true;
                    try {
                        const response = await fetch(`${this.backendUrl}/api/accounts`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(this.newAccount)
                        });
                        
                        const result = await response.json();
                        
                        if (response.ok) {
                            this.showNotification('Account added successfully!', 'success');
                            this.newAccount = {
                                email: '',
                                password: '',
                                imap_server: 'imap.gmail.com',
                                smtp_server: 'smtp.gmail.com'
                            };
                            await this.fetchAccounts();
                        } else {
                            this.showNotification(result.detail || 'Failed to add account', 'error');
                        }
                    } catch (error) {
                        this.showNotification('Error adding account', 'error');
                    } finally {
                        this.addingAccount = false;
                    }
                },

                async processEmails() {
                    if (this.accounts.length === 0) {
                        this.showNotification('Please add an email account first', 'error');
                        return;
                    }

                    this.processing = true;
                    try {
                        const accountId = this.accounts[0].id;
                        const response = await fetch(`${this.backendUrl}/api/process-emails/${accountId}`, {
                            method: 'POST'
                        });
                        
                        const result = await response.json();
                        
                        if (response.ok) {
                            this.showNotification(`Processed ${result.processed_count} emails successfully!`, 'success');
                            await this.fetchEmails();
                            await this.fetchDashboardStats();
                        } else {
                            this.showNotification(result.detail || 'Failed to process emails', 'error');
                        }
                    } catch (error) {
                        this.showNotification('Error processing emails', 'error');
                    } finally {
                        this.processing = false;
                    }
                },

                async processAccountEmails(accountId) {
                    this.processing = true;
                    try {
                        const response = await fetch(`${this.backendUrl}/api/process-emails/${accountId}`, {
                            method: 'POST'
                        });
                        
                        const result = await response.json();
                        
                        if (response.ok) {
                            this.showNotification(`Processed ${result.processed_count} emails successfully!`, 'success');
                            await this.fetchEmails();
                            await this.fetchDashboardStats();
                        } else {
                            this.showNotification(result.detail || 'Failed to process emails', 'error');
                        }
                    } catch (error) {
                        this.showNotification('Error processing emails', 'error');
                    } finally {
                        this.processing = false;
                    }
                },

                showNotification(message, type = 'success') {
                    this.notification = { show: true, message, type };
                    setTimeout(() => {
                        this.notification.show = false;
                    }, 5000);
                }
            }
        }
    </script>
</body>
</html>'''

# App lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"Environment: {getattr(settings, 'ENVIRONMENT', 'development')}")
    logger.info(f"Debug mode: {getattr(settings, 'DEBUG', True)}")
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
    description=getattr(settings, 'APP_DESCRIPTION', 'AI-powered email processing system'),
    docs_url=getattr(settings, 'DOCS_URL', '/docs'),
    redoc_url=getattr(settings, 'REDOC_URL', '/redoc'),
    lifespan=lifespan
)

# Security middleware (only if configured)
if hasattr(settings, 'TRUSTED_HOSTS') and not getattr(settings, 'is_development', True):
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)

# CORS middleware
try:
    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)
except:
    # Fallback CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, 'ALLOWED_ORIGINS', ["*"]),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# Rate limiting middleware (only if available)
if RATE_LIMITING_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    imap_server: str = getattr(settings, 'GMAIL_IMAP_SERVER', 'imap.gmail.com')
    smtp_server: str = getattr(settings, 'GMAIL_SMTP_SERVER', 'smtp.gmail.com')

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

# Email processor class
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
        
        # Use config settings with defaults
        self.max_content_length = getattr(settings, 'MAX_EMAIL_CONTENT_LENGTH', 10000)
        self.max_subject_length = getattr(settings, 'MAX_SUBJECT_LENGTH', 200)
        
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
        if not getattr(settings, 'ENABLE_RESPONSE_GENERATION', True):
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

# Rate limiting decorator (safe)
def safe_rate_limit(rate: str):
    """Apply rate limiting if available, otherwise do nothing"""
    def decorator(func):
        if RATE_LIMITING_ENABLED:
            return limiter.limit(rate)(func)
        return func
    return decorator

# Frontend serving endpoints
@app.get("/app", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend application"""
    return HTMLResponse(content=FRONTEND_HTML, status_code=200)

@app.get("/")
async def root():
    """Main landing page with navigation links"""
    return {
        "status": "healthy",
        "message": f"{settings.APP_NAME} v{settings.APP_VERSION}",
        "description": "AI-powered email processing and management system",
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "links": {
            "frontend": "/app",
            "api_health": "/health",
            "api_docs": "/docs" if getattr(settings, 'ENABLE_DOCS', True) else None,
            "dashboard": "/api/dashboard",
            "accounts": "/api/accounts"
        },
        "features": [
            "Smart email categorization",
            "Action item extraction", 
            "Deadline detection",
            "Sentiment analysis",
            "Response suggestions",
            "Analytics dashboard"
        ]
    }

# Health check endpoints
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
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "uptime": "running",
        "services": {
            "database": db_status,
            "rate_limiting": "enabled" if RATE_LIMITING_ENABLED else "disabled",
            "error_tracking": "enabled" if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN else "disabled",
            "frontend": "enabled"
        }
    }

# Account management endpoints
@app.post("/api/accounts", response_model=dict)
@safe_rate_limit("5/minute")
async def add_email_account(request: Request, account: EmailAccount):
    """Add an email account for processing"""
    try:
        # Test connection with timeout
        timeout = getattr(settings, 'IMAP_CONNECTION_TIMEOUT', 30)
        imap = imaplib.IMAP4_SSL(account.imap_server)
        imap.sock.settimeout(timeout)
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
async def get_email_accounts():
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
@app.post("/api/process-emails/{account_id}")
@safe_rate_limit("10/minute")
async def process_emails(request: Request, account_id: int, limit: int = None):
    """Fetch and process emails from specified account"""
    if not getattr(settings, 'ENABLE_EMAIL_PROCESSING', True):
        raise HTTPException(status_code=503, detail="Email processing is disabled")
    
    # Apply batch size limits
    if limit is None:
        limit = getattr(settings, 'EMAIL_BATCH_SIZE', 10)
    limit = min(limit, getattr(settings, 'MAX_EMAIL_BATCH_SIZE', 50))
    
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
        timeout = getattr(settings, 'IMAP_CONNECTION_TIMEOUT', 30)
        imap = imaplib.IMAP4_SSL(imap_server)
        imap.sock.settimeout(timeout)
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
                max_subject_length = getattr(settings, 'MAX_SUBJECT_LENGTH', 200)
                subject = subject[:max_subject_length]
                
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
                max_content_length = getattr(settings, 'MAX_EMAIL_CONTENT_LENGTH', 10000)
                content = content[:max_content_length]
                
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
async def get_processed_emails(category: Optional[str] = None, priority: Optional[int] = None):
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
async def get_dashboard_stats():
    """Get dashboard statistics"""
    if not getattr(settings, 'ENABLE_ANALYTICS', True):
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

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn based on settings
    port = int(os.getenv("PORT", getattr(settings, 'PORT', 8000)))
    host = getattr(settings, 'HOST', '0.0.0.0')
    log_level = getattr(settings, 'LOG_LEVEL', 'info').lower()
    
    logger.info(f"Starting {settings.APP_NAME} on {host}:{port}")
    logger.info(f"Environment: {getattr(settings, 'ENVIRONMENT', 'development')}")
    logger.info(f"Debug mode: {getattr(settings, 'DEBUG', True)}")
    logger.info(f"Frontend available at: /app")
    logger.info(f"API documentation at: /docs")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level=log_level,
        access_log=getattr(settings, 'ACCESS_LOG', True)
    )