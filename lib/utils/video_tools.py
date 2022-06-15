# -*- coding: utf-8 -*-
"""
#####################################################################
    > File Name: video_tools.py
    > Author: Tramac
    > Created Time: 2022/06/15 15:54:20
#####################################################################
"""
import os
import tempfile
import requests


def video_download(url, save_dir):
    """video download from url"""
    url = url.replace('https://', 'http://') if url.startswith('https://') else url
    print(url)
    mp4_file = tempfile.NamedTemporaryFile(prefix="video_", suffix=".mp4", dir=save_dir, delete=False)
    response = requests.get(url, timeout=1200)
    if response.status_code != requests.codes.ok:
        return "failed"
    mp4_file.write(response.content)
    mp4_file.close()
    
    return mp4_file.name
    
