#!/bin/bash

# Railway Deployment Automation Script
# This script helps automate the deployment process to Railway

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_warning "Railway CLI not found. Installing..."
        npm install -g @railway/cli
        print_success "Railway CLI installed"
    else
        print_success "Railway CLI found"
    fi
}

check_git() {
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi
    print_success "Git found"
}

setup_git_repo() {
    print_header "Setting up Git Repository"
    
    if [ ! -d ".git" ]; then
        print_warning "Git repository not initialized. Initializing..."
        git init
        git add .
        git commit -m "Initial commit: FreightHero Watchtower v0.1.0"
        print_success "Git repository initialized"
    else
        print_success "Git repository already exists"
    fi
    
    echo ""
    echo "Enter your GitHub repository URL:"
    echo "Format: https://github.com/YOUR_USERNAME/freighthero-watchtower.git"
    read -p "> " repo_url
    
    git remote add origin "$repo_url" || print_warning "Remote 'origin' already exists"
    print_success "Remote repository added"
}

push_to_github() {
    print_header "Pushing to GitHub"
    
    git branch -M main
    git push -u origin main
    
    print_success "Code pushed to GitHub"
}

login_railway() {
    print_header "Login to Railway"
    
    railway login
    
    print_success "Logged in to Railway"
}

create_railway_project() {
    print_header "Creating Railway Project"
    
    railway init --name freighthero-watchtower
    
    print_success "Railway project created"
}

deploy_backend() {
    print_header "Deploying Backend"
    
    print_warning "Make sure you have:"
    echo "1. PostgreSQL service with PGVector added"
    echo "2. Redis service added"
    echo "3. Environment variables configured"
    echo ""
    
    read -p "Press Enter to continue..."
    
    railway up --service freighthero-backend
    
    print_success "Backend deployed"
}

deploy_frontend() {
    print_header "Deploying Frontend"
    
    railway up --service freighthero-frontend --path ./console
    
    print_success "Frontend deployed"
}

check_deployment() {
    print_header "Checking Deployment Status"
    
    railway logs
    
    print_success "Deployment check complete"
}

# Main script
main() {
    print_header "FreightHero Watchtower - Railway Deployment"
    
    echo ""
    echo "This script will help you deploy to Railway."
    echo ""
    echo "Prerequisites:"
    echo "1. Railway account (https://railway.app)"
    echo "2. GitHub account"
    echo "3. OpenRouter API key"
    echo ""
    
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    # Step 1: Check prerequisites
    print_header "Step 1: Checking Prerequisites"
    check_git
    check_railway_cli
    
    # Step 2: Setup Git
    print_header "Step 2: Git Setup"
    setup_git_repo
    push_to_github
    
    # Step 3: Login to Railway
    print_header "Step 3: Railway Login"
    login_railway
    
    # Step 4: Create Railway Project
    print_header "Step 4: Create Railway Project"
    create_railway_project
    
    # Step 5: Deploy Services
    print_header "Step 5: Deploy Services"
    echo "Note: You'll need to manually add PostgreSQL and Redis in Railway dashboard"
    echo "1. Go to https://railway.app"
    echo "2. Add PostgreSQL database"
    echo "3. Add Redis database"
    echo "4. Set environment variables (see .env.railway.example)"
    echo ""
    
    read -p "Have you added the databases? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy_backend
        deploy_frontend
    else
        print_warning "Please add databases first, then run: railway up"
    fi
    
    # Step 6: Check Deployment
    print_header "Step 6: Deployment Status"
    check_deployment
    
    # Final
    print_header "Deployment Complete!"
    
    echo ""
    echo "Your application is now deployed!"
    echo ""
    echo "Next steps:"
    echo "1. Check logs: railway logs"
    echo "2. View dashboard: railway open"
    echo "3. Set custom domain: railway domain"
    echo ""
    echo "Backend URL: https://freighthero-backend.railway.app"
    echo "Frontend URL: https://freighthero-frontend.railway.app"
    echo ""
    print_success "Happy deploying! 🚀"
}

# Run main function
main
