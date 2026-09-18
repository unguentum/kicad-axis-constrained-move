from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Axis(str, Enum):
    SAME_X = "same_x"
    SAME_Y = "same_y"

    @property
    def label(self) -> str:
        return "Same X" if self is Axis.SAME_X else "Same Y"

    @property
    def movement_description(self) -> str:
        return "vertical" if self is Axis.SAME_X else "horizontal"

    @property
    def movement_axis_wire_value(self) -> int:
        """KiCad AxisAlignment value for the direction left free after alignment."""
        return 2 if self is Axis.SAME_X else 1


@dataclass(frozen=True)
class Bounds:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def center_x(self) -> int:
        return self.left + (self.right - self.left) // 2

    @property
    def center_y(self) -> int:
        return self.top + (self.bottom - self.top) // 2

    def union(self, other: Bounds) -> Bounds:
        return Bounds(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )


class HasId(Protocol):
    @property
    def id(self): ...


def aggregate_bounds(bounds: Iterable[Bounds]) -> Bounds:
    iterator = iter(bounds)
    try:
        result = next(iterator)
    except StopIteration as exc:
        raise ValueError("At least one bounding box is required") from exc

    for box in iterator:
        result = result.union(box)
    return result


def alignment_delta(moving: Bounds, reference: Bounds, axis: Axis) -> tuple[int, int]:
    if axis is Axis.SAME_X:
        return reference.center_x - moving.center_x, 0
    return 0, reference.center_y - moving.center_y


def stable_id(item: HasId) -> str:
    value = getattr(item.id, "value", item.id)
    return str(value)
