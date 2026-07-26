"""Seat layouts, one per screen format.

Real auditoriums are not interchangeable. An IMAX GT house seats several
hundred people across a wide, deep grid; a 4DX room is small because every seat
is a motion platform. So the seat map a visitor sees is generated from the
format's own layout rather than from one shared grid.

Rooms also narrow toward the screen: the front rows are closest to it and hold
fewer seats, which is what `taper` describes. Seat counts are modelled on real
Japanese multiplex screens.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Layout:
    """How one screen format is laid out."""

    # Number of rows, front (nearest the screen) to back.
    rows: int
    # Seats in the widest row, at the back.
    back_row_seats: int
    # How many seats fewer than the back row each row has, front row first.
    # Rows past the end of this tuple are full width.
    taper: tuple
    # An aisle falls after this many seats in from each end of a row. Counting
    # from the ends rather than using fixed seat numbers keeps the aisles lined
    # up once rows differ in length.
    aisle_from_ends: int
    # Row letters sold at the premium rate (the centre block).
    premium_rows: tuple
    # The row holding the accessible spaces, and how many sit at each end.
    wheelchair_row: str
    wheelchair_spaces_per_side: int = 2

    def row_labels(self):
        return [chr(ord("A") + index) for index in range(self.rows)]

    def seats_in_row(self, index):
        """How many seats the row at this index (0 = front) holds."""
        missing = self.taper[index] if index < len(self.taper) else 0
        return self.back_row_seats - missing

    def rows_with_seats(self):
        """(row label, seat count) for every row, front to back."""
        return [
            (label, self.seats_in_row(index))
            for index, label in enumerate(self.row_labels())
        ]

    @property
    def seat_count(self):
        return sum(count for _, count in self.rows_with_seats())

    def kind_for(self, row, number, seats_in_row):
        """Which kind of seat sits at this position."""
        # Checked first: an accessible space is never sold as premium, even
        # when it sits inside the premium block.
        if row == self.wheelchair_row:
            at_start = number <= self.wheelchair_spaces_per_side
            at_end = number > seats_in_row - self.wheelchair_spaces_per_side
            if at_start or at_end:
                return "wheelchair"
        if row in self.premium_rows:
            return "premium"
        return "standard"

    def is_aisle(self, number, seats_in_row):
        """Whether an aisle gap falls immediately after this seat."""
        return number in (self.aisle_from_ends, seats_in_row - self.aisle_from_ends)


LAYOUTS = {
    # 18 rows tapering from 18 seats at the front to 26 at the back: 432 seats,
    # the size of a real IMAX GT house.
    "imax_gt": Layout(
        rows=18,
        back_row_seats=26,
        taper=(8, 7, 6, 5, 4, 3, 2, 1),
        aisle_from_ends=4,
        premium_rows=("H", "I", "J", "K", "L", "M"),
        # Mid-house landing, as in a real IMAX GT auditorium.
        wheelchair_row="K",
    ),
    # 13 rows, 18 at the front to 22 at the back: 276 seats.
    "dolby": Layout(
        rows=13,
        back_row_seats=22,
        taper=(4, 3, 2, 1),
        aisle_from_ends=3,
        premium_rows=("F", "G", "H", "I"),
        wheelchair_row="H",
    ),
    # 8 rows, 12 at the front to 14 at the back: 109 seats. Small because every
    # seat is a motion platform; the accessible spaces are at the rear, off the
    # moving floor.
    "4dx": Layout(
        rows=8,
        back_row_seats=14,
        taper=(2, 1),
        aisle_from_ends=3,
        premium_rows=("D", "E"),
        wheelchair_row="H",
    ),
    # 10 rows, 15 at the front to 18 at the back: 174 seats.
    "standard": Layout(
        rows=10,
        back_row_seats=18,
        taper=(3, 2, 1),
        aisle_from_ends=3,
        premium_rows=("E", "F", "G"),
        wheelchair_row="J",
    ),
}
