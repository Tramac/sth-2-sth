# -*- coding: utf-8 -*-
"""
#####################################################################
    > File Name: video_cutframe.py
    > Author: Tramac
    > Created Time：2022/06/10 19:47:37
#####################################################################
"""
import os
import sys
import tempfile
import subprocess
import re


class VideoCutFrame(object):
    """视频抽帧"""
    def __init__(self, params=None):
        super(VideoCutFrame, self).__init__()
        if params is None:
            params = {}

        self.ffmpeg = os.path.abspath(str(params.get('tools', 'ffmpeg')))
        self.ffprobe = os.path.abspath(str(params.get('tools', 'ffprobe')))

        self.tmp_dir = str(params.get('result', 'tmp_dir'))

        self.imgs = None
        self.fps = params.pop('fps') if 'fps' in params else 1
        self.threads = params.pop('threads') if 'threads' in params else 8

    def __call__(self, mp4, video_dir=None, params=None):
        if video_dir is None or video_dir == '':
            video_dir = self.tmp_dir
        img_dir = tempfile.mkdtemp(prefix="img", dir=video_dir)
        if params is not None and 'fps' in params:
            real_fps = params['fps']
        elif self.fps == 'full':
            real_fps = self._get_video_fps(mp4)
            if real_fps is None:
                real_fps = 1
        else:
            real_fps = self.fps

        cmd = "{} -threads {} -i '{}' -threads {} -vf fps={} -loglevel quiet ".format(
            self.ffmpeg, self.threads, mp4, self.threads, real_fps)

        cmd += "-q:v 2 {}/%5d.jpg".format(img_dir)

        subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True).communicate()
        imgs = os.listdir(img_dir)

        if len(imgs) == 0:
            cmd = "{} -threads {} -i '{}' -threads {} -r {} -loglevel quiet ".format(
                self.ffmpeg, self.threads, mp4, self.threads, real_fps)
            cmd += " -q:v 2 {}/%5d.jpg".format(img_dir)
            subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True).communicate()
            imgs = os.listdir(img_dir)
            if len(imgs) == 0:
                raise ValueError('CutFrame Error!')

        return img_dir, real_fps

    def _get_video_fps(self, mp4):
        cmd = r" 2>&1 | grep 'Stream' |  grep 'Video'"
        cmd = self.ffprobe + ' ' + mp4 + cmd
        (status, output) = subprocess.getstatusoutput(cmd)
        fps = None
        if status == 0 and output != '':
            fps = output
        if fps is not None:
            fps = re.search(r'\d+ fps', fps)
            if fps is not None:
                fps_v = fps.group(0).split()
                if len(fps_v) == 2:
                    fps = int(fps_v[0])
                else:
                    fps = None
        return fps

