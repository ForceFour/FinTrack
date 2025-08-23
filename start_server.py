"""Startup script for FinTrack API server"""

import uvicorn
import os
from src.api.main import app

def start_server():
    """Start the FinTrack API server"""
    print("🚀 Starting FinTrack API Server")
    print("=" * 40)
    print("🏦 Financial Transaction Analysis System")
    print("🤖 6-Agent Pipeline Ready")
    print()
    print("📡 Server will start at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 40)
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()
