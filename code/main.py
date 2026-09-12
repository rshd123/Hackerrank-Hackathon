"""
main.py — Entry point for the Buy or Wait? financial agent

Reads dataset/requests.csv, processes each request, writes output.csv.
"""

import sys
from pathlib import Path

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent))

from agent import run_agent

if __name__ == "__main__":
    run_agent()
