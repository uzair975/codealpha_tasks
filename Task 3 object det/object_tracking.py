from __future__ import annotations

import argparse
import os
from typing import List

import cv2
import numpy as np

from src.detection.yolo_detector import YoloDetector
from src.tracking.sort_tracker import SortTracker


WINDOW_NAME = "Object Detection and Tracking"


def draw_box(frame: np.ndarray, bbox: np.ndarray, label: str, track_id: int | None = None, color=(0, 255, 0)) -> None:
    x, y, w, h = bbox
    x1, y1 = int(x), int(y)
    x2, y2 = int(x + w), int(y + h)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    text = f"{label}"
    if track_id is not None:
        text += f" ID:{track_id}"

    (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.rectangle(frame, (x1, y1 - 20), (x1 + text_w + 6, y1), color, -1)
    cv2.putText(frame, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)


def detect_and_track(source: str, use_camera: bool = False, show_preview: bool = True, detection_interval: int = 2) -> None:
    model_dir = os.path.join(os.path.dirname(__file__))
    detector = YoloDetector(
        weights_path=os.path.join(model_dir, "yolov4.weights"),
        config_path=os.path.join(model_dir, "yolov4.cfg"),
        labels_path=os.path.join(model_dir, "coco.names"),
        input_size=320,
        conf_thresh=0.25,
        nms_thresh=0.45,
    )
    tracker = SortTracker(max_age=15, min_hits=2, iou_threshold=0.25)

    cap = cv2.VideoCapture(0 if use_camera else source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")

    if use_camera:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

    frame_index = 0
    last_drawn_objects = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_AREA)

        if frame_index % detection_interval == 0:
            detections = detector.detect(frame)
            if detections:
                detection_boxes = np.array([det["bbox"] for det in detections], dtype=np.float32)
                tracked = tracker.update(detection_boxes)
                track_map = {int(row[4]): np.array([row[0], row[1], row[2], row[3]], dtype=np.float32) for row in tracked}

                last_drawn_objects = []
                for det in detections:
                    bbox = np.array(det["bbox"], dtype=np.float32)
                    best_track_id = None
                    best_iou = 0.0
                    for track_id, track_box in track_map.items():
                        iou = SortTracker._iou(SortTracker._xywh_to_xyxy(bbox), SortTracker._xywh_to_xyxy(track_box))
                        if iou > best_iou:
                            best_iou = iou
                            best_track_id = track_id

                    if best_track_id is not None:
                        draw_box(frame, bbox, det["class_name"], best_track_id)
                        last_drawn_objects.append({"bbox": bbox, "class_name": det["class_name"], "track_id": best_track_id})
                    else:
                        draw_box(frame, bbox, det["class_name"])
                        last_drawn_objects.append({"bbox": bbox, "class_name": det["class_name"], "track_id": None})
            else:
                tracker.update(np.empty((0, 4), dtype=np.float32))
                last_drawn_objects = []
        else:
            for obj in last_drawn_objects:
                bbox = np.array(obj["bbox"], dtype=np.float32)
                draw_box(frame, bbox, obj["class_name"], obj["track_id"])

        if show_preview:
            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        frame_index += 1

    cap.release()
    if show_preview:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time object detection and tracking")
    parser.add_argument("--source", type=str, default="0", help="Path to video file or use 0 for webcam")
    parser.add_argument("--camera", action="store_true", help="Use webcam input")
    parser.add_argument("--no-preview", action="store_true", help="Disable on-screen display for headless runs")
    parser.add_argument("--detection-interval", type=int, default=2, help="Run YOLO every N frames to keep the stream responsive")
    args = parser.parse_args()

    use_camera = args.camera or args.source == "0"
    source = 0 if use_camera else args.source
    detect_and_track(
        source,
        use_camera=use_camera,
        show_preview=not args.no_preview,
        detection_interval=max(1, args.detection_interval),
    )
