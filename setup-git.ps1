# Git Setup Script
# Run this to commit and push all code to GitHub

# Stage all files
git add -A

# Commit with message
git commit -m "Complete BOT GPT Backend: FastAPI + MongoDB + Groq LLM + RAG + Tests + Docker + CI/CD"

# Show commit log
git log --oneline -5

# Instructions for pushing
Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Green
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor Yellow
Write-Host "   - Go to https://github.com/new" -ForegroundColor Cyan
Write-Host "   - Repository name: bot-gpt-backend" -ForegroundColor Cyan
Write-Host "   - Make it Public" -ForegroundColor Cyan
Write-Host "   - Do NOT initialize with README" -ForegroundColor Cyan
Write-Host "`n2. Then run these commands:" -ForegroundColor Yellow
Write-Host "   git remote add origin https://github.com/Fawad1121/bot-gpt-backend.git" -ForegroundColor Cyan
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
