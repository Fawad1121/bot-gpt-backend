@echo off
echo ===== Checking Git Status =====
git status

echo.
echo ===== Checking Commits =====
git log --oneline -5

echo.
echo ===== Checking Remote =====
git remote -v

echo.
echo ===== Checking Branch =====
git branch -a

echo.
echo ===== Attempting Push =====
git push -u origin main --verbose

echo.
echo ===== Done =====
pause
