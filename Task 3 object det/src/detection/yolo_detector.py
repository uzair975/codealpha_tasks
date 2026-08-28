from __future__ import annotations

import os
from typing import List

import cv2
import numpy as np


class YoloDetector:
    def __init__(
        self,
        weights_path: str,
        config_path: str,
        labels_path: str,
        input_size: int = 416,
        conf_thresh: float = 0.25,
        nms_thresh: float = 0.45,
    ) -> None:
        self.weights_path = weights_path
        self.config_path = config_path
        self.labels_path = labels_path
        self.input_size = input_size
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh

        try:
            self.net = cv2.dnn.readNet(self.weights_path, self.config_path)
        except cv2.error:
            try:
                self.net = cv2.dnn.readNetFromDarknet(self.config_path, self.weights_path)
            except cv2.error as exc:
                raise RuntimeError(
                    "YOLOv4 could not be loaded. This usually means the installed OpenCV build does not support Darknet import. "
                    "Install OpenCV 4.x (for example: pip install 'opencv-python<5') and ensure yolov4.cfg and yolov4.weights exist."
                ) from exc

        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.output_layers = self._get_output_layers()
        self.class_names = self._load_labels()

    def _load_labels(self) -> List[str]:
        with open(self.labels_path, "r", encoding="utf-8") as handle:
            return [line.strip() for line in handle if line.strip()]

    def _get_output_layers(self):
        layer_names = self.net.getLayerNames()
        out_layers = self.net.getUnconnectedOutLayers()
        if hasattr(out_layers, "flatten"):
            out_layers = out_layers.flatten()
        return [layer_names[idx - 1] for idx in out_layers]

    def _letterbox(self, frame: np.ndarray):
        height, width = frame.shape[:2]
        scale = min(self.input_size / width, self.input_size / height)
        resized_width = max(1, int(round(width * scale)))
        resized_height = max(1, int(round(height * scale)))
        resized = cv2.resize(frame, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)

        canvas = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        pad_x = (self.input_size - resized_width) // 2
        pad_y = (self.input_size - resized_height) // 2
        canvas[pad_y: pad_y + resized_height, pad_x: pad_x + resized_width] = resized

        return canvas, scale, pad_x, pad_y

    def detect(self, frame: np.ndarray):
        if frame is None or frame.size == 0:
            return []

        letterboxed, scale, pad_x, pad_y = self._letterbox(frame)
        blob = cv2.dnn.blobFromImage(
            letterboxed,
            1 / 255.0,
            (self.input_size, self.input_size),
            swapRB=True,
            crop=False,
        )

        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        height, width = frame.shape[:2]
        boxes, confidences, class_ids = [], [], []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = int(np.argmax(scores))
                confidence = float(scores[class_id])
                if confidence < self.conf_thresh:
                    continue

                center_x = float(detection[0]) * self.input_size
                center_y = float(detection[1]) * self.input_size
                detection_w = float(detection[2]) * self.input_size
                detection_h = float(detection[3]) * self.input_size

                x = (center_x - detection_w / 2 - pad_x) / scale
                y = (center_y - detection_h / 2 - pad_y) / scale
                w = detection_w / scale
                h = detection_h / scale

                box = [x, y, w, h]
                boxes.append(box)
                confidences.append(confidence)
                class_ids.append(class_id)

        if not boxes:
            return []

        idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_thresh, self.nms_thresh)
        if isinstance(idxs, tuple):
            idxs = idxs[0]
        if len(idxs) == 0:
            return []

        detections = []
        for idx in idxs.flatten():
            x, y, w, h = boxes[int(idx)]
            x = max(0, min(width - 1, x))
            y = max(0, min(height - 1, y))
            w = max(1, min(width - x, w))
            h = max(1, min(height - y, h))

            label = self.class_names[class_ids[int(idx)]].title()
            detections.append(
                {
                    "bbox": [int(round(x)), int(round(y)), int(round(w)), int(round(h))],
                    "class_name": label,
                    "confidence": float(confidences[int(idx)]),
                    "class_id": int(class_ids[int(idx)]),
                }
            )

        return detections
