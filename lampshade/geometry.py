import math
from typing import List, Tuple

import numpy as np
import trimesh

from .params import Params
from .utils import lerp


def quadratic_profile(u: float, P: Params) -> float:
    """
    Radial profile as a function of height parameter u in [0, 1].
    Interpolation modes:
      0: Quadratic Bezier
      1: Quadratic Lagrange
      2: Piecewise Linear (via middle)
    All return radius.
    """
    if P.interpolation == 1:
        # Lagrange (three points at u=0,0.5,1)
        return (
            2 * (u - 1) * (u - 0.5) * (P.topDiameter / 2.0)
            - 4 * (u - 1) * u * (P.middleDiameter / 2.0)
            + 2 * u * (u - 0.5) * (P.bottomDiameter / 2.0)
        )
    elif P.interpolation == 2:
        # Linear between top-middle, then middle-bottom
        if u <= 0.5:
            t = u / 0.5
            return lerp(P.topDiameter / 2.0, P.middleDiameter / 2.0, t)
        else:
            t = (u - 0.5) / 0.5
            return lerp(P.middleDiameter / 2.0, P.bottomDiameter / 2.0, t)
    else:
        # Quadratic Bezier
        t = u
        return (
            (1 - t) * (1 - t) * (P.topDiameter / 2.0)
            + 2 * (1 - t) * t * (P.middleDiameter / 2.0)
            + t * t * (P.bottomDiameter / 2.0)
        )


def design_offset(u: float, v: float, P: Params) -> float:
    """
    Procedural radial offset (patterns). u in [0,1] along height, v in [0,2π) around.
    Mode 0 disables patterns.
    """
    if P.designMode <= 0:
        return 0.0

    fd = P.featureDepth
    fc = float(P.featureCount)
    m = P.designMode

    # The patterns below control how the radius is modulated across the surface.
    # They stay bounded by featureDepth and depend on fc (repeat count).
    if m == 1:
        return fd * math.sin(fc * math.pi * u) * math.cos(fc * v)
    elif m == 2:
        return fd * math.sin(fc * (v + math.pi * u))
    elif m == 3:
        return fd * abs(math.sin(fc * v))
    elif m == 4:
        return fd * (abs(math.sin(fc * math.pi * u)) + abs(math.sin(fc * v)))
    elif m == 5:
        return fd * math.sin(fc * (v + u)) * math.sin(fc * (v - u))
    elif m == 6:
        return fd * math.sin(fc * (v + 0.5 * math.sin(2 * math.pi * u)))
    elif m == 7:
        return fd * (abs(math.sin(fc * v)) - abs(math.sin(fc * math.pi * u)))
    elif m == 8:
        return fd * 0.5 * (math.sin(fc * v) + math.sin((fc + 1.0) * v + 2 * math.pi * u))
    elif m == 9:
        return fd * 0.7 * math.cos(fc * 2 * math.pi * u)
    elif m == 10:
        phase = fc * u
        # Triangle wave in u
        return fd * 0.8 * abs(2.0 * (phase - math.floor(phase + 0.5)))
    elif m == 11:
        return fd * 0.9 * abs(math.sin(fc * math.pi * u + v))
    elif m == 12:
        d = math.cos(fc * 2 * math.pi * u + 2.0 * v) + 0.7 * math.sin(fc * v + u * 2.7)
        return fd * 0.5 * d
    else:
        return 0.0


def compute_outer_vertex(u: float, v: float, P: Params) -> np.ndarray:
    """
    Compute vertex on the outer surface:
      - u in [0,1]: 0 = top rim, 1 = bottom rim
      - v in [0,2π): azimuth
    Coordinate system for the viewer: Y up, X right, Z forward.
    """
    baseR = quadratic_profile(u, P)
    offset = design_offset(u, v, P)
    r = max(0.0, baseR + offset)
    x = r * math.cos(v)
    z = r * math.sin(v)
    y = lerp(P.cylinderHeight / 2.0, -P.cylinderHeight / 2.0, u)
    return np.array([x, y, z], dtype=np.float64)


