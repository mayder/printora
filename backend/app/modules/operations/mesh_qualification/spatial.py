from __future__ import annotations

import math


Vector = tuple[float, float, float]
Face = tuple[int, int, int]
MAX_INTERSECTION_CANDIDATES = 200_000
MAX_THICKNESS_RAYS = 500
MAX_THICKNESS_CANDIDATES = 300_000


def count_self_intersections(vertices: list[Vector], faces: list[Face], tolerance: float) -> int | None:
    bounds = [_bounds(tuple(vertices[index] for index in face)) for face in faces]
    ordered = sorted(range(len(faces)), key=lambda index: bounds[index][0][0])
    active: list[int] = []
    candidates = 0
    intersections = 0
    for right_index in ordered:
        right_min, right_max = bounds[right_index]
        active = [index for index in active if bounds[index][1][0] + tolerance >= right_min[0]]
        for left_index in active:
            if set(faces[left_index]).intersection(faces[right_index]):
                continue
            candidates += 1
            if candidates > MAX_INTERSECTION_CANDIDATES:
                return None
            left_min, left_max = bounds[left_index]
            if _bounds_overlap(left_min, left_max, right_min, right_max, tolerance):
                left = tuple(vertices[index] for index in faces[left_index])
                right = tuple(vertices[index] for index in faces[right_index])
                intersections += int(_triangles_overlap(left, right, tolerance))
        active.append(right_index)
    return intersections


def estimate_minimum_thickness(
    vertices: list[Vector],
    faces: list[Face],
    tolerance: float,
    signed_volume: float,
) -> float | None:
    if not faces:
        return None
    step = max(1, math.ceil(len(faces) / MAX_THICKNESS_RAYS))
    candidates = 0
    minimum: float | None = None
    orientation = -1.0 if signed_volume >= 0 else 1.0
    for face_index in range(0, len(faces), step):
        face = faces[face_index]
        triangle = tuple(vertices[index] for index in face)
        normal = _unit(_cross(_subtract(triangle[1], triangle[0]), _subtract(triangle[2], triangle[0])))
        if normal is None:
            continue
        direction = _scale(normal, orientation)
        center = tuple(sum(point[axis] for point in triangle) / 3 for axis in range(3))
        origin = _add(center, _scale(direction, tolerance * 10))
        for target_index, target in enumerate(faces):
            if target_index == face_index:
                continue
            candidates += 1
            if candidates > MAX_THICKNESS_CANDIDATES:
                return None
            distance = _ray_triangle(origin, direction, tuple(vertices[index] for index in target), tolerance)
            if distance is not None and (minimum is None or distance < minimum):
                minimum = distance
    return minimum


def _triangles_overlap(left: tuple[Vector, Vector, Vector], right: tuple[Vector, Vector, Vector], tolerance: float) -> bool:
    left_edges = _edges(left)
    right_edges = _edges(right)
    left_normal = _cross(left_edges[0], left_edges[1])
    right_normal = _cross(right_edges[0], right_edges[1])
    axes = [left_normal, right_normal]
    axes.extend(_cross(left_edge, right_edge) for left_edge in left_edges for right_edge in right_edges)
    axes.extend(_cross(left_normal, edge) for edge in (*left_edges, *right_edges))
    for axis in axes:
        magnitude = math.sqrt(_dot(axis, axis))
        if magnitude <= tolerance:
            continue
        normalized = _scale(axis, 1 / magnitude)
        left_projection = [_dot(point, normalized) for point in left]
        right_projection = [_dot(point, normalized) for point in right]
        if max(left_projection) < min(right_projection) - tolerance:
            return False
        if max(right_projection) < min(left_projection) - tolerance:
            return False
    return True


def _ray_triangle(origin: Vector, direction: Vector, triangle: tuple[Vector, Vector, Vector], tolerance: float) -> float | None:
    edge_one = _subtract(triangle[1], triangle[0])
    edge_two = _subtract(triangle[2], triangle[0])
    perpendicular = _cross(direction, edge_two)
    determinant = _dot(edge_one, perpendicular)
    if abs(determinant) <= tolerance:
        return None
    inverse = 1.0 / determinant
    distance_to_vertex = _subtract(origin, triangle[0])
    u = inverse * _dot(distance_to_vertex, perpendicular)
    if u < -tolerance or u > 1 + tolerance:
        return None
    q = _cross(distance_to_vertex, edge_one)
    v = inverse * _dot(direction, q)
    if v < -tolerance or u + v > 1 + tolerance:
        return None
    distance = inverse * _dot(edge_two, q)
    return distance if distance > tolerance else None


def _bounds(triangle: tuple[Vector, Vector, Vector]) -> tuple[Vector, Vector]:
    return (
        tuple(min(point[axis] for point in triangle) for axis in range(3)),
        tuple(max(point[axis] for point in triangle) for axis in range(3)),
    )  # type: ignore[return-value]


def _bounds_overlap(left_min: Vector, left_max: Vector, right_min: Vector, right_max: Vector, tolerance: float) -> bool:
    return all(left_max[axis] + tolerance >= right_min[axis] and right_max[axis] + tolerance >= left_min[axis] for axis in range(3))


def _edges(triangle: tuple[Vector, Vector, Vector]) -> tuple[Vector, Vector, Vector]:
    return (
        _subtract(triangle[1], triangle[0]),
        _subtract(triangle[2], triangle[0]),
        _subtract(triangle[2], triangle[1]),
    )


def _subtract(left: Vector, right: Vector) -> Vector:
    return left[0] - right[0], left[1] - right[1], left[2] - right[2]


def _add(left: Vector, right: Vector) -> Vector:
    return left[0] + right[0], left[1] + right[1], left[2] + right[2]


def _scale(vector: Vector, factor: float) -> Vector:
    return vector[0] * factor, vector[1] * factor, vector[2] * factor


def _dot(left: Vector, right: Vector) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def _cross(left: Vector, right: Vector) -> Vector:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _unit(vector: Vector) -> Vector | None:
    magnitude = math.sqrt(_dot(vector, vector))
    return _scale(vector, 1 / magnitude) if magnitude else None
