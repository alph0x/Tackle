"""A small room registry."""
from dataclasses import dataclass


@dataclass
class Room:
    name: str
    capacity: int


def find_room(rooms, name):
    """The Room named `name` among `rooms`, or None."""
    for room in rooms:
        if room.name == name:
            return room
    return None
