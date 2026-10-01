"""
Synapse Backend Server Launcher
Runs FastAPI backend on port 8000 using Uvicorn.
"""

import uvicorn
from backend.database import init_db

if __name__ == "__main__":
    init_db(reset=False)
    print("Starting Synapse Backend API on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.api:app", host="127.0.0.1", port=8000, reload=False)
