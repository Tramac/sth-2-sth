# -*- coding: utf-8 -*-
"""
Author: Tramac
Created Time：2022/06/10 19:47:37
"""
import os
import cv2
import shutil
import time
import numpy as np

from PIL import Image
from annoy import AnnoyIndex
from configparser import ConfigParser
from flask import Flask, make_response, render_template, request, redirect

from lib.video_fea import VideoFeaExtractor
from lib.utils.video_cutframe import VideoCutFrame

app = Flask(__name__)

# server config
conf = ConfigParser()
conf.read("./conf/app.conf")


@app.route('/')
def cekawal():
    # 初始化索引
    global index
    global invert
    index_file = str(conf.get('ann', 'index'))
    invert_file = str(conf.get('ann', 'invert'))

    # 倒排表
    invert = {}
    with open(invert_file, 'r') as lines:
        for line in lines:
            line = line.strip().split('\t')
            idx, url = line
            invert[idx] = url

    # 加载索引
    dim = int(conf.get('ann', 'dim'))
    metric = str(conf.get('ann', 'metric'))
    index = AnnoyIndex(dim, metric)
    index.load(index_file)

    tmp_dir = str(conf.get('result', 'tmp_dir'))
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
        return redirect('/home')
    else:
        return redirect('/home')

@app.route('/home')
def home():
    tmp_dir = str(conf.get('result', 'tmp_dir'))
    res = os.path.join(tmp_dir, 'recall.txt')
    if os.path.exists(res):
        pass
        recalls = []
        recall_urls = []
        with open(res, 'r') as lines:
            for line in lines:
                line = line.strip().split('\t')
                query, video_url, score = line
                recalls.append([video_url, float(score)])
        nearest = recalls[0][1]
        return render_template("index.html", querys=[query], recalls=recalls, page_status=1, count=len(invert), nearest=(nearest))
    else:
        return render_template("index.html", page_status=2, count=len(invert))

@app.route('/search', methods=['POST'])
def search():
    video_file = request.files['video']
    # 将视频保存到本地路径
    tmp_dir = str(conf.get('result', 'tmp_dir'))
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    video_path = os.path.join(tmp_dir, video_file.filename)
    video_file.save(video_path)

    # 视频抽帧
    cutframe_op = VideoCutFrame(conf)
    img_dir, real_fps = cutframe_op(video_path, video_dir=tmp_dir)

    # 提取特征
    model = VideoFeaExtractor(conf)
    fea = model(img_dir)

    # 近邻搜索
    topk = int(conf.get('ann', 'topk'))
    idxs, scores = index.get_nns_by_vector(fea, topk, include_distances=True)

    res = open(os.path.join(tmp_dir, 'recall.txt'), 'w')
    for i in range(len(idxs)):
        res.write('{}\t{}\t{}\n'.format(video_path, invert[str(idxs[i])], scores[i]))
    res.close()

    return redirect("/home")

@app.route('/<page_name>')
def other_page(page_name):
    return render_template("404.html"), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8991)
