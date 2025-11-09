@echo off
REM Activate virtual environment and run the application
call .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
