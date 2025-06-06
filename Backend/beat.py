#!/usr/bin/env python3
"""Celery beat scheduler startup script."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.celery_app import celery_app
from celery.bin import beat

if __name__ == "__main__":
    # Start the Celery beat scheduler
    beat_app = beat.beat(app=celery_app)
    beat_app.run()
