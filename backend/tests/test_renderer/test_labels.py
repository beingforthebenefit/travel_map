import pytest
from app.renderer.labels import collision_avoidance, LabelBox, render_label


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
