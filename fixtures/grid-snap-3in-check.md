# Grid snap: the 3-inch reach check

Open `grid-snap-3in-check.json`. It holds two short vertical walls:

* the **upper** one at x = 5'-0" (60"), **on** the 6" grid;
* the **lower** one at x = 5'-3 1/4" (63.25", 5.27 ft), **off** the grid.

Run the macro `grid-snap-3in-check.fpm` (Macro > Run), or draw the four
walls by hand with the Interior wall tool, each from the right toward a
vertical wall. Watch the status bar: it reads the end as you draw.

| # | drawn at height | released near x | **the end must land at** | why |
|---|---|---|---|---|
| 1 | y = 6'-0", toward the upper wall | 6'-0" | **6'-0"** | 12" from the wall: no pull |
| 2 | y = 8'-0", toward the upper wall | 5'-6" | **5'-6"** | 6" from the wall: a reveal, left alone |
| 3 | y = 16'-0", toward the lower wall | 6'-0" | **6'-0"** | 8.75" from the wall: **no pull** -- this is the one that used to land on the wall, at 5.27 ft |
| 4 | y = 18'-0", toward the lower wall | 5'-6" | **5'-3 1/4"**, joined to the wall | 2.75" from it: inside the 3" reach, so it meets the wall |

The rule: **nothing pulls an end from more than 3 inches away.** Within 3
inches the end goes to the wall, so a wall that is off the grid can still be
met -- the grid point nearest any line is never more than 3" from it.

The macro releases an inch to the right of each grid line (x = 73" and 67")
so that the pointer's own pixel cannot tip the result at a low zoom; the end
still lands on the grid line named above.

Close without saving. Do not save over the check file.
