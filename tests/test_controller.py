from dataclasses import dataclass

import pytest

from move_aligned_to.controller import MoveAlignedController, WorkflowError
from move_aligned_to.model import Axis, Bounds


@dataclass
class FakeId:
    value: str


@dataclass
class FakeItem:
    id: FakeId


class FakeAdapter:
    def __init__(self, moving, reference, boxes):
        self.current = list(moving)
        self.reference = list(reference)
        self.boxes = boxes
        self.moves = []

    def selection(self):
        return list(self.current)

    def clear_selection(self):
        self.current = list(self.reference)

    def bounds_for(self, items):
        return [self.boxes[item.id.value] for item in items]

    def align_and_move(self, items, dx, dy, axis):
        self.moves.append(([item.id.value for item in items], dx, dy, axis))


def test_full_same_x_workflow():
    moving = [FakeItem(FakeId("a")), FakeItem(FakeId("b"))]
    refs = [FakeItem(FakeId("r"))]
    adapter = FakeAdapter(
        moving,
        refs,
        {
            "a": Bounds(0, 0, 10, 10),
            "b": Bounds(20, 0, 30, 10),
            "r": Bounds(95, 40, 105, 50),
        },
    )
    controller = MoveAlignedController(adapter)
    count, dx, dy = controller.align(Axis.SAME_X)
    assert (count, dx, dy) == (1, 85, 0)
    assert adapter.moves == [(["a", "b"], 85, 0, Axis.SAME_X)]


def test_no_initial_selection_is_rejected():
    adapter = FakeAdapter([], [], {})
    with pytest.raises(WorkflowError, match="Select at least one"):
        MoveAlignedController(adapter)


def test_multiple_moving_and_reference_items_same_y():
    moving = [FakeItem(FakeId("a")), FakeItem(FakeId("b"))]
    refs = [FakeItem(FakeId("r1")), FakeItem(FakeId("r2"))]
    adapter = FakeAdapter(
        moving,
        refs,
        {
            "a": Bounds(0, 0, 10, 10),
            "b": Bounds(20, 20, 30, 30),
            "r1": Bounds(100, 80, 110, 90),
            "r2": Bounds(120, 100, 130, 110),
        },
    )

    controller = MoveAlignedController(adapter)
    count, dx, dy = controller.align(Axis.SAME_Y)

    assert (count, dx, dy) == (2, 0, 80)
    assert adapter.moves == [(["a", "b"], 0, 80, Axis.SAME_Y)]


def test_empty_reference_selection_is_rejected():
    item = FakeItem(FakeId("a"))
    adapter = FakeAdapter([item], [], {"a": Bounds(0, 0, 10, 10)})
    controller = MoveAlignedController(adapter)
    with pytest.raises(WorkflowError, match="reference"):
        controller.align(Axis.SAME_Y)


def test_overlapping_selections_are_rejected():
    item = FakeItem(FakeId("same"))
    adapter = FakeAdapter([item], [item], {"same": Bounds(0, 0, 10, 10)})
    controller = MoveAlignedController(adapter)
    with pytest.raises(WorkflowError, match="separate"):
        controller.align(Axis.SAME_X)
