"""
solve.py – Layer‑by‑layer Rubik's cube solver
============================================

This module implements a deterministic solver for the 3×3×3 Rubik's cube
using a layer‑by‑layer (LBL) strategy.  The algorithm is adapted from
the open‑source `pglass/cube` project under the MIT licence.  It solves
the cube in the following steps:

1. **Cross:** Solve the four edges on the top face forming a cross.
2. **Corners:** Solve the four corners of the first layer.
3. **Second layer:** Place the four middle layer edges.
4. **Last layer edges:** Orient and permute the edges on the back face.
5. **Last layer corners:** Position and orient the four back corners.
6. **Last layer edges:** Finalise the top layer edges to complete the cube.

The solver collects the move sequence applied so that it can be used
elsewhere (for example, to feed instructions to a physical robot).  The
solver is not optimised for speed or move count; its primary goal is
educational clarity and reliability.
"""

from rubik import cube
from rubik.maths import Point

DEBUG = False  # enable to print intermediate cube states


class Solver:
    """A solver that uses a fixed sequence of algorithms to solve a cube."""

    def __init__(self, c: cube.Cube):
        self.cube = c
        self.colors = c.colors()
        self.moves: list[str] = []
        # Cache references to centre pieces for quick lookup
        self.left_piece  = self.cube.find_piece(self.cube.left_color())
        self.right_piece = self.cube.find_piece(self.cube.right_color())
        self.up_piece    = self.cube.find_piece(self.cube.up_color())
        self.down_piece  = self.cube.find_piece(self.cube.down_color())
        # Protect against infinite loops in algorithms
        self.inifinite_loop_max_iterations = 12

    def solve(self) -> None:
        """Execute the full solving routine in order."""
        if DEBUG:
            print(self.cube)
        self.cross()
        if DEBUG:
            print('Cross:\n', self.cube)
        self.cross_corners()
        if DEBUG:
            print('Corners:\n', self.cube)
        self.second_layer()
        if DEBUG:
            print('Second layer:\n', self.cube)
        self.back_face_edges()
        if DEBUG:
            print('Last layer edges\n', self.cube)
        self.last_layer_corners_position()
        if DEBUG:
            print('Last layer corners -- position\n', self.cube)
        self.last_layer_corners_orientation()
        if DEBUG:
            print('Last layer corners -- orientation\n', self.cube)
        self.last_layer_edges()
        if DEBUG:
            print('Solved\n', self.cube)

    def move(self, move_str: str) -> None:
        """Record and apply a sequence of moves to the cube."""
        self.moves.extend(move_str.split())
        self.cube.sequence(move_str)

    # --- Cross ---
    def cross(self) -> None:
        """Solve the cross on the front face."""
        if DEBUG:
            print("cross")
        fl_piece = self.cube.find_piece(self.cube.front_color(), self.cube.left_color())
        fr_piece = self.cube.find_piece(self.cube.front_color(), self.cube.right_color())
        fu_piece = self.cube.find_piece(self.cube.front_color(), self.cube.up_color())
        fd_piece = self.cube.find_piece(self.cube.front_color(), self.cube.down_color())
        # Solve left and right edges
        self._cross_left_or_right(fl_piece, self.left_piece, self.cube.left_color(), "L L", "E L Ei Li")
        self._cross_left_or_right(fr_piece, self.right_piece, self.cube.right_color(), "R R", "Ei R E Ri")
        # Rotate to solve up/down edges
        self.move("Z")
        self._cross_left_or_right(fd_piece, self.down_piece, self.cube.left_color(), "L L", "E L Ei Li")
        self._cross_left_or_right(fu_piece, self.up_piece, self.cube.right_color(), "R R", "Ei R E Ri")
        self.move("Zi")

    def _cross_left_or_right(self, edge_piece, face_piece, face_color, move_1, move_2) -> None:
        """Helper to place one of the cross edges on the left or right faces."""
        # If the edge is already correctly positioned and oriented, do nothing
        if (edge_piece.pos == (face_piece.pos.x, face_piece.pos.y, 1)
                and edge_piece.colors[2] == self.cube.front_color()):
            return
        # Bring the piece to z = -1 layer if necessary
        undo_move = None
        if edge_piece.pos.z == 0:
            pos = Point(edge_piece.pos)
            pos.x = 0  # pick the UP or DOWN face
            cw, cc = cube.get_rot_from_face(pos)
            if edge_piece.pos in (cube.LEFT + cube.UP, cube.RIGHT + cube.DOWN):
                self.move(cw)
                undo_move = cc
            else:
                self.move(cc)
                undo_move = cw
        elif edge_piece.pos.z == 1:
            pos = Point(edge_piece.pos)
            pos.z = 0
            cw, cc = cube.get_rot_from_face(pos)
            self.move(f"{cc} {cc}")
            # don't set the undo move if the piece starts out in the right position
            # (with wrong orientation) or we'll screw up the remainder of the algorithm
            if edge_piece.pos.x != face_piece.pos.x:
                undo_move = f"{cw} {cw}"
        # Ensure z == -1
        assert edge_piece.pos.z == -1
        # Rotate around the back until the piece is on the correct face
        count = 0
        while (edge_piece.pos.x, edge_piece.pos.y) != (face_piece.pos.x, face_piece.pos.y):
            self.move("B")
            count += 1
            if count >= self.inifinite_loop_max_iterations:
                raise Exception("Stuck in loop - unsolvable cube?\n" + str(self.cube))
        # If we moved a correctly‑placed piece, restore it
        if undo_move:
            self.move(undo_move)
        # Orient the edge
        if edge_piece.colors[0] == face_color:
            self.move(move_1)
        else:
            self.move(move_2)

    # --- Cross corners ---
    def cross_corners(self) -> None:
        """Place the four first‑layer corners."""
        if DEBUG:
            print("cross_corners")
        fld_piece = self.cube.find_piece(self.cube.front_color(), self.cube.left_color(), self.cube.down_color())
        flu_piece = self.cube.find_piece(self.cube.front_color(), self.cube.left_color(), self.cube.up_color())
        frd_piece = self.cube.find_piece(self.cube.front_color(), self.cube.right_color(), self.cube.down_color())
        fru_piece = self.cube.find_piece(self.cube.front_color(), self.cube.right_color(), self.cube.up_color())
        # Place corners in sequence, rotating the cube to reuse algorithms
        self.place_frd_corner(frd_piece, self.right_piece, self.down_piece, self.cube.front_color())
        self.move("Z")
        self.place_frd_corner(fru_piece, self.up_piece, self.right_piece, self.cube.front_color())
        self.move("Z")
        self.place_frd_corner(flu_piece, self.left_piece, self.up_piece, self.cube.front_color())
        self.move("Z")
        self.place_frd_corner(fld_piece, self.down_piece, self.left_piece, self.cube.front_color())
        self.move("Z")

    def place_frd_corner(self, corner_piece, right_piece, down_piece, front_color) -> None:
        """Place a single front‑right‑down corner cubie."""
        # Rotate corner to z = -1
        if corner_piece.pos.z == 1:
            pos = Point(corner_piece.pos)
            pos.x = pos.z = 0
            cw, cc = cube.get_rot_from_face(pos)
            # be careful not to screw up other pieces on the front face
            count = 0
            undo_move = cc
            while corner_piece.pos.z != -1:
                self.move(cw)
                count += 1
            if count > 1:
                # go the other direction if needed
                for _ in range(count):
                    self.move(cc)
                count = 0
                while corner_piece.pos.z != -1:
                    self.move(cc)
                    count += 1
                undo_move = cw
            # insert one back rotation to move into position and then restore
            self.move("B")
            for _ in range(count):
                self.move(undo_move)
        # Rotate to be directly below its destination
        while (corner_piece.pos.x, corner_piece.pos.y) != (right_piece.pos.x, down_piece.pos.y):
            self.move("B")
        # There are three possible orientations for a corner
        if corner_piece.colors[0] == front_color:
            self.move("B D Bi Di")
        elif corner_piece.colors[1] == front_color:
            self.move("Bi Ri B R")
        else:
            self.move("Ri B B R Bi Bi D Bi Di")

    # --- Middle layer ---
    def second_layer(self) -> None:
        """Solve the middle layer edges."""
        rd_piece = self.cube.find_piece(self.cube.right_color(), self.cube.down_color())
        ru_piece = self.cube.find_piece(self.cube.right_color(), self.cube.up_color())
        ld_piece = self.cube.find_piece(self.cube.left_color(), self.cube.down_color())
        lu_piece = self.cube.find_piece(self.cube.left_color(), self.cube.up_color())
        # Repeatedly place edges, rotating the cube between placements
        self.place_middle_layer_ld_edge(ld_piece, self.cube.left_color(), self.cube.down_color())
        self.move("Z")
        self.place_middle_layer_ld_edge(rd_piece, self.cube.left_color(), self.cube.down_color())
        self.move("Z")
        self.place_middle_layer_ld_edge(ru_piece, self.cube.left_color(), self.cube.down_color())
        self.move("Z")
        self.place_middle_layer_ld_edge(lu_piece, self.cube.left_color(), self.cube.down_color())
        self.move("Z")

    def place_middle_layer_ld_edge(self, ld_piece, left_color, down_color) -> None:
        """Place a single middle layer edge from the left or right faces."""
        # Move the edge into the z == -1 layer
        if ld_piece.pos.z == 0:
            count = 0
            while (ld_piece.pos.x, ld_piece.pos.y) != (-1, -1):
                self.move("Z")
                count += 1
            self.move("B L Bi Li Bi Di B D")
            for _ in range(count):
                self.move("Zi")
        assert ld_piece.pos.z == -1
        if ld_piece.colors[2] == left_color:
            # left color is on the back face, move piece to the down face
            while ld_piece.pos.y != -1:
                self.move("B")
            self.move("B L Bi Li Bi Di B D")
        elif ld_piece.colors[2] == down_color:
            # down color is on the back face, move to left face
            while ld_piece.pos.x != -1:
                self.move("B")
            self.move("Bi Di B D B L Bi Li")
        else:
            raise Exception("BUG!!")

    # --- Last layer edges (back face) ---
    def back_face_edges(self) -> None:
        """Orient the last layer edges to form a cross on the back face."""
        # rotate BACK to FRONT
        self.move("X X")
        # Helper state checks for orientation patterns
        def state1():
            return (self.cube[0, 1, 1].colors[2] == self.cube.front_color()
                    and self.cube[-1, 0, 1].colors[2] == self.cube.front_color()
                    and self.cube[0, -1, 1].colors[2] == self.cube.front_color()
                    and self.cube[1, 0, 1].colors[2] == self.cube.front_color())
        def state2():
            return (self.cube[0, 1, 1].colors[2] == self.cube.front_color()
                    and self.cube[-1, 0, 1].colors[2] == self.cube.front_color())
        def state3():
            return (self.cube[-1, 0, 1].colors[2] == self.cube.front_color()
                    and self.cube[1, 0, 1].colors[2] == self.cube.front_color())
        def state4():
            return (self.cube[0, 1, 1].colors[2] != self.cube.front_color()
                    and self.cube[-1, 0, 1].colors[2] != self.cube.front_color()
                    and self.cube[0, -1, 1].colors[2] != self.cube.front_color()
                    and self.cube[1, 0, 1].colors[2] != self.cube.front_color())
        # Iterate until the cross is oriented
        count = 0
        while not state1():
            if state4() or state2():
                self.move("D F R Fi Ri Di")
            elif state3():
                self.move("D R F Ri Fi Di")
            else:
                self.move("F")
            count += 1
            if count >= self.inifinite_loop_max_iterations:
                raise Exception("Stuck in loop - unsolvable cube\n" + str(self.cube))
        self.move("Xi Xi")

    # --- Last layer corners position ---
    def last_layer_corners_position(self) -> None:
        """Permute the last layer corners into their correct positions."""
        self.move("X X")
        # Moves that swap two corners on the UP face
        move_1 = "Li Fi L D F Di Li F L F F "  # swaps positions 1 and 2
        move_2 = "F Li Fi L D F Di Li F L F "  # swaps positions 1 and 3
        # Identify corners
        c1 = self.cube.find_piece(self.cube.front_color(), self.cube.right_color(), self.cube.down_color())
        c2 = self.cube.find_piece(self.cube.front_color(), self.cube.left_color(), self.cube.down_color())
        c3 = self.cube.find_piece(self.cube.front_color(), self.cube.right_color(), self.cube.up_color())
        c4 = self.cube.find_piece(self.cube.front_color(), self.cube.left_color(), self.cube.up_color())
        # Place corner 4
        if c4.pos == Point(1, -1, 1):
            self.move(move_1 + "Zi " + move_1 + " Z")
        elif c4.pos == Point(1, 1, 1):
            self.move("Z " + move_2 + " Zi")
        elif c4.pos == Point(-1, -1, 1):
            self.move("Zi " + move_1 + " Z")
        assert c4.pos == Point(-1, 1, 1)
        # Place corner 2
        if c2.pos == Point(1, 1, 1):
            self.move(move_2 + move_1)
        elif c2.pos == Point(1, -1, 1):
            self.move(move_1)
        assert c2.pos == Point(-1, -1, 1)
        # Place corners 1 and 3
        if c3.pos == Point(1, -1, 1):
            self.move(move_2)
        assert c3.pos == Point(1, 1, 1)
        assert c1.pos == Point(1, -1, 1)
        self.move("Xi Xi")

    # --- Last layer corners orientation ---
    def last_layer_corners_orientation(self) -> None:
        """Orient the last layer corners correctly."""
        self.move("X X")
        # Define pattern detection functions for different states
        def state1():
            return (self.cube[1, 1, 1].colors[1] == self.cube.front_color()
                    and self.cube[-1, -1, 1].colors[1] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[0] == self.cube.front_color())
        def state2():
            return (self.cube[-1, 1, 1].colors[1] == self.cube.front_color()
                    and self.cube[1, 1, 1].colors[0] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[1] == self.cube.front_color())
        def state3():
            return (self.cube[-1, -1, 1].colors[1] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[1] == self.cube.front_color()
                    and self.cube[-1, 1, 1].colors[2] == self.cube.front_color()
                    and self.cube[1, 1, 1].colors[2] == self.cube.front_color())
        def state4():
            return (self.cube[-1, 1, 1].colors[1] == self.cube.front_color()
                    and self.cube[-1, -1, 1].colors[1] == self.cube.front_color()
                    and self.cube[1, 1, 1].colors[2] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[2] == self.cube.front_color())
        def state5():
            return (self.cube[-1, 1, 1].colors[1] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[0] == self.cube.front_color())
        def state6():
            return (self.cube[1, 1, 1].colors[1] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[1] == self.cube.front_color()
                    and self.cube[-1, -1, 1].colors[0] == self.cube.front_color()
                    and self.cube[-1, 1, 1].colors[0] == self.cube.front_color())
        def state7():
            return (self.cube[1, 1, 1].colors[0] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[0] == self.cube.front_color()
                    and self.cube[-1, -1, 1].colors[0] == self.cube.front_color()
                    and self.cube[-1, 1, 1].colors[0] == self.cube.front_color())
        def state8():
            return (self.cube[1, 1, 1].colors[2] == self.cube.front_color()
                    and self.cube[1, -1, 1].colors[2] == self.cube.front_color()
                    and self.cube[-1, -1, 1].colors[2] == self.cube.front_color()
                    and self.cube[-1, 1, 1].colors[2] == self.cube.front_color())
        move_1 = "Ri Fi R Fi Ri F F R F F "
        move_2 = "R F Ri F R F F Ri F F "
        count = 0
        while not state8():
            if state1():
                self.move(move_1)
            elif state2():
                self.move(move_2)
            elif state3():
                self.move(move_2 + "F F " + move_1)
            elif state4():
                self.move(move_2 + move_1)
            elif state5():
                self.move(move_1 + "F " + move_2)
            elif state6():
                self.move(move_1 + "Fi " + move_1)
            elif state7():
                self.move(move_1 + "F F " + move_1)
            else:
                self.move("F")
            count += 1
            if count >= self.inifinite_loop_max_iterations:
                raise Exception("Stuck in loop - unsolvable cube:\n" + str(self.cube))
        # rotate corners into correct locations (cube is inverted, so swap up and down colours)
        bru_corner = self.cube.find_piece(self.cube.front_color(), self.cube.right_color(), self.cube.up_color())
        while bru_corner.pos != Point(1, 1, 1):
            self.move("F")
        self.move("Xi Xi")

    # --- Final last layer edges ---
    def last_layer_edges(self) -> None:
        """Complete the last layer edge cycles to finish the cube."""
        self.move("X X")
        # Identify the four edges on the last layer
        br_edge = self.cube.find_piece(self.cube.front_color(), self.cube.right_color())
        bl_edge = self.cube.find_piece(self.cube.front_color(), self.cube.left_color())
        bu_edge = self.cube.find_piece(self.cube.front_color(), self.cube.up_color())
        bd_edge = self.cube.find_piece(self.cube.front_color(), self.cube.down_color())
        # Helper state checks
        def state1():
            return (bu_edge.colors[2] != self.cube.front_color()
                    and bd_edge.colors[2] != self.cube.front_color()
                    and bl_edge.colors[2] != self.cube.front_color()
                    and br_edge.colors[2] != self.cube.front_color())
        def state2():
            return (bu_edge.colors[2] == self.cube.front_color()
                    or bd_edge.colors[2] == self.cube.front_color()
                    or bl_edge.colors[2] == self.cube.front_color()
                    or br_edge.colors[2] == self.cube.front_color())
        cycle_move = "R R F D Ui R R Di U F R R"
        h_pattern_move = "Ri S Ri Ri S S Ri Fi Fi R Si Si Ri Ri Si R Fi Fi "
        fish_move = "Di Li " + h_pattern_move + " L D"
        if state1():
            self._handle_last_layer_state1(br_edge, bl_edge, bu_edge, bd_edge, cycle_move, h_pattern_move)
        if state2():
            self._handle_last_layer_state2(br_edge, bl_edge, bu_edge, bd_edge, cycle_move)
        # Additional patterns
        def h_pattern1():
            return (self.cube[-1, 0, 1].colors[0] != self.cube.left_color()
                    and self.cube[1, 0, 1].colors[0] != self.cube.right_color()
                    and self.cube[0, -1, 1].colors[1] == self.cube.down_color()
                    and self.cube[0, 1, 1].colors[1] == self.cube.up_color())
        def h_pattern2():
            return (self.cube[-1, 0, 1].colors[0] == self.cube.left_color()
                    and self.cube[1, 0, 1].colors[0] == self.cube.right_color()
                    and self.cube[0, -1, 1].colors[1] == self.cube.front_color()
                    and self.cube[0, 1, 1].colors[1] == self.cube.front_color())
        def fish_pattern():
            return (self.cube[cube.FRONT + cube.DOWN].colors[2] == self.cube.down_color()
                    and self.cube[cube.FRONT + cube.RIGHT].colors[2] == self.cube.right_color()
                    and self.cube[cube.FRONT + cube.DOWN].colors[1] == self.cube.front_color()
                    and self.cube[cube.FRONT + cube.RIGHT].colors[0] == self.cube.front_color())
        count = 0
        while not self.cube.is_solved():
            for _ in range(4):
                if fish_pattern():
                    self.move(fish_move)
                    if self.cube.is_solved():
                        return
                else:
                    self.move("Z")
            if h_pattern1():
                self.move(h_pattern_move)
            elif h_pattern2():
                self.move("Z " + h_pattern_move + "Zi")
            else:
                self.move(cycle_move)
            count += 1
            if count >= self.inifinite_loop_max_iterations:
                raise Exception("Stuck in loop - unsolvable cube:\n" + str(self.cube))
        self.move("Xi Xi")

    # Helpers for last layer edges state handling
    def _handle_last_layer_state1(self, br_edge, bl_edge, bu_edge, bd_edge, cycle_move: str, h_move: str) -> None:
        if DEBUG:
            print("_handle_last_layer_state1")
        def check_edge_lr():
            return self.cube[cube.LEFT + cube.FRONT].colors[2] == self.cube.left_color()
        count = 0
        while not check_edge_lr():
            self.move("F")
            count += 1
            if count == 4:
                raise Exception("Bug: Failed to handle last layer state1")
        self.move(h_move)
        for _ in range(count):
            self.move("Fi")

    def _handle_last_layer_state2(self, br_edge, bl_edge, bu_edge, bd_edge, cycle_move: str) -> None:
        if DEBUG:
            print("_handle_last_layer_state2")
        def correct_edge():
            piece = self.cube[cube.LEFT + cube.FRONT]
            if piece.colors[2] == self.cube.front_color() and piece.colors[0] == self.cube.left_color():
                return piece
            piece = self.cube[cube.RIGHT + cube.FRONT]
            if piece.colors[2] == self.cube.front_color() and piece.colors[0] == self.cube.right_color():
                return piece
            piece = self.cube[cube.UP + cube.FRONT]
            if piece.colors[2] == self.cube.front_color() and piece.colors[1] == self.cube.up_color():
                return piece
            piece = self.cube[cube.DOWN + cube.FRONT]
            if piece.colors[2] == self.cube.front_color() and piece.colors[1] == self.cube.down_color():
                return piece
            return None
        count = 0
        while True:
            edge = correct_edge()
            if edge is None:
                self.move(cycle_move)
            else:
                break
            count += 1
            if count % 3 == 0:
                self.move("Z")
            if count >= self.inifinite_loop_max_iterations:
                raise Exception("Stuck in loop - unsolvable cube:\n" + str(self.cube))
        while edge.pos != Point(-1, 0, 1):
            self.move("Z")
        assert (self.cube[cube.LEFT + cube.FRONT].colors[2] == self.cube.front_color()
                and self.cube[cube.LEFT + cube.FRONT].colors[0] == self.cube.left_color())