from __future__ import annotations

import argparse

from object_tracking import detect_and_track


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Object detection and tracking")
    parser.add_argument("--source", type=str, default="0", help="Path to a video file or use 0 for webcam")
    parser.add_argument("--camera", action="store_true", help="Use webcam input")
    parser.add_argument("--no-preview", action="store_true", help="Disable preview window")
    args = parser.parse_args()

    use_camera = args.camera or args.source == "0"
    source = 0 if use_camera else args.source
    detect_and_track(source, use_camera=use_camera, show_preview=not args.no_preview)
