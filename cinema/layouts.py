"""Seat layouts, one per screen format.

Real auditoriums are not interchangeable. An IMAX GT house seats several
hundred people across a wide, deep grid; a 4DX room is small because every seat
is a motion platform. So the seat map a visitor sees is generated from the
format's own layout rather than from one shared grid.

Seat counts are modelled on real Japanese multiplex screens (the IMAX GT layout
below comes to 468 seats, the size of a real IMAX GT house).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    """How one screen format is laid out."""

    rows: int
    seats_per_row: int
    # Seat numbers after which to draw an aisle gap.
    aisles: tuple
    # Row letters sold at the premium rate (the centre block).
    premium_rows: tuple
    # The row holding the accessible spaces, and which seats in it they are.
    # Wheelchair spaces sit at the ends of the row, next to the aisle.
    wheelchair_row: str
    wheelchair_seats: tuple

    @property
    def seat_count(self):
        return self.rows * self.seats_per_row

    def row_labels(self):
        return [chr(ord("A") + index) for index in range(self.rows)]

    def kind_for(self, row, number):
        """Which kind of seat sits at this position."""
        # Checked first: an accessible space is never sold as premium, even
        # when it sits inside the premium block.
        if row == self.wheelchair_row and number in self.wheelchair_seats:
            return "wheelchair"
        if row in self.premium_rows:
            return "premium"
        return "standard"


LAYOUTS = {
    # 18 x 26 = 468 seats.
    "imax_gt": Layout(
        rows=18,
        seats_per_row=26,
        aisles=(4, 22),
        premium_rows=("H", "I", "J", "K", "L", "M"),
        # Mid-house landing, as in a real IMAX GT auditorium.
        wheelchair_row="K",
        wheelchair_seats=(1, 2, 25, 26),
    ),
    # 13 x 22 = 286 seats.
    "dolby": Layout(
        rows=13,
        seats_per_row=22,
        aisles=(3, 20),
        premium_rows=("F", "G", "H", "I"),
        wheelchair_row="H",
        wheelchair_seats=(1, 2, 21, 22),
    ),
    # 8 x 14 = 112 seats. Small because every seat is a motion platform; the
    # accessible spaces are at the rear, off the moving floor.
    "4dx": Layout(
        rows=8,
        seats_per_row=14,
        aisles=(3, 12),
        premium_rows=("D", "E"),
        wheelchair_row="H",
        wheelchair_seats=(1, 2, 13, 14),
    ),
    # 10 x 18 = 180 seats.
    "standard": Layout(
        rows=10,
        seats_per_row=18,
        aisles=(3, 16),
        premium_rows=("E", "F", "G"),
        wheelchair_row="J",
        wheelchair_seats=(1, 2, 17, 18),
    ),
}
