# Object Detection and Tracking

This project converts the earlier YOLO single-image inference into a real-time object detection and tracking pipeline using OpenCV, a pretrained YOLOv4 model, and a lightweight SORT tracker.

## Architecture

- [object_tracking.py](object_tracking.py) – main real-time entry point
- [src/detection/yolo_detector.py](src/detection/yolo_detector.py) – YOLO model wrapper and post-processing
- [src/tracking/sort_tracker.py](src/tracking/sort_tracker.py) – tracking logic with IDs across frames
- [tests/test_sort_tracker.py](tests/test_sort_tracker.py) – tracker regression test
- [yolov4.cfg](yolov4.cfg), [yolov4.weights](yolov4.weights), [coco.names](coco.names) – model config, weights, and label names

## Features
- Real-time webcam or video file input
- YOLOv4 object detection using OpenCV DNN
- Bounding boxes and labels per detected object
- SORT ID tracking across frames
- Live output window with tracking IDs

## Requirements
- Python 3.10+
- OpenCV
- NumPy
- Pytest

## Setup
```bash
pip install -r requirements.txt
```

## Run webcam
```bash
python object_tracking.py --camera
```

## Run a video file
```bash
python object_tracking.py --source sample.mp4
```

## Run without preview window
```bash
python object_tracking.py --source sample.mp4 --no-preview
```

## Notes
- `--camera` automatically uses webcam index 0.
- The default YOLO settings balance accuracy and speed for CPU-based real-time use.
- If a webcam is unavailable, use a video file path instead.

