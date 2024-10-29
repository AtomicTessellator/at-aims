import numpy as np
from ataims import mathlib


def test_add():
    v1 = [1.0, 2.0, 3.0]
    v2 = [4.0, 5.0, 6.0]
    assert mathlib.add(v1, v2) == [5.0, 7.0, 9.0]


def test_subtract():
    v1 = [4.0, 5.0, 6.0]
    v2 = [1.0, 2.0, 3.0]
    assert mathlib.subtract(v1, v2) == [3.0, 3.0, 3.0]


def test_multiply_scalar():
    v = [1.0, 2.0, 3.0]
    scalar = 2.0
    assert mathlib.multiply_scalar(v, scalar) == [2.0, 4.0, 6.0]


def test_divide_scalar():
    v = [2.0, 4.0, 6.0]
    scalar = 2.0
    assert mathlib.divide_scalar(v, scalar) == [1.0, 2.0, 3.0]


def test_get_distance():
    p1 = [0.0, 0.0, 0.0]
    p2 = [3.0, 4.0, 0.0]
    assert mathlib.get_distance(p1, p2) == 5.0


def test_norm():
    v = [3.0, 4.0, 0.0]
    assert mathlib.norm(v) == 5.0


def test_dot_product():
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    assert mathlib.cdot(v1, v2) == 0.0


def test_cross_product():
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    assert mathlib.cross(v1, v2) == [0.0, 0.0, 1.0]


def test_angle():
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    assert abs(mathlib.angle(v1, v2) - np.pi/2) < 1e-10


def test_normalize():
    v = [3.0, 0.0, 0.0]
    assert mathlib.normalize(v) == [1.0, 0.0, 0.0]


def test_get_angle():
    p1 = [1.0, 0.0, 0.0]
    p2 = [0.0, 0.0, 0.0]
    p3 = [0.0, 1.0, 0.0]
    assert abs(mathlib.get_angle(p1, p2, p3) - 90.0) < 1e-10


def test_get_torsion_angle():
    p0 = [1.0, 0.0, 0.0]
    p1 = [0.0, 0.0, 0.0]
    p2 = [0.0, 1.0, 0.0]
    p3 = [0.0, 1.0, 1.0]
    assert isinstance(mathlib.get_torsion_angle(p0, p1, p2, p3), float)


def test_minmax():
    mat = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    assert mathlib.minmax(mat, 0, np.min) == [1.0, 2.0, 3.0]
    assert mathlib.minmax(mat, 0, np.max) == [4.0, 5.0, 6.0]


def test_matrix_dot():
    A = [[1.0, 0.0], [0.0, 1.0]]
    B = [[2.0, 0.0], [0.0, 2.0]]
    assert mathlib.matrix_dot(A, B) == [[2.0, 0.0], [0.0, 2.0]]


def test_tensor_dot():
    A = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    B = [2.0, 0.0, 0.0]
    result = mathlib.tensor_dot(A, B)
    assert len(result) == 6 and len(result[0]) == 3
    assert result[0] == [2.0, 0.0, 0.0]
    assert all(len(row) == 3 for row in result)


def test_get_dim():
    mat = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    vec = [1.0, 2.0, 3.0]
    assert mathlib.get_dim(mat) == [2, 3]
    assert mathlib.get_dim(vec) == [0, 3]

def test_determinant33():
    m = [[1.0, 0.0, 0.0],
         [0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0]]
    assert mathlib.determinant33(m) == 1.0


def test_invert33():
    m = [[1.0, 0.0, 0.0],
         [0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0]]
    assert mathlib.invert33(m) == m
    
    # Test singular matrix
    m_singular = [[1.0, 1.0, 1.0],
                  [1.0, 1.0, 1.0],
                  [1.0, 1.0, 1.0]]
    assert mathlib.invert33(m_singular) is None


def test_multiply_m33v3():
    m = [[1.0, 0.0, 0.0],
         [0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0]]
    v = [1.0, 2.0, 3.0]
    assert mathlib.multiply_m33v3(m, v) == v

def test_transpose33():
    m = [[1.0, 2.0, 3.0],
         [4.0, 5.0, 6.0],
         [7.0, 8.0, 9.0]]
    expected = [[1.0, 4.0, 7.0],
                [2.0, 5.0, 8.0],
                [3.0, 6.0, 9.0]]
    assert mathlib.transpose33(m) == expected


def test_solve33():
    m = [[1.0, 0.0, 0.0],
         [0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0]]
    v = [1.0, 2.0, 3.0]
    assert mathlib.solve33(m, v) == v
