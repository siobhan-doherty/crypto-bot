#!/usr/bin/env python3
"""
Development script to run FastAPI backend and Dash frontend locally.
This script is used for development purposes only and is not intended for production use.
Before running this script, make sure that the following services are running:
- MongoDB
- Kafka
Do not launch fastapi and dash containers.

Usage:
    ./run_api.py all       # Run both (in separate processes)
    ./run_api.py fastapi   # Run FastAPI backend only
    ./run_api.py dash      # Run Dash frontend only (FastAPI is run using uvicorn)
"""
import os
import sys
import subprocess
import threading
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables from .env file if it exists
load_dotenv()

def run_fastapi():
    """Run the FastAPI backend."""
    fastapi_dir = project_root / "src" / "api_user"
    os.chdir(str(fastapi_dir))
  
    # replace mongodb host with localhost
    os.environ["MONGO_URI"] = os.environ["MONGO_URI"].replace("@mongodb", "@localhost")
    
    print("\n🚀 Starting FastAPI backend on http://localhost:8000")
    
    # If we're being called as a subprocess, run uvicorn directly
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        import uvicorn
        uvicorn.run(
            "api_user.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(project_root / "src")],
            log_level="debug"
        )
        return
    
    # Otherwise, run as a subprocess
    cmd = [sys.executable, str(Path(__file__).resolve()), "api"]
    subprocess.run(cmd, env={"MONGO_INITDB_ROOT_USERNAME": mongo_user,
                              "MONGO_INITDB_ROOT_PASSWORD": mongo_pass,
                              "MONGO_HOST": mongo_host})

def run_dash():
    """Run the Dash frontend."""
    sys.path.insert(0, str(project_root))
    
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ.setdefault("API_BASE_URL", "http://localhost:8000/api")
    
    print("\n🚀 Starting Dash frontend on http://localhost:8050\n")
    
    from api_user.visualization import init_app
    app = init_app()
    app.run(debug=True, host="0.0.0.0", port=8050)

def wait_for_api():
    """Wait for the FastAPI server to be ready."""
    import time
    import requests
    from requests.exceptions import ConnectionError
    
    url = "http://localhost:8000/api/health"
    max_attempts = 30
    attempt = 0
    
    print("\n⏳ Waiting for FastAPI server to be ready...")
    while attempt < max_attempts:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print("✅ FastAPI server is ready!")
                return True
        except (ConnectionError, requests.exceptions.RequestException):
            pass
            
        attempt += 1
        time.sleep(1)
        if attempt % 5 == 0:
            print(f"   Waiting for FastAPI server... (attempt {attempt}/{max_attempts})")
    
    print("❌ Timed out waiting for FastAPI server")
    return False

def main():
    command = sys.argv[1]
    
    if command == "api":
        run_fastapi()
    elif command == "dash":
        run_dash()
    elif command == "all":
        api_process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "api"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        def print_output(stream, prefix):
            for line in iter(stream.readline, ''):
                print(f"{prefix} {line}", end='')
        
        stdout_thread = threading.Thread(
            target=print_output,
            args=(api_process.stdout, "[API]")
        )
        stderr_thread = threading.Thread(
            target=print_output,
            args=(api_process.stderr, "[API ERROR]")
        )
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()
        
        try:
            if wait_for_api():
                print("\n🚀 Starting Dash frontend...")
                run_dash()
            else:
                print("Failed to start FastAPI server")
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            api_process.terminate()
            api_process.wait()
            print("Cleanup complete.")

if __name__ == "__main__":
    main()
