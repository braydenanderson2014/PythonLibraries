import os
import sys
import json
import requests
from pathlib import Path
import numpy as np

def main():
    print("Testing imports...")
    print(f"OS: {os.name}")
    print(f"Python: {sys.version}")
    data = {"test": True}
    print(json.dumps(data))

if __name__ == "__main__":
    main()
