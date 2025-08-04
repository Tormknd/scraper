#!/usr/bin/env python3

import subprocess
import sys
import os

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    packages = [
        "newspaper3k==0.2.8",
        "extruct==0.16.0", 
        "readability-lxml==0.8.1",
        "lxml==4.9.3",
        "selenium==4.15.2",
        "playwright==1.40.0",
        "undetected-chromedriver==3.5.4",
        "fake-useragent==1.4.0",
        "requests-html==0.10.0",
        "scrapy==2.11.0"
    ]
    
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    except subprocess.CalledProcessError:
        pass
    
    return success_count, len(packages)

if __name__ == "__main__":
    success_count, total_packages = main() 