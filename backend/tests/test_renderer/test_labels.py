import pytest
from app.renderer.labels import (
    collision_avoidance, LabelBox, render_label, compute_banner_height,
    _label_candidates,
)


def test_collision_avoidance_overlapping():
    """Overlapping labels should be pushed apart."""
    boxes = [
        LabelBox(x=100, y=100, width=80, height=40, stop_index=0),
        LabelBox(x=110, y=120, width=80, height=40, stop_index=1),
    ]
    collision_avoidance(boxes)
    # Second box should be pushed down so they don't overlap
    assert boxes[1].y >= boxes[0].y + boxes[0].height


def test_collision_avoidance_non_overlapping():
    """Non-overlapping labels should not move."""
    boxes = [
        LabelBox(x=100, y=100, width=80, height=40, stop_index=0),
        LabelBox(x=100, y=200, width=80, height=40, stop_index=1),
    ]
    original_y = [b.y for b in boxes]
    collision_avoidance(boxes)
    assert [b.y for b in boxes] == original_y


def test_collision_avoidance_same_position():
    """Labels at the same position should all be separated."""
    boxes = [
        LabelBox(x=100, y=100, width=80, height=40, stop_index=i)
        for i in range(3)
    ]
    collision_avoidance(boxes)
    # All boxes should have different y positions
    ys = [b.y for b in boxes]
    assert len(set(ys)) == 3


def test_render_label_produces_image():
    label = render_label("Madrid", "Mar 22-24")
    assert label.mode == "RGBA"
    assert label.width > 0
    assert label.height > 0


# --- min_y floor ---

def test_collision_avoidance_respects_min_y():
    """A label with min_y should not be pushed above that floor."""
    boxes = [
        LabelBox(x=100, y=200, width=80, height=40, stop_index=0, min_y=200),
        LabelBox(x=100, y=210, width=80, height=40, stop_index=1, min_y=210),
    ]
    collision_avoidance(boxes)
    assert boxes[0].y >= 200
    assert boxes[1].y >= 210


def test_collision_avoidance_min_y_pushes_other_down():
    """When a has min_y and can't move up, the full overlap is pushed onto b."""
    a = LabelBox(x=0, y=100, width=100, height=40, stop_index=0, min_y=100)
    b = LabelBox(x=0, y=120, width=100, height=40, stop_index=1, min_y=0)
    collision_avoidance([a, b], pad=0)
    # a must not go above 100
    assert a.y >= 100
    # b must be pushed down so there's no overlap
    assert b.y >= a.y + a.height


# --- compute_banner_height ---

def test_compute_banner_height_positive():
    h = compute_banner_height("Spain & Portugal 2026", "March 22 – April 10")
    assert h > 0


def test_compute_banner_height_no_subtitle():
    h_with = compute_banner_height("Title", "Subtitle")
    h_without = compute_banner_height("Title", "")
    assert h_with > h_without


def test_compute_banner_height_scales_with_font():
    h_small = compute_banner_height("Title", "Sub", title_font_size=24, subtitle_font_size=14)
    h_large = compute_banner_height("Title", "Sub", title_font_size=96, subtitle_font_size=48)
    assert h_large > h_small


# --- _label_candidates ---

def test_candidates_with_photo_prefer_sides_over_below():
    """For a photo stop, E/W of bubble should appear before S of marker."""
    cands = _label_candidates(cx=400, cy=400, lw=80, lh=40,
                              gap=16, has_photo=True, photo_diameter=80)
    xs = [lx for lx, _ in cands]
    # First two candidates should be to the right or left (not centred on cx)
    assert xs[0] != 400 - 80 // 2  # not centred → beside the bubble


def test_candidates_without_photo_prefer_below():
    """For a dot stop, first candidate should be directly below the marker."""
    cands = _label_candidates(cx=400, cy=400, lw=80, lh=40,
                              gap=16, has_photo=False, photo_diameter=80)
    lx, ly = cands[0]
    # Should be centred horizontally and below cy
    assert lx == 400 - 40   # cx - lw//2
    assert ly > 400          # below marker


def test_candidates_returns_at_least_four():
    for has_photo in (True, False):
        cands = _label_candidates(400, 400, 80, 40, 16, has_photo, 80)
        assert len(cands) >= 4
