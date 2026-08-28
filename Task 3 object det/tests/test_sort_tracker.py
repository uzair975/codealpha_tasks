import numpy as np

from src.tracking.sort_tracker import SortTracker


def test_tracker_assigns_ids_and_updates_existing_tracks():
    tracker = SortTracker(max_age=5, min_hits=1, iou_threshold=0.3)

    dets = np.array([[10, 10, 30, 30], [100, 100, 30, 30]], dtype=np.float32)
    tracked = tracker.update(dets)

    assert tracked.shape[0] == 2
    ids = tracked[:, 4].astype(int)
    assert np.unique(ids).size == 2

    moved = np.array([[12, 12, 30, 30], [102, 102, 30, 30]], dtype=np.float32)
    tracked2 = tracker.update(moved)
    assert tracked2.shape[0] == 2
    assert np.unique(tracked2[:, 4].astype(int)).size == 2
