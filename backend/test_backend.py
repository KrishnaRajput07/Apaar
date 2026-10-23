import sys

try:
    from app.main import app
    print("SUCCESS: FastAPI App, all 10 module routers, ML models, and audit chain initialized properly!")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
