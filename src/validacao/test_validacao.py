"""
Testes unitários do Módulo Validação.

Convenção de saídas validada por estes testes (funções validadoras → int):
    0 -> êxito (entrada válida)
    1 -> erro  (entrada inválida)

Mock: `valida_uf` lê `data/estados.json`. Para que o teste não dependa do
arquivo real nem do diretório de execução, o `open` é substituído por um
`mock_open` com um conteúdo JSON controlado.
"""
import builtins
from unittest.mock import mock_open, patch

import numpy as np
import pytest

from validacao.validacao import (
    valida_uf,
    valida_elevacao,
    valida_raster,
    valida_poligono,
    valida_matrizes_tamanho,
)

# JSON de estados litorâneos simulado (apenas as chaves importam para `valida_uf`).
ESTADOS_JSON = '{"RS": {}, "RJ": {}, "SP": {}}'


def _mock_estados(conteudo=ESTADOS_JSON):
    """Substitui o `open` usado por `valida_uf` por um arquivo JSON simulado."""
    return patch("builtins.open", mock_open(read_data=conteudo))


# =============================================================================
# valida_uf
# =============================================================================

def test_valida_uf_ok_uf_litoranea():
    with _mock_estados():
        assert valida_uf("RS") == 0


def test_valida_uf_ok_normaliza_espacos_e_minusculas():
    with _mock_estados():
        assert valida_uf("  rj  ") == 0


def test_valida_uf_erro_nao_string():
    assert valida_uf(42) == 1
    assert valida_uf(None) == 1


def test_valida_uf_erro_tamanho_diferente_de_dois():
    with _mock_estados():
        assert valida_uf("R") == 1
        assert valida_uf("RSP") == 1


def test_valida_uf_erro_caracteres_nao_alfabeticos():
    with _mock_estados():
        assert valida_uf("R1") == 1
        assert valida_uf("@!") == 1


def test_valida_uf_erro_uf_inexistente_no_conjunto():
    with _mock_estados():
        assert valida_uf("ZZ") == 1


def test_valida_uf_erro_falha_ao_abrir_arquivo():
    with patch("builtins.open", side_effect=OSError("arquivo ausente")):
        assert valida_uf("RS") == 1


# =============================================================================
# valida_elevacao
# =============================================================================

def test_valida_elevacao_ok_inteiro_positivo():
    assert valida_elevacao(10) == 0


def test_valida_elevacao_ok_zero():
    assert valida_elevacao(0) == 0


def test_valida_elevacao_erro_inteiro_negativo():
    assert valida_elevacao(-1) == 1


def test_valida_elevacao_erro_nao_inteiro():
    assert valida_elevacao(3.5) == 1
    assert valida_elevacao("5") == 1
    assert valida_elevacao(None) == 1


# =============================================================================
# valida_raster
# =============================================================================

def test_valida_raster_ok_matriz_bidimensional():
    assert valida_raster(np.zeros((3, 4))) == 0


def test_valida_raster_erro_none():
    assert valida_raster(None) == 1


def test_valida_raster_erro_sem_shape():
    assert valida_raster([[1, 2], [3, 4]]) == 1


def test_valida_raster_erro_dimensao_diferente_de_dois():
    assert valida_raster(np.zeros(5)) == 1          # 1D
    assert valida_raster(np.zeros((2, 2, 2))) == 1  # 3D


# =============================================================================
# valida_poligono
# =============================================================================

class _PoligonoFake:
    def __init__(self, geo_interface):
        self.__geo_interface__ = geo_interface


def test_valida_poligono_ok_geo_interface_valida():
    poligono = _PoligonoFake({"type": "Polygon", "coordinates": []})
    assert valida_poligono(poligono) == 0


def test_valida_poligono_erro_none():
    assert valida_poligono(None) == 1


def test_valida_poligono_erro_sem_geo_interface():
    assert valida_poligono(object()) == 1


def test_valida_poligono_erro_geo_interface_nao_dict():
    assert valida_poligono(_PoligonoFake("nao_dict")) == 1


def test_valida_poligono_erro_geo_interface_sem_type():
    assert valida_poligono(_PoligonoFake({"coordinates": []})) == 1


# =============================================================================
# valida_matrizes_tamanho
# =============================================================================

def test_valida_matrizes_tamanho_ok_mesmo_shape():
    assert valida_matrizes_tamanho(np.zeros((3, 3)), np.ones((3, 3))) == 0


def test_valida_matrizes_tamanho_erro_shapes_diferentes():
    assert valida_matrizes_tamanho(np.zeros((3, 3)), np.ones((2, 3))) == 1


def test_valida_matrizes_tamanho_erro_alguma_none():
    assert valida_matrizes_tamanho(None, np.zeros((3, 3))) == 1
    assert valida_matrizes_tamanho(np.zeros((3, 3)), None) == 1


def test_valida_matrizes_tamanho_erro_sem_shape():
    assert valida_matrizes_tamanho([[1, 2]], np.zeros((1, 2))) == 1