def build_mesh_arrays(P: Params) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns (vertices (N,3), faces (M,3)) in viewer coordinates (Y up).
    Mesh consists of:
      1) Main lampshade outer surface
      1b) Bottom cap
      2) Transition surface (from top rim to mount radius)
      3) Mount cylinder outer surface + top cap

    Note: This generator uses a grid with 'detail' subdivisions in both u (height) and v (angle)
    to ensure consistent triangulation and pattern sampling.
    """
    P.update_transition()
    P.update_feature_depth_max()

    vertices: List[np.ndarray] = []
    faces: List[Tuple[int, int, int]] = []

    def add_vertex(p: np.ndarray) -> int:
        vertices.append(p)
        return len(vertices) - 1

    def add_tri(a: int, b: int, c: int) -> None:
        faces.append((a, b, c))

    detail = int(P.detail)
    def v_at(j, n): return (float(j) / float(n)) * (2.0 * math.pi)

    # 1) Main outer surface quilt
    for i in range(detail):
        u1 = float(i) / float(detail)
        u2 = float(i + 1) / float(detail)
        for j in range(detail):
            v1 = v_at(j, detail)
            v2 = v_at(j + 1, detail)
            p1 = add_vertex(compute_outer_vertex(u1, v1, P))
            p2 = add_vertex(compute_outer_vertex(u2, v1, P))
            p3 = add_vertex(compute_outer_vertex(u2, v2, P))
            p4 = add_vertex(compute_outer_vertex(u1, v2, P))
            add_tri(p1, p2, p3)
            add_tri(p1, p3, p4)

    # 1b) Bottom cap (flat fan)
    center_bottom = add_vertex(np.array([0.0, -P.cylinderHeight / 2.0, 0.0], dtype=np.float64))
    for j in range(detail):
        v1 = v_at(j, detail)
        v2 = v_at(j + 1, detail)
        p1 = add_vertex(compute_outer_vertex(1.0, v1, P))
        p2 = add_vertex(compute_outer_vertex(1.0, v2, P))
        add_tri(center_bottom, p1, p2)

    # 2) Transition from top rim to mount radius
    transBottomY = P.cylinderHeight / 2.0
    transTopY = transBottomY + P.transitionHeight
    topR = P.mountCylinderOuterDiameter / 2.0

    for i in range(detail):
        t1 = float(i) / float(detail)
        t2 = float(i + 1) / float(detail)
        y1 = lerp(transBottomY, transTopY, t1)
        y2 = lerp(transBottomY, transTopY, t2)
        for j in range(detail):
            a1 = v_at(j, detail)
            a2 = v_at(j + 1, detail)

            # Bottom samples on the decorated top rim, top samples at mount radius
            bottomV1 = compute_outer_vertex(0.0, a1, P)
            bottomV2 = compute_outer_vertex(0.0, a2, P)
            topV1 = np.array([topR * math.cos(a1), transTopY, topR * math.sin(a1)], dtype=np.float64)
            topV2 = np.array([topR * math.cos(a2), transTopY, topR * math.sin(a2)], dtype=np.float64)

            # Linear blend along the transition height
            x1 = lerp(bottomV1[0], topV1[0], t1); z1 = lerp(bottomV1[2], topV1[2], t1)
            x2 = lerp(bottomV1[0], topV1[0], t2); z2 = lerp(bottomV1[2], topV1[2], t2)
            x3 = lerp(bottomV2[0], topV2[0], t2); z3 = lerp(bottomV2[2], topV2[2], t2)
            x4 = lerp(bottomV2[0], topV2[0], t1); z4 = lerp(bottomV2[2], topV2[2], t1)

            P1 = add_vertex(np.array([x1, y1, z1], dtype=np.float64))
            P2 = add_vertex(np.array([x2, y2, z2], dtype=np.float64))
            P3 = add_vertex(np.array([x3, y2, z3], dtype=np.float64))
            P4 = add_vertex(np.array([x4, y1, z4], dtype=np.float64))
            add_tri(P1, P2, P3)
            add_tri(P1, P3, P4)

    # 3) Mount cylinder: side + top cap
    cylBottomY = P.cylinderHeight / 2.0 + P.transitionHeight
    cylTopY = cylBottomY + P.mountCylinderHeight
    r_out = P.mountCylinderOuterDiameter / 2.0

    # Side wall
    for i in range(detail):
        a1 = v_at(i, detail)
        a2 = v_at(i + 1, detail)
        p1 = add_vertex(np.array([r_out * math.cos(a1), cylBottomY, r_out * math.sin(a1)], dtype=np.float64))
        p2 = add_vertex(np.array([r_out * math.cos(a1), cylTopY,    r_out * math.sin(a1)], dtype=np.float64))
        p3 = add_vertex(np.array([r_out * math.cos(a2), cylTopY,    r_out * math.sin(a2)], dtype=np.float64))
        p4 = add_vertex(np.array([r_out * math.cos(a2), cylBottomY, r_out * math.sin(a2)], dtype=np.float64))
        add_tri(p1, p2, p3)
        add_tri(p1, p3, p4)

    # Top cap
    center_top = add_vertex(np.array([0.0, cylTopY, 0.0], dtype=np.float64))
    for j in range(detail):
        a1 = v_at(j, detail)
        a2 = v_at(j + 1, detail)
        p1 = add_vertex(np.array([r_out * math.cos(a1), cylTopY, r_out * math.sin(a1)], dtype=np.float64))
        p2 = add_vertex(np.array([r_out * math.cos(a2), cylTopY, r_out * math.sin(a2)], dtype=np.float64))
        add_tri(center_top, p2, p1)

    V = np.vstack(vertices) if vertices else np.zeros((0, 3))
    F = np.array(faces, dtype=np.int64) if faces else np.zeros((0, 3), dtype=np.int64)
    return V, F


def build_trimesh_for_export(P: Params) -> trimesh.Trimesh:
    """
    Build a Trimesh for STL export. Reorders coordinates to (x, z, y)
    to match the original export convention (Z up in the STL).
    """
    V, F = build_mesh_arrays(P)
    Vexp = np.stack([V[:, 0], V[:, 2], V[:, 1]], axis=1)
    mesh = trimesh.Trimesh(vertices=Vexp, faces=F, process=False)
    mesh.remove_degenerate_faces()
    mesh.remove_unreferenced_vertices()
    mesh.rezero()
    return mesh