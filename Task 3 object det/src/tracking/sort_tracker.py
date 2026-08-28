from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class Track:
    track_id: int
    bbox: np.ndarray
    hits: int = 1
    age: int = 1
    time_since_update: int = 0


class SortTracker:
    """Minimal SORT implementation for object tracking in video frames."""

    def __init__(self, max_age: int = 30, min_hits: int = 3, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.next_id = 1

    @staticmethod
    def _xywh_to_xyxy(bbox: np.ndarray) -> np.ndarray:
        x, y, w, h = bbox.astype(float)
        return np.array([x, y, x + w, y + h], dtype=np.float32)

    @staticmethod
    def _iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
        inter_x1 = max(box_a[0], box_b[0])
        inter_y1 = max(box_a[1], box_b[1])
        inter_x2 = min(box_a[2], box_b[2])
        inter_y2 = min(box_a[3], box_b[3])

        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
        area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
        union = area_a + area_b - inter_area
        if union <= 0:
            return 0.0
        return inter_area / union

    def _associate_detections_to_tracks(self, detections: np.ndarray, track_boxes: np.ndarray):
        if len(track_boxes) == 0 and len(detections) == 0:
            return (
                np.empty((0,), dtype=int),
                np.empty((0,), dtype=int),
                np.empty((0,), dtype=int),
                np.empty((0,), dtype=int),
            )

        if len(track_boxes) == 0:
            return (
                np.empty((0,), dtype=int),
                np.empty((0,), dtype=int),
                np.empty((0,), dtype=int),
                np.arange(len(detections), dtype=int),
            )

        if len(detections) == 0:
            return (
                np.empty((0,), dtype=int),
                np.empty((0,), dtype=int),
                np.arange(len(track_boxes), dtype=int),
                np.empty((0,), dtype=int),
            )

        iou_matrix = np.zeros((len(track_boxes), len(detections)), dtype=np.float32)
        for i, track_box in enumerate(track_boxes):
            for j, det_box in enumerate(detections):
                iou_matrix[i, j] = self._iou(track_box, det_box)

        matched_indices = []
        used_detection = set()
        used_track = set()

        # Prefer strongest matches first
        for i in np.argsort(iou_matrix.max(axis=1))[::-1]:
            if i in used_track:
                continue
            j_candidates = np.where(iou_matrix[i] > self.iou_threshold)[0]
            if j_candidates.size == 0:
                continue
            best_j = int(j_candidates[np.argmax(iou_matrix[i, j_candidates])])
            if best_j in used_detection:
                continue
            matched_indices.append((i, best_j))
            used_track.add(i)
            used_detection.add(best_j)

        unmatched_tracks = [idx for idx in range(len(track_boxes)) if idx not in {i for i, _ in matched_indices}]
        unmatched_detections = [idx for idx in range(len(detections)) if idx not in {j for _, j in matched_indices}]
        return np.array([i for i, _ in matched_indices], dtype=int), np.array([j for _, j in matched_indices], dtype=int), np.array(unmatched_tracks, dtype=int), np.array(unmatched_detections, dtype=int)

    def update(self, detections: np.ndarray):
        """Update tracks from current detections.

        Detections are expected as a (N, 4) array in xywh format.
        Returns a (M, 5) array with x, y, w, h, track_id.
        """
        if detections.size == 0:
            detections = np.empty((0, 4), dtype=np.float32)
        else:
            detections = np.asarray(detections, dtype=np.float32).reshape(-1, 4)

        if not self.tracks:
            for det in detections:
                self.tracks.append(Track(track_id=self.next_id, bbox=det.copy(), hits=1, age=1, time_since_update=0))
                self.next_id += 1
            return self._tracks_to_array()

        track_boxes = np.array([track.bbox.copy() for track in self.tracks], dtype=np.float32)
        matched_tracks, matched_dets, unmatched_tracks, unmatched_dets = self._associate_detections_to_tracks(
            np.array([self._xywh_to_xyxy(det) for det in detections], dtype=np.float32),
            np.array([self._xywh_to_xyxy(track.bbox) for track in self.tracks], dtype=np.float32),
        )

        for track_idx, det_idx in zip(matched_tracks, matched_dets):
            track = self.tracks[track_idx]
            det = detections[det_idx]
            track.bbox = det.copy()
            track.hits += 1
            track.age += 1
            track.time_since_update = 0

        for track_idx in unmatched_tracks:
            track = self.tracks[track_idx]
            track.age += 1
            track.time_since_update += 1

        for det_idx in unmatched_dets:
            det = detections[det_idx]
            self.tracks.append(Track(track_id=self.next_id, bbox=det.copy(), hits=1, age=1, time_since_update=0))
            self.next_id += 1

        survivors = []
        for track in self.tracks:
            if track.time_since_update <= self.max_age and (track.hits >= self.min_hits or track.time_since_update == 0):
                survivors.append(track)
        self.tracks = survivors

        return self._tracks_to_array()

    def _tracks_to_array(self):
        results = []
        for track in self.tracks:
            if track.time_since_update <= self.max_age:
                x, y, w, h = track.bbox
                results.append([x, y, w, h, track.track_id])
        return np.array(results, dtype=np.float32).reshape(-1, 5) if results else np.empty((0, 5), dtype=np.float32)
