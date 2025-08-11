"""
Example use of the rubik solver package
======================================

This script demonstrates how to scramble and solve a 3×3×3 Rubik's cube
using the layer‑by‑layer solver implemented in the ``rubik`` package.

Usage
-----
Running the script will produce a random scramble, solve it and report
statistics about the solution:

```
python solve_cube.py
```

The output shows the scramble moves, the solution moves and verifies
that the cube returns to the solved state.
"""

import random
from rubik.cube import Cube
from rubik.solve import Solver
from rubik.optimize import optimize_moves

# Sticker string representing a solved cube.  The order of faces is
# orange (O), yellow (Y), white (W), green (G), blue (B) and red (R)
SOLVED_CUBE_STR = "OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR"

# Move names used for scrambling.  We use only face rotations here; slice
# rotations and cube rotations are omitted for clarity.
SCRAMBLE_MOVES = ["L", "R", "U", "D", "F", "B", "Li", "Ri", "Ui", "Di", "Fi", "Bi"]


def generate_scramble(length: int = 25) -> str:
    """Return a scramble as a space‑separated string of random moves."""
    return " ".join(random.choice(SCRAMBLE_MOVES) for _ in range(length))


def solve_random_cube() -> None:
    """Scramble a cube, solve it and report the results."""
    scramble = generate_scramble()
    cube_obj = Cube(SOLVED_CUBE_STR)
    cube_obj.sequence(scramble)
    print("Scramble:", scramble)
    solver = Solver(cube_obj)
    solver.solve()
    solution_moves = solver.moves
    optimised_moves = optimize_moves(solution_moves)
    print(f"Solver produced {len(solution_moves)} moves.")
    print("Solution (raw):", " ".join(solution_moves))
    print(f"Optimised to {len(optimised_moves)} moves.")
    print("Solution (optimised):", " ".join(optimised_moves))
    # Verify solution
    check_cube = Cube(SOLVED_CUBE_STR)
    check_cube.sequence(scramble)
    check_cube.sequence(" ".join(optimised_moves))
    assert check_cube.is_solved(), "Cube should be solved after applying the solution!"
    print("Verification passed: cube is solved.")


if __name__ == "__main__":
    solve_random_cube()