# APAAR Pramaan — local dev startup script
# Starts: PostgreSQL + Redis + FastAPI backend (Docker), then Vite frontend
# Usage: powershell -ExecutionPolicy Bypass -File start-dev.ps1

Write-Host "`n=== APAAR Pramaan — Starting development environment ===`n" -ForegroundColor Cyan

# Step 1: Start Docker services (PostgreSQL + Redis + API + Mock APAAR)
Write-Host "Starting Docker services (PostgreSQL, Redis, API, Mock APAAR)..." -ForegroundColor Yellow
docker compose -f docker-compose.yml up -d db redis api apaar-mock

Write-Host "`nWaiting for database to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 2: Run the seeder
Write-Host "Seeding database with demo data..." -ForegroundColor Yellow
docker compose exec -T api python -m app.seed

# Step 3: Start the Vite dev server
Write-Host "`nStarting Vite dev server..." -ForegroundColor Yellow
Write-Host "Frontend will be at: http://localhost:5173" -ForegroundColor Green
Write-Host "API docs at:         http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Mock APAAR at:       http://localhost:8001/docs" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop the frontend. Use 'docker compose down' to stop backend.`n" -ForegroundColor Cyan

npm run dev
