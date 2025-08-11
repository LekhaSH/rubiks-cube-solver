"""
cube.py – Rubik's cube representation
====================================

This module provides a 3×3×3 Rubik's cube data structure and methods for
applying standard cube rotations.  The implementation is adapted from
the open‑source project `pglass/cube` under the MIT licence.

The cube is represented by ``Piece`` objects positioned in a 3D coordinate
system.  Faces, edges, and corners are assigned coordinates on the axes:

* +x is the right direction, –x is left
* +y is up, –y is down
* +z is front, –z is back

Each ``Piece`` stores the colours of its stickers along the axes.  The
``Cube`` class groups together the pieces and exposes methods
corresponding to Rubik's cube moves (e.g. ``R``, ``U``, ``F`` etc.).

Example
-------
>>> from rubik.cube import Cube
>>> c = Cube("OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR")
>>> c.sequence("R U Ri Ui")
>>> print(c)

"""

import string
from rubik.maths import Point, Matrix

# Direction constants; these also serve as vectors for rotations
RIGHT = X_AXIS = Point(1, 0, 0)
LEFT            = Point(-1, 0, 0)
UP    = Y_AXIS  = Point(0, 1, 0)
DOWN            = Point(0, -1, 0)
FRONT = Z_AXIS  = Point(0, 0, 1)
BACK            = Point(0, 0, -1)

# Piece type identifiers
FACE = 'face'
EDGE = 'edge'
CORNER = 'corner'

# 90° rotations in the XY plane.  CW is clockwise, CC is counter‑clockwise.
ROT_XY_CW = Matrix(0, 1, 0,
                   -1, 0, 0,
                   0, 0, 1)
ROT_XY_CC = Matrix(0, -1, 0,
                   1, 0, 0,
                   0, 0, 1)

# 90° rotations in the XZ plane (around the y‑axis when viewed pointing toward you).
ROT_XZ_CW = Matrix(0, 0, -1,
                   0, 1, 0,
                   1, 0, 0)
ROT_XZ_CC = Matrix(0, 0, 1,
                   0, 1, 0,
                   -1, 0, 0)

# 90° rotations in the YZ plane (around the x‑axis when viewed pointing toward you).
ROT_YZ_CW = Matrix(1, 0, 0,
                   0, 0, 1,
                   0, -1, 0)
ROT_YZ_CC = Matrix(1, 0, 0,
                   0, 0, -1,
                   0, 1, 0)


def get_rot_from_face(face):
    """Return the clockwise and counter‑clockwise move names for the given face.

    Parameters
    ----------
    face : Point
        One of ``FRONT``, ``BACK``, ``LEFT``, ``RIGHT``, ``UP`` or ``DOWN``.

    Returns
    -------
    tuple of str
        A pair ``(CW, CC)`` representing the rotation names used by
        ``Cube.sequence()``.
    """
    if face == RIGHT:
        return "R", "Ri"
    elif face == LEFT:
        return "L", "Li"
    elif face == UP:
        return "U", "Ui"
    elif face == DOWN:
        return "D", "Di"
    elif face == FRONT:
        return "F", "Fi"
    elif face == BACK:
        return "B", "Bi"
    return None


class Piece:
    """Represents a single cubie on the Rubik's cube."""

    def __init__(self, pos, colors):
        """Construct a piece at the given position with the given colours.

        Parameters
        ----------
        pos : Point
            A 3D coordinate with components in {-1, 0, 1}.
        colors : tuple of length 3
            Gives the colour on the x, y and z faces (``None`` if the
            sticker is missing on that axis).
        """
        assert all(isinstance(x, int) and x in (-1, 0, 1) for x in pos)
        assert len(colors) == 3
        self.pos = pos
        self.colors = list(colors)
        self._set_piece_type()

    def __str__(self):
        colors = "".join(c for c in self.colors if c is not None)
        return f"({self.type}, {colors}, {self.pos})"

    def _set_piece_type(self):
        if self.colors.count(None) == 2:
            self.type = FACE
        elif self.colors.count(None) == 1:
            self.type = EDGE
        elif self.colors.count(None) == 0:
            self.type = CORNER
        else:
            raise ValueError(f"Must have 1, 2 or 3 colours – given colors={self.colors}")

    def rotate(self, matrix):
        """Apply the given rotation matrix to this piece and adjust sticker positions."""
        before = self.pos
        self.pos = matrix * self.pos
        # We need to swap colours so that stickers remain on the correct faces.
        rot = self.pos - before
        if not any(rot):
            return  # no change occurred
        if rot.count(0) == 2:
            rot += matrix * rot
        # Exactly two components of rot are non‑zero
        i, j = (i for i, x in enumerate(rot) if x != 0)
        self.colors[i], self.colors[j] = self.colors[j], self.colors[i]


