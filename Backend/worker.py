#!/usr/bin/env python3
"""Celery worker startup script."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.start()
