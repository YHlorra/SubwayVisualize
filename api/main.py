import os
import sys
api_dir = os.path.dirname(os.path.abspath(__file__))
proj_root = os.path.dirname(api_dir)
sys.path.insert(0, api_dir)
sys.path.insert(0, proj_root)
from app import app

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
