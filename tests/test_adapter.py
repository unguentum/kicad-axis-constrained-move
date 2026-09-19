from kipy.board_types import BoardSegment, FootprintInstance, Track, Via
from kipy.geometry import Vector2
from kipy.proto.board import board_commands_pb2

from move_aligned_to import adapter as adapter_module
from move_aligned_to.adapter import KiCadAdapter
from move_aligned_to.model import Axis


def point(x, y):
    return Vector2.from_xy(x, y)


def test_connection_retries_transient_not_ready(monkeypatch):
    board = object()

    class FakeKiCad:
        attempts = 0

        def get_board(self):
            self.attempts += 1
            if self.attempts < 3:
                raise RuntimeError("KiCad is not ready to reply")
            return board

    monkeypatch.setattr(adapter_module, "KiCad", FakeKiCad)
    monkeypatch.setattr(adapter_module.time, "sleep", lambda _seconds: None)

    adapter = KiCadAdapter()

    assert adapter.board is board
    assert adapter.kicad.attempts == 3


def test_translates_footprint_by_position():
    item = FootprintInstance()
    item.position = point(10, 20)
    KiCadAdapter._translate_item(item, point(3, -4))
    assert (item.position.x, item.position.y) == (13, 16)


def test_translates_via_by_position():
    item = Via()
    item.position = point(10, 20)
    KiCadAdapter._translate_item(item, point(-5, 7))
    assert (item.position.x, item.position.y) == (5, 27)


def test_translates_track_endpoints():
    item = Track()
    item.start = point(1, 2)
    item.end = point(11, 12)
    KiCadAdapter._translate_item(item, point(4, 5))
    assert (item.start.x, item.start.y) == (5, 7)
    assert (item.end.x, item.end.y) == (15, 17)


def test_translates_board_shape_with_native_move():
    item = BoardSegment()
    item.start = point(1, 2)
    item.end = point(11, 12)
    KiCadAdapter._translate_item(item, point(4, 5))
    assert (item.start.x, item.start.y) == (5, 7)
    assert (item.end.x, item.end.y) == (15, 17)


def encoded_movement_axis(axis):
    sent = []

    class Client:
        def send(self, command, response_type):
            sent.append((command, response_type))

    class Board:
        client = Client()
        document = board_commands_pb2.InteractiveMoveItems().board

    adapter = KiCadAdapter.__new__(KiCadAdapter)
    adapter.board = Board()
    adapter._interactive_move_on_axis([], axis)

    return sent[0][0].SerializeToString()


def test_same_x_leaves_vertical_y_axis_movement():
    assert encoded_movement_axis(Axis.SAME_X).endswith(b"\x18\x02")


def test_same_y_leaves_horizontal_x_axis_movement():
    assert encoded_movement_axis(Axis.SAME_Y).endswith(b"\x18\x01")