class Cube:
    """Stores pieces which are addressed through an x–y–z coordinate system.

    * –x is the LEFT direction, +x is the RIGHT direction
    * –y is the DOWN direction, +y is the UP direction
    * –z is the BACK direction, +z is the FRONT direction

    The cube is constructed from a 54‑character string where each
    character represents a sticker in the net diagram.  See
    ``Cube.__init__`` for details.
    """

    def _from_cube(self, c):
        # Copy pieces from another cube
        self.faces = [Piece(pos=Point(p.pos), colors=p.colors) for p in c.faces]
        self.edges = [Piece(pos=Point(p.pos), colors=p.colors) for p in c.edges]
        self.corners = [Piece(pos=Point(p.pos), colors=p.colors) for p in c.corners]
        self.pieces = self.faces + self.edges + self.corners

    def _assert_data(self):
        assert len(self.pieces) == 26
        assert all(p.type == FACE for p in self.faces)
        assert all(p.type == EDGE for p in self.edges)
        assert all(p.type == CORNER for p in self.corners)

    def __init__(self, cube_str):
        """Construct a cube from a 54‑character string or copy another cube.

        The string format looks like:

            UUU
            UUU
            UUU
        LLL FFF RRR BBB
        LLL FFF RRR BBB
        LLL FFF RRR BBB
            DDD
            DDD
            DDD

        Indices (0–53) are indicated in comments in the original
        implementation.  The back face is mirrored horizontally
        during unfolding.  Each sticker must be a single character.
        """
        if isinstance(cube_str, Cube):
            self._from_cube(cube_str)
            return

        # remove whitespace
        cube_str = "".join(x for x in cube_str if x not in string.whitespace)
        assert len(cube_str) == 54

        # faces
        self.faces = (
            Piece(pos=RIGHT, colors=(cube_str[28], None, None)),
            Piece(pos=LEFT,  colors=(cube_str[22], None, None)),
            Piece(pos=UP,    colors=(None, cube_str[4],  None)),
            Piece(pos=DOWN,  colors=(None, cube_str[49], None)),
            Piece(pos=FRONT, colors=(None, None, cube_str[25])),
            Piece(pos=BACK,  colors=(None, None, cube_str[31]))
        )
        # edges
        self.edges = (
            Piece(pos=RIGHT + UP,    colors=(cube_str[16], cube_str[5], None)),
            Piece(pos=RIGHT + DOWN,  colors=(cube_str[40], cube_str[50], None)),
            Piece(pos=RIGHT + FRONT, colors=(cube_str[27], None, cube_str[26])),
            Piece(pos=RIGHT + BACK,  colors=(cube_str[29], None, cube_str[30])),
            Piece(pos=LEFT + UP,     colors=(cube_str[10], cube_str[3], None)),
            Piece(pos=LEFT + DOWN,   colors=(cube_str[34], cube_str[48], None)),
            Piece(pos=LEFT + FRONT,  colors=(cube_str[23], None, cube_str[24])),
            Piece(pos=LEFT + BACK,   colors=(cube_str[21], None, cube_str[32])),
            Piece(pos=UP + FRONT,    colors=(None, cube_str[7],  cube_str[13])),
            Piece(pos=UP + BACK,     colors=(None, cube_str[1],  cube_str[19])),
            Piece(pos=DOWN + FRONT,  colors=(None, cube_str[46], cube_str[37])),
            Piece(pos=DOWN + BACK,   colors=(None, cube_str[52], cube_str[43]))
        )
        # corners
        self.corners = (
            Piece(pos=RIGHT + UP + FRONT,   colors=(cube_str[15], cube_str[8], cube_str[14])),
            Piece(pos=RIGHT + UP + BACK,    colors=(cube_str[17], cube_str[2], cube_str[18])),
            Piece(pos=RIGHT + DOWN + FRONT, colors=(cube_str[39], cube_str[47], cube_str[38])),
            Piece(pos=RIGHT + DOWN + BACK,  colors=(cube_str[41], cube_str[53], cube_str[42])),
            Piece(pos=LEFT + UP + FRONT,    colors=(cube_str[11], cube_str[6], cube_str[12])),
            Piece(pos=LEFT + UP + BACK,     colors=(cube_str[9],  cube_str[0], cube_str[20])),
            Piece(pos=LEFT + DOWN + FRONT,  colors=(cube_str[35], cube_str[45], cube_str[36])),
            Piece(pos=LEFT + DOWN + BACK,   colors=(cube_str[33], cube_str[51], cube_str[44]))
        )
        self.pieces = self.faces + self.edges + self.corners
        self._assert_data()

    def is_solved(self):
        """Return True if the cube is in the solved state."""
        def check(colors):
            assert len(colors) == 9
            return all(c == colors[0] for c in colors)
        return (check([piece.colors[2] for piece in self._face(FRONT)]) and
                check([piece.colors[2] for piece in self._face(BACK)]) and
                check([piece.colors[1] for piece in self._face(UP)]) and
                check([piece.colors[1] for piece in self._face(DOWN)]) and
                check([piece.colors[0] for piece in self._face(LEFT)]) and
                check([piece.colors[0] for piece in self._face(RIGHT)]))

    def _face(self, axis):
        """Return a list of pieces on the given face.

        Parameters
        ----------
        axis : Point
            One of ``LEFT``, ``RIGHT``, ``UP``, ``DOWN``, ``FRONT`` or ``BACK``.
        """
        assert axis.count(0) == 2
        return [p for p in self.pieces if p.pos.dot(axis) > 0]

    def _slice(self, plane):
        """Return a list of pieces in the given slice.

        The plane must be the sum of two axis constants (e.g. ``X_AXIS + Y_AXIS``).
        """
        assert plane.count(0) == 1
        i = next(i for i, x in enumerate(plane) if x == 0)
        return [p for p in self.pieces if p.pos[i] == 0]

    def _rotate_face(self, face, matrix):
        self._rotate_pieces(self._face(face), matrix)

    def _rotate_slice(self, plane, matrix):
        self._rotate_pieces(self._slice(plane), matrix)

    def _rotate_pieces(self, pieces, matrix):
        for piece in pieces:
            piece.rotate(matrix)

    # Standard Rubik's Cube Notation: http://ruwix.com/the-rubiks-cube/notation/
    def L(self):  self._rotate_face(LEFT, ROT_YZ_CC)
    def Li(self): self._rotate_face(LEFT, ROT_YZ_CW)
    def R(self):  self._rotate_face(RIGHT, ROT_YZ_CW)
    def Ri(self): self._rotate_face(RIGHT, ROT_YZ_CC)
    def U(self):  self._rotate_face(UP, ROT_XZ_CW)
    def Ui(self): self._rotate_face(UP, ROT_XZ_CC)
    def D(self):  self._rotate_face(DOWN, ROT_XZ_CC)
    def Di(self): self._rotate_face(DOWN, ROT_XZ_CW)
    def F(self):  self._rotate_face(FRONT, ROT_XY_CW)
    def Fi(self): self._rotate_face(FRONT, ROT_XY_CC)
    def B(self):  self._rotate_face(BACK, ROT_XY_CC)
    def Bi(self): self._rotate_face(BACK, ROT_XY_CW)
    def M(self):  self._rotate_slice(Y_AXIS + Z_AXIS, ROT_YZ_CC)
    def Mi(self): self._rotate_slice(Y_AXIS + Z_AXIS, ROT_YZ_CW)
    def E(self):  self._rotate_slice(X_AXIS + Z_AXIS, ROT_XZ_CC)
    def Ei(self): self._rotate_slice(X_AXIS + Z_AXIS, ROT_XZ_CW)
    def S(self):  self._rotate_slice(X_AXIS + Y_AXIS, ROT_XY_CW)
    def Si(self): self._rotate_slice(X_AXIS + Y_AXIS, ROT_XY_CC)
    def X(self):  self._rotate_pieces(self.pieces, ROT_YZ_CW)
    def Xi(self): self._rotate_pieces(self.pieces, ROT_YZ_CC)
    def Y(self):  self._rotate_pieces(self.pieces, ROT_XZ_CW)
    def Yi(self): self._rotate_pieces(self.pieces, ROT_XZ_CC)
    def Z(self):  self._rotate_pieces(self.pieces, ROT_XY_CW)
    def Zi(self): self._rotate_pieces(self.pieces, ROT_XY_CC)

    def sequence(self, move_str):
        """Apply a sequence of moves expressed as space‑delimited notations."""
        moves = [getattr(self, name) for name in move_str.split()]
        for move in moves:
            move()

    def find_piece(self, *colors):
        """Return the piece that contains exactly the given colours."""
        if None in colors:
            return None
        for p in self.pieces:
            if p.colors.count(None) == 3 - len(colors) and all(c in p.colors for c in colors):
                return p
        return None

    def get_piece(self, x, y, z):
        """Return the ``Piece`` at the given coordinates."""
        point = Point(x, y, z)
        for p in self.pieces:
            if p.pos == point:
                return p

    def __getitem__(self, *args):
        if len(args) == 1:
            return self.get_piece(*args[0])
        return self.get_piece(*args)

    def __eq__(self, other):
        return isinstance(other, Cube) and self._color_list() == other._color_list()

    def __ne__(self, other):
        return not (self == other)

    def colors(self):
        """Return a set containing the colours of all stickers on the cube."""
        return set(c for piece in self.pieces for c in piece.colors if c is not None)

    # Helper accessors for the centre colours
    def left_color(self): return self[LEFT].colors[0]
    def right_color(self): return self[RIGHT].colors[0]
    def up_color(self): return self[UP].colors[1]
    def down_color(self): return self[DOWN].colors[1]
    def front_color(self): return self[FRONT].colors[2]
    def back_color(self): return self[BACK].colors[2]

    def _color_list(self):
        """Return the colours in unfolded net order for rendering and comparison."""
        right = [p.colors[0] for p in sorted(self._face(RIGHT), key=lambda p: (-p.pos.y, -p.pos.z))]
        left  = [p.colors[0] for p in sorted(self._face(LEFT),  key=lambda p: (-p.pos.y, p.pos.z))]
        up    = [p.colors[1] for p in sorted(self._face(UP),    key=lambda p: (p.pos.z, p.pos.x))]
        down  = [p.colors[1] for p in sorted(self._face(DOWN),  key=lambda p: (-p.pos.z, p.pos.x))]
        front = [p.colors[2] for p in sorted(self._face(FRONT), key=lambda p: (-p.pos.y, p.pos.x))]
        back  = [p.colors[2] for p in sorted(self._face(BACK),  key=lambda p: (-p.pos.y, -p.pos.x))]
        return (up + left[0:3] + front[0:3] + right[0:3] + back[0:3] +
                left[3:6] + front[3:6] + right[3:6] + back[3:6] +
                left[6:9] + front[6:9] + right[6:9] + back[6:9] + down)

    def flat_str(self):
        """Return a flat string representation of the cube's colours."""
        return "".join(x for x in str(self) if x not in string.whitespace)

    def __str__(self):
        template = ("    {}{}{}\n"
                    "    {}{}{}\n"
                    "    {}{}{}\n"
                    "{}{}{} {}{}{} {}{}{} {}{}{}\n"
                    "{}{}{} {}{}{} {}{}{} {}{}{}\n"
                    "{}{}{} {}{}{} {}{}{} {}{}{}\n"
                    "    {}{}{}\n"
                    "    {}{}{}\n"
                    "    {}{}{}")
        return "    " + template.format(*self._color_list()).strip()