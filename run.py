#!/usr/bin/env python
"""
GoShala Care - Application Server Entrypoint
"""
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f" * GoShala Care is running at: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
