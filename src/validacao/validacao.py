import json
from typing import Any


def valida_uf(uf: str) -> int:
    """Valida se a UF é uma sigla de estado litorâneo disponível no conjunto de dados."""
    if not isinstance(uf, str):
        return 1

    uf_formatada = uf.strip().upper()
    if len(uf_formatada) != 2 or not uf_formatada.isalpha():
        return 1

    try:
        with open('data/estados.json', 'r', encoding='utf-8') as arquivo:
            estados = json.load(arquivo)
    except Exception:
        return 1

    return 0 if uf_formatada in estados else 1


def valida_elevacao(metros: int) -> int:
    """Valida se a elevação é um inteiro não-negativo."""
    if not isinstance(metros, int):
        return 1

    return 0 if metros >= 0 else 1


def valida_raster(raster: Any) -> int:
    """Valida se o raster é uma matriz bidimensional válida."""
    if raster is None:
        return 1

    if not hasattr(raster, 'shape'):
        return 1

    if len(getattr(raster, 'shape')) != 2:
        return 1

    return 0


def valida_poligono(poligono: Any) -> int:
    """Valida se o polígono tem uma interface geo-spacial válida."""
    if poligono is None:
        return 1

    if not hasattr(poligono, '__geo_interface__'):
        return 1

    geo_interface = getattr(poligono, '__geo_interface__')
    if not isinstance(geo_interface, dict) or 'type' not in geo_interface:
        return 1

    return 0


def valida_matrizes_tamanho(matriz1: Any, matriz2: Any) -> int:
    """Valida se duas matrizes possuem o mesmo tamanho."""
    if matriz1 is None or matriz2 is None:
        return 1

    if not hasattr(matriz1, 'shape') or not hasattr(matriz2, 'shape'):
        return 1

    return 0 if getattr(matriz1, 'shape') == getattr(matriz2, 'shape') else 1

