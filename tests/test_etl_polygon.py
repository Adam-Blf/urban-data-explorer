"""Tests pour l'algorithme ray-casting _point_in_polygon (fix bug #5)."""

from __future__ import annotations

import pytest
from etl.silver.processing import _point_in_polygon

# Carré unitaire [0,0]-[1,0]-[1,1]-[0,1]
SQUARE = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]

# Triangle simple
TRIANGLE = [[0.0, 0.0], [2.0, 0.0], [1.0, 2.0]]


# ── Tests de base ────────────────────────────────────────────────────────────

def test_point_inside_square():
    assert _point_in_polygon(0.5, 0.5, SQUARE) is True


def test_point_outside_square_right():
    assert _point_in_polygon(2.0, 0.5, SQUARE) is False


def test_point_outside_square_above():
    assert _point_in_polygon(0.5, 2.0, SQUARE) is False


def test_point_outside_square_below():
    assert _point_in_polygon(0.5, -1.0, SQUARE) is False


def test_degenerate_polygon_two_points():
    """Un polygone avec moins de 3 sommets retourne False."""
    assert _point_in_polygon(0.5, 0.5, [[0.0, 0.0], [1.0, 0.0]]) is False


def test_degenerate_polygon_empty():
    assert _point_in_polygon(0.5, 0.5, []) is False


def test_triangle_inside():
    assert _point_in_polygon(1.0, 0.5, TRIANGLE) is True


def test_triangle_outside():
    assert _point_in_polygon(0.1, 1.8, TRIANGLE) is False


# ── Fix bug #5 : p1y == p2y ne doit pas lever NameError sur xints ────────────

def test_horizontal_edge_no_nameerror():
    """Fix #5 : un bord horizontal ne doit jamais provoquer NameError sur xints."""
    # Le carré SQUARE a deux bords horizontaux : bottom (y=0) et top (y=1).
    # Test avec un point ayant lat = 0.0 (sur le bord horizontal inférieur).
    try:
        result = _point_in_polygon(0.5, 0.0, SQUARE)
        assert isinstance(result, bool)
    except NameError as exc:
        pytest.fail(f"Bug #5 non corrigé : {exc}")


def test_horizontal_edge_lat_equals_edge():
    """Point avec lat exactement sur un bord horizontal – pas d'erreur."""
    poly = [[0.0, 1.0], [2.0, 1.0], [2.0, 3.0], [0.0, 3.0]]  # rectangle, bord bas y=1
    try:
        result = _point_in_polygon(1.0, 1.0, poly)
        assert isinstance(result, bool)
    except NameError as exc:
        pytest.fail(f"Bug #5 non corrigé : {exc}")


def test_polygon_with_only_horizontal_edges():
    """Polygone artificiellement dégénéré avec tous les y identiques → pas d'erreur."""
    # Segment horizontal (tous y=0), cas limite extrême
    flat = [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]]
    try:
        result = _point_in_polygon(1.0, 0.0, flat)
        assert isinstance(result, bool)
    except NameError as exc:
        pytest.fail(f"Bug #5 non corrigé : {exc}")


def test_xints_not_stale_across_iterations():
    """Vérifie que xints d'une itération précédente n'est pas réutilisé incorrectement.

    Polygone conçu pour qu'une itération calcule xints puis que la suivante
    ait un bord horizontal et ne doive PAS réutiliser la valeur précédente.
    """
    # Hexagone avec deux bords horizontaux intentionnels
    hexagon = [
        [0.0, 0.0],
        [2.0, 0.0],   # bord horizontal
        [3.0, 1.0],
        [2.0, 2.0],
        [0.0, 2.0],   # bord horizontal
        [-1.0, 1.0],
    ]
    try:
        result = _point_in_polygon(1.0, 1.0, hexagon)
        assert result is True
    except NameError as exc:
        pytest.fail(f"Bug #5 non corrigé : {exc}")
