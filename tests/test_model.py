import pytest

from move_aligned_to.model import Axis, Bounds, aggregate_bounds, alignment_delta


def test_aggregate_bounds_uses_combined_visual_extent():
    result = aggregate_bounds(
        [Bounds(0, 10, 20, 30), Bounds(-10, -20, 5, 15), Bounds(4, 8, 40, 50)]
    )
    assert result == Bounds(-10, -20, 40, 50)


def test_same_x_moves_only_x():
    moving = Bounds(0, 0, 20, 10)
    reference = Bounds(90, 100, 130, 140)
    assert alignment_delta(moving, reference, Axis.SAME_X) == (100, 0)


def test_same_y_moves_only_y():
    moving = Bounds(0, 0, 20, 10)
    reference = Bounds(90, 100, 130, 140)
    assert alignment_delta(moving, reference, Axis.SAME_Y) == (0, 115)


def test_half_nanometre_centres_are_deterministic():
    moving = Bounds(0, 0, 1, 1)
    reference = Bounds(2, 2, 5, 5)
    assert alignment_delta(moving, reference, Axis.SAME_X) == (3, 0)


def test_empty_bounds_are_rejected():
    with pytest.raises(ValueError):
        aggregate_bounds([])
