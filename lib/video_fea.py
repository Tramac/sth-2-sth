# -*- coding: utf-8 -*-
"""
#####################################################################
    > File Name: video_fea.py
    > Author: Tramac
    > Created Time：2022/06/11 16:18:13
#####################################################################
"""
import os
import cv2
import numpy as np
import torch

from PIL import Image
from collections import OrderedDict
from torchvision import transforms

from .utils.transforms import *
from .models.model import resnet50


class VideoFeaExtractor(object):
    """视频特征提取器"""
    def __init__(self, conf=None):
        super(VideoFeaExtractor, self).__init__()
        if conf is None:
            conf = {}

        model_cfg_dict = dict(
            num_classes=64,
            mlp=True,
            intra_out=False,
            order_out=False,
            diff_out=False,
            tsn_out=True
        )

        self.model = resnet50(**model_cfg_dict)

        weight = str(conf.get('model', 'checkpoint'))
        checkpoint = torch.load(weight, map_location=lambda storage, loc: storage)
        new_state_dict = OrderedDict()
        for k, v in checkpoint['state_dict'].items():
            name = k[7:]
            new_state_dict[name] = v
        self.model.load_state_dict(new_state_dict)
        
        self.transform = transforms.Compose([
            GroupScale(256),
            GroupCenterCrop(224),
            Stack(roll=False),
            ToTorchFormatTensor(div=True),
            GroupNormalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        self.model.eval()

    def __call__(self, img_dir):
        # 均匀抽帧
        frames_name = sorted(os.listdir(img_dir))
        frames = [os.path.join(img_dir, name) for name in frames_name]

        # 均匀抽取10帧图像
        frames_num = len(frames)
        indices = self._get_indices(frames_num, 0, num_segments=min(frames_num, 10))
        images_path = [frames[int(idx)] for idx in indices]

        images = []
        for img_path in images_path:
            img = Image.open(img_path).convert('RGB')
            images.append(img)

        with torch.no_grad():
            images = self.transform(images).unsqueeze_(0)
            fea = self.model(images, tsn_mode=True)
            fea = fea.data.numpy()[0]
            #fea = fea.cpu().data.numpy()[0]

        return fea

    def _get_indices(self, num_frames, s, new_length=1, num_segments=10):
        """均匀分段"""
        tick = (num_frames - new_length + 1) / float(num_segments)
        offsets = np.array([int(tick / 2.0 + tick * x) for x in range(num_segments)])

        return offsets + s

