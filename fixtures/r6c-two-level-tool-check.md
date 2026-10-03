# R6.c two-level tool check

Open `r6c-two-level-tool-check.json`. It opens on `upper`: the solid target is
on the right. Turn on **Floors > Show other floors** to reveal the grey lower
target on the left.

Each check is independent. Reopen the fixture without saving before the next
one. A crash is a failure; record the last action and stop.

1. **Ghosted roof does not take the ridge press.** Choose **Roof > Sketch
   ridge**. Drag along the grey lower ridge from left to right. **PASS:** a new
   ridge appears under the drag and waits for its eaves. Close without saving.
2. **Eaves stay on the edited level.** Reopen. Sketch a horizontal ridge in
   the empty strip below the two boxes. Click the lower box's grey bottom wall.
   **PASS:** it is refused and the ridge still waits. Click the upper box's
   solid bottom wall. **PASS:** it is accepted. Close without saving.
3. **A level switch settles the old gesture.** Reopen. Sketch a horizontal
   ridge directly below the upper box and release it, but do not click an eaves
   wall. Switch to `default`. **PASS:** the new roof remains on `upper` and is
   now grey; it did not attach to a lower-level wall. Close without saving.
4. **The dialog distinguishes relative from building height.** Reopen.
   Right-click the round marker at the right end of the solid upper ridge.
   **PASS:** the blue line says the level base is 120 inches, the eaves stand
   at 216 inches, and the ridge stands at 264 inches. Cancel the dialog.
5. **A dormer cannot use a host from another level.** Reopen. Choose **Roof >
   Sketch dormer** and drag on either slope of the grey lower roof, away from
   its ridge. **PASS:** no dormer appears and the status bar names `default` as
   the roof's level.

