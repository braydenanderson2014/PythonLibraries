#!/usr/bin/env python3
"""Test file with various imports to test package detection."""

import requests
import numpy as np
from PIL import Image
import cv2
import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import os
import sys
import json
from datetime import datetime

# Some code using these packages
def main():
    response = requests.get("https://api.github.com")
    data = np.array([1, 2, 3, 4, 5])
    img = Image.new('RGB', (100, 100), color='red')
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    print(f"Current time: {datetime.now()}")

if __name__ == "__main__":
    main()
