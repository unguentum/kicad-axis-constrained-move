from kipy.board_types import BoardSegment, FootprintInstance, Track, Via
from kipy.geometry import Vector2
from kipy.proto.board import board_commands_pb2

from move_aligned_to.adapter import KiCadAdapter
from move_aligned_to.model import Axis


def point(x, y):
    return Vector2.from_xy(x, y)


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


def test_axis_constraint_is_encoded_for_patched_kicad_api():
    sent = []

    class Client:
        def send(self, command, response_type):
            sent.append((command, response_type))

    class Board:
        client = Client()
        document = board_commands_pb2.InteractiveMoveItems().board

    adapter = KiCadAdapter.__new__(KiCadAdapter)
    adapter.board = Board()
    adapter._interactive_move_on_axis([], Axis.SAME_Y)

    payload = sent[0][0].SerializeToString()
    assert payload.endswith(b"\x18\x02")
