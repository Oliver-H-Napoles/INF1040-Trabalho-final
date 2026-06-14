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
    """UF litorânea presente no conjunto ('RS') -> 0 (êxito)."""
    with _mock_estados():
        assert valida_uf("RS") == 0


def test_valida_uf_ok_normaliza_espacos_e_minusculas():
    """UF com espaços e minúsculas ('  rj  ') é normalizada -> 0 (êxito)."""
    with _mock_estados():
        assert valida_uf("  rj  ") == 0


def test_valida_uf_erro_nao_string():
    """Entrada não-string (int/None) -> 1 (erro)."""
    assert valida_uf(42) == 1
    assert valida_uf(None) == 1


def test_valida_uf_erro_tamanho_diferente_de_dois():
    """UF com tamanho diferente de 2 ('R', 'RSP') -> 1 (erro)."""
    with _mock_estados():
        assert valida_uf("R") == 1
        assert valida_uf("RSP") == 1


def test_valida_uf_erro_caracteres_nao_alfabeticos():
    """UF com dígitos ou símbolos ('R1', '@!') -> 1 (erro)."""
    with _mock_estados():
        assert valida_uf("R1") == 1
        assert valida_uf("@!") == 1


def test_valida_uf_erro_uf_inexistente_no_conjunto():
    """UF válida em forma, mas ausente do conjunto ('ZZ') -> 1 (erro)."""
    with _mock_estados():
        assert valida_uf("ZZ") == 1


def test_valida_uf_erro_falha_ao_abrir_arquivo():
    """Falha ao abrir o estados.json -> 2 (erro)."""
    with patch("builtins.open", side_effect=OSError("arquivo ausente")):
        assert valida_uf("RS") == 2


# =============================================================================
# valida_elevacao
# =============================================================================

def test_valida_elevacao_ok_inteiro_positivo():
    """Elevação inteira positiva (10) -> 0 (êxito)."""
    assert valida_elevacao(10) == 0


def test_valida_elevacao_ok_zero():
    """Elevação igual a zero (0) -> 0 (êxito)."""
    assert valida_elevacao(0) == 0


def test_valida_elevacao_erro_inteiro_negativo():
    """Elevação inteira negativa (-1) -> 1 (erro)."""
    assert valida_elevacao(-1) == 1


def test_valida_elevacao_erro_nao_inteiro():
    """Elevação não-inteira (float/str/None) -> 2 (erro)."""
    assert valida_elevacao(3.5) == 2
    assert valida_elevacao("5") == 2
    assert valida_elevacao(None) == 2


# =============================================================================
# valida_raster
# =============================================================================

def test_valida_raster_ok_matriz_bidimensional():
    """Raster 2D válido (ndarray 3x4) -> 0 (êxito)."""
    assert valida_raster(np.zeros((3, 4))) == 0


def test_valida_raster_erro_none():
    """Raster None -> 1 (erro)."""
    assert valida_raster(None) == 1


def test_valida_raster_erro_sem_shape():
    """Objeto sem atributo 'shape' (lista) -> 1 (erro)."""
    assert valida_raster([[1, 2], [3, 4]]) == 1


def test_valida_raster_erro_dimensao_diferente_de_dois():
    """Raster 1D ou 3D (dimensão != 2) -> 2 (erro)."""
    assert valida_raster(np.zeros(5)) == 2          # 1D
    assert valida_raster(np.zeros((2, 2, 2))) == 2  # 3D


# =============================================================================
# valida_matrizes_tamanho
# =============================================================================

def test_valida_matrizes_tamanho_ok_mesmo_shape():
    """Duas matrizes de mesmo shape (3x3 e 3x3) -> 0 (êxito)."""
    assert valida_matrizes_tamanho(np.zeros((3, 3)), np.ones((3, 3))) == 0


def test_valida_matrizes_tamanho_erro_shapes_diferentes():
    """Matrizes de shapes diferentes (3x3 e 2x3) -> 1 (erro)."""
    assert valida_matrizes_tamanho(np.zeros((3, 3)), np.ones((2, 3))) == 1


def test_valida_matrizes_tamanho_erro_alguma_none():
    """Alguma das matrizes é None -> 2 (erro)."""
    assert valida_matrizes_tamanho(None, np.zeros((3, 3))) == 2
    assert valida_matrizes_tamanho(np.zeros((3, 3)), None) == 2


def test_valida_matrizes_tamanho_erro_sem_shape():
    """Alguma das matrizes não possui 'shape' (lista) -> 2 (erro)."""
    assert valida_matrizes_tamanho([[1, 2]], np.zeros((1, 2))) == 2
