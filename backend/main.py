"""
Main entry point for HospitAI API on Render.
This file imports the FastAPI app from api.py for deployment.
"""

from api import app

# This allows Render to find the app with: uvicorn main:app
