#!/bin/bash

# Activate virtual environment and run the application
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
