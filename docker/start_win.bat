@echo off
setlocal

echo Starting AgentChat Docker services...

REM Create directories
echo Creating directories...
if not exist "mysql\init" mkdir mysql\init

REM Start services
echo Building and starting services...
docker compose up --build -d

REM Wait for startup
echo Waiting for services to start...
timeout /t 10 >nul

REM Show status
echo Checking service status...
docker compose ps

echo.
echo AgentChat started successfully!
echo.
echo Access URLs:
echo Frontend: http://localhost:8090
echo Backend API: http://localhost:7860
echo API Docs: http://localhost:7860/docs
echo.
echo View logs:
echo docker compose logs -f
echo.
echo Stop services:
echo docker compose down
echo.

pause