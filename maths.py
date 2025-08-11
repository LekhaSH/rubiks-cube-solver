class Point:
    """A 3D point/vector used by the Rubik's cube implementation."""

    def __init__(self, x, y=None, z=None):
        """Construct a Point from an (x, y, z) tuple or an iterable.

        The constructor accepts either three scalars or any iterable with
        three values.  Each coordinate must not be ``None``.
        """
        try:
            # convert from an iterable
            ii = iter(x)
            self.x = next(ii)
            self.y = next(ii)
            self.z = next(ii)
        except TypeError:
            # not iterable
            self.x = x
            self.y = y
            self.z = z
        if any(val is None for val in self):
            raise ValueError(f"Point does not allow None values: {self}")

    def __str__(self):
        return str(tuple(self))

    def __repr__(self):
        return "Point" + str(self)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        return Point(self.x * other, self.y * other, self.z * other)

    def dot(self, other):
        """Return the dot product of this point with another point."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        """Return the cross product of this point with another point."""
        return Point(self.y * other.z - self.z * other.y,
                     self.z * other.x - self.x * other.z,
                     self.x * other.y - self.y * other.x)

    def __getitem__(self, item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        elif item == 2:
            return self.z
        raise IndexError("Point index out of range")

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def count(self, val):
        return int(self.x == val) + int(self.y == val) + int(self.z == val)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __eq__(self, other):
        if isinstance(other, (tuple, list)):
            return self.x == other[0] and self.y == other[1] and self.z == other[2]
        return (isinstance(other, self.__class__) and self.x == other.x
                and self.y == other.y and self.z == other.z)

    def __ne__(self, other):
        return not (self == other)


class Matrix:
    """A simple 3×3 matrix supporting multiplication with points and other matrices."""

    def __init__(self, *args):
        """Construct a Matrix from nine values.

        Accepts nine positional values, a flat iterable, or a nested list.  A
        ValueError is raised if nine values are not supplied.
        """
        if len(args) == 9:
            self.vals = list(args)
        elif len(args) == 3:
            try:
                self.vals = [x for y in args for x in y]
            except Exception:
                self.vals = []
        else:
            self.__init__(*args[0])

        if len(self.vals) != 9:
            raise ValueError(f"Matrix requires 9 items, got {args}")

    def __str__(self):
        return ("[{}, {}, {},\n"
                " {}, {}, {},\n"
                " {}, {}, {}]".format(*self.vals))

    def __repr__(self):
        return ("Matrix({}, {}, {},\n"
                "       {}, {}, {},\n"
                "       {}, {}, {})".format(*self.vals))

    def __eq__(self, other):
        return self.vals == other.vals

    def __add__(self, other):
        return Matrix(a + b for a, b in zip(self.vals, other.vals))

    def __sub__(self, other):
        return Matrix(a - b for a, b in zip(self.vals, other.vals))

    def __iadd__(self, other):
        self.vals = [a + b for a, b in zip(self.vals, other.vals)]
        return self

    def __isub__(self, other):
        self.vals = [a - b for a, b in zip(self.vals, other.vals)]
        return self

    def __mul__(self, other):
        """Do matrix–matrix or matrix–point multiplication."""
        if isinstance(other, Point):
            # Multiply a matrix by a point
            return Point(other.dot(Point(row)) for row in self.rows())
        elif isinstance(other, Matrix):
            # Multiply a matrix by another matrix
            return Matrix(Point(row).dot(Point(col))
                          for row in self.rows() for col in other.cols())
        else:
            raise TypeError(f"Unsupported multiplication with type {type(other)}")

    def rows(self):
        yield self.vals[0:3]
        yield self.vals[3:6]
        yield self.vals[6:9]

    def cols(self):
        yield self.vals[0:9:3]
        yield self.vals[1:9:3]
        yield self.vals[2:9:3]