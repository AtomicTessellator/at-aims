"""
@author Iker Hurtado, Sebastian Kokott (Original)

@overview This is a basic math library adapted to use NumPy and Pandas.
It maintains the functionality of the original JavaScript implementation.
"""
import numpy as np
import pandas as pd
from typing import List, Union, Callable, Optional


def add(p1: List[float], p2: List[float]) -> List[float]:
    """Adds two vectors and returns a new one"""
    return np.add(p1, p2).tolist()


def add_up(p1: List[float], p2: List[float]) -> List[float]:
    """Adds up a vector (the second parameter) to first one and returns it"""
    p1 += np.array(p2)
    return p1.tolist()


def subtract(p2: List[float], p1: List[float]) -> List[float]:
    """Subtracts the second vector from the first one and returns a new one"""
    return np.subtract(p2, p1).tolist()


def multiply_scalar(vector: List[float], scalar: float) -> List[float]:
    """Multiplies a vector by a scalar number and returns a new vector"""
    return (np.array(vector) * scalar).tolist()


def divide_scalar(vector: List[float], scalar: float) -> List[float]:
    """Divides a vector by a scalar number and returns a new vector"""
    return (np.array(vector) / scalar).tolist()


def get_distance(p1: List[float], p2: List[float]) -> float:
    """Returns the distance between two points"""
    return np.linalg.norm(np.subtract(p1, p2))


def norm(v: List[float]) -> float:
    """Returns vector length"""
    return np.linalg.norm(v)


def cdot(x: List[float], y: List[float]) -> float:
    """Returns dot product of two 3D vectors"""
    return np.dot(x, y)


def cross(a: List[float], b: List[float]) -> List[float]:
    """Returns cross product of two 3D vectors"""
    return np.cross(a, b).tolist()


def angle(x: List[float], y: List[float]) -> float:
    """Returns angle between two 3D vectors"""
    return np.arccos(np.clip(np.dot(x, y) / (norm(x) * norm(y)), -1.0, 1.0))


def normalize(v: List[float]) -> List[float]:
    """Normalizes 3D vector v"""
    return (np.array(v) / norm(v)).tolist()


def get_angle(p1: List[float], p2: List[float], p3: List[float]) -> float:
    """Returns the angle made up of three points"""
    p12v = subtract(p1, p2)
    p32v = subtract(p3, p2)
    return np.degrees(angle(p12v, p32v))


def get_torsion_angle(p0: List[float], p1: List[float], p2: List[float], p3: List[float]) -> float:
    """Returns the torsion angle comprised of four points using praxeolitic formula"""
    b0 = np.subtract(p0, p1)
    b1 = np.subtract(p2, p1)
    b2 = np.subtract(p3, p2)
    b1 = b1 / np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1) * b1
    w = b2 - np.dot(b2, b1) * b1
    x = np.dot(v, w)
    y = np.dot(np.cross(b1, v), w)
    return np.degrees(np.arctan2(y, x))


def minmax(mat: List[List[float]], axis: int, op: Callable[[np.ndarray], float]) -> List[float]:
    """Determines minimum or maximum of array along certain axis."""
    df = pd.DataFrame(mat)
    return df.apply(op, axis=axis).tolist()


def matrix_dot(A: List[List[float]], B: List[List[float]], C: Optional[List[List[float]]] = None) -> List[List[float]]:
    """Multiplies (dot) two matrices. C can be pre-allocated for performance."""
    if C is None:
        return np.dot(A, B).tolist()
    np.dot(A, B, out=C)
    return C


def tensor_dot(A: List[List[float]], B: List[float]) -> List[List[float]]:
    """Not yet full tensor dot. Accepts vector B and matrix A."""
    return np.tensordot(A, B, axes=0).reshape(-1, 3).tolist()


def get_dim(mat: Union[List[float], List[List[float]]]) -> List[int]:
    """Returns the dimensions of a 2D matrix. If flat, returns 0 as first dimension."""
    arr = np.array(mat)
    return [0, arr.size] if arr.ndim == 1 else list(arr.shape)


def add_arrays(arr1: List[float], arr2: List[float]) -> List[float]:
    """Adds the values of two arrays and returns them in a new array"""
    return np.add(arr1, arr2).tolist()


def determinant33(m: List[List[float]]) -> float:
    """Calculates the determinant of a 3x3 matrix"""
    return np.linalg.det(m)


def invert33(m: List[List[float]]) -> Union[List[List[float]], None]:
    """Inverts a 3x3 matrix"""
    try:
        return np.linalg.inv(m).tolist()
    except np.linalg.LinAlgError:
        print("invert33(m): det(m) == 0. m cannot be inverted!")
        return None


def multiply_m33v3(m: List[List[float]], v: List[float]) -> List[float]:
    """Multiplies a 3x3 matrix with a 3D vector"""
    return np.dot(m, v).tolist()


def transpose33(m: List[List[float]]) -> List[List[float]]:
    """Transposes a 3x3 matrix"""
    return np.array(m).T.tolist()


def solve33(m: List[List[float]], v: List[float]) -> List[float]:
    """Solves a 3x3 linear system"""
    return np.linalg.solve(m, v).tolist()
