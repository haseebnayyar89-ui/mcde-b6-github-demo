"""Task 13 | Booking Conflict Scheduler"""
from datetime import datetime


class Scheduler:
    def __init__(self):
        self.bookings = []          # list of dicts: id, room, start, end

    def add_booking(self, booking_id, room, start, end):
        """Return (True, []) if accepted, or (False, conflicting_bookings) if rejected.
        Raises ValueError for invalid input."""
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise ValueError("start and end must be datetime objects")
        if end <= start:
            raise ValueError("end must be after start")
        for b in self.bookings:
            if b["id"] == booking_id:
                raise ValueError("duplicate booking id: " + str(booking_id))

        conflicts = []
        for b in self.bookings:
            # overlap only if same room, and each starts before the other ends
            # (adjacent bookings like 9-10 and 10-11 are allowed)
            if b["room"] == room and start < b["end"] and b["start"] < end:
                conflicts.append(b)
        if conflicts:
            return False, conflicts

        self.bookings.append({"id": booking_id, "room": room, "start": start, "end": end})
        return True, []


if __name__ == "__main__":
    s = Scheduler()
    day = lambda hour, minute=0: datetime(2026, 11, 7, hour, minute)

    print(s.add_booking("B1", "Room A", day(9), day(10)))              # accepted
    print(s.add_booking("B2", "Room A", day(10), day(11)))             # accepted (adjacent)
    accepted, conflicts = s.add_booking("B3", "Room A", day(9, 30), day(10, 30))
    print(accepted, [c["id"] for c in conflicts])                      # rejected, B1 and B2
    print(s.add_booking("B4", "Room B", day(9, 30), day(10, 30)))      # other room -> accepted
    for args in [("B5", "Room A", day(14), day(13)), ("B1", "Room C", day(14), day(15))]:
        try:
            s.add_booking(*args)
        except ValueError as error:
            print("Error:", error)
