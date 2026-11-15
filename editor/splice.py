"""
splice.py - pure keep-list maths for inserting audio into a clip.

No GUI and no disk access: it only rewrites a list of Keep ranges.
"""
from .timeline import Keep

EPS = 1e-6   # seconds; positions closer than this count as "on the boundary"


# Return a new list of keeps with `lengths` (seconds, one per inserted file)
# spliced in at time `at`.
#
#   - keeps that end before `at` are unchanged
#   - keeps that start after `at` are shifted later by the total inserted length
#   - a keep that straddles `at` is split in two around the new audio
#     (fade-in stays on the left half, fade-out on the right half)
#   - the new pieces sit between the keeps before and after `at`
def insert_into_keeps(keeps, at, lengths):

    # New pieces sit back to back starting at the insertion point
    new_pieces = []
    cursor = at
    for length in lengths:
        if length > 0:
            new_pieces.append(Keep(cursor, cursor + length))
            cursor += length
    shift = cursor - at

    result = []
    placed = False
    for keep in keeps:

        # Entirely before the insertion point
        if keep.end <= at + EPS:
            result.append(keep.copy())
            continue

        # Entirely after: drop the new pieces in first, then shift this keep
        if keep.start >= at - EPS:
            if not placed:
                result.extend(new_pieces)
                placed = True
            moved = keep.copy()
            moved.start += shift
            moved.end += shift
            result.append(moved)
            continue

        # Straddles the insertion point: split it
        left = Keep(keep.start, at, keep.fade_in, None)
        right = Keep(at + shift, keep.end + shift, None, keep.fade_out)
        result.append(left)
        result.extend(new_pieces)
        result.append(right)
        placed = True

    if not placed:
        result.extend(new_pieces)
    return result