"""
Testes unitários do Módulo Água.

Convenção de saídas validada por estes testes:
    - cria_mascara_agua / expandir_mascara_agua / acha_nascente (produtoras):
        retornam o objeto/valor em caso de êxito e `None` em caso de erro.
    - carrega_dados (ação):
        0 -> êxito; 1 -> sem máscara/nascente; 2 -> erro de leitura/processamento.

Mock: `carrega_dados` lê um arquivo JSON do disco. O `open`/`load` é substituído
para que o teste não dependa de nenhum arquivo real.
"""
from unittest.mock import mock_open, patch

import numpy as np
import pytest

from agua import cria_mascara_agua, expandir_mascara_agua, carrega_dados
from agua.agua import acha_nascente, _dados


@pytest.fixture(autouse=True)
def reset_estado_modulo():
    """Reseta o estado encapsulado do módulo antes de cada teste."""
    _dados["mascara"] = None
    _dados["nascente"] = 0
    yield


# =============================================================================
# cria_mascara_agua  (produtora -> ndarray | None)
# =============================================================================

def test_cria_mascara_ok_canto_superior_esquerdo():
    esperado = np.array([[1, 0], [0, 0], [0, 0]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 0), esperado)


def test_cria_mascara_ok_canto_superior_direito():
    esperado = np.array([[0, 1], [0, 0], [0, 0]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 1), esperado)


def test_cria_mascara_ok_canto_inferior_direito():
    esperado = np.array([[0, 0], [0, 0], [0, 1]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 2), esperado)


def test_cria_mascara_ok_canto_inferior_esquerdo():
    esperado = np.array([[0, 0], [0, 0], [1, 0]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 3), esperado)


def test_cria_mascara_ok_dimensoes_maiores():
    esperado = np.array(
        [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 1]], dtype=float
    )
    assert np.array_equal(cria_mascara_agua(4, 3, 2), esperado)


@pytest.mark.parametrize("tam_x, tam_y", [(-1, 0), (0, 0), (10, -2), (0, 5)])
def test_cria_mascara_erro_tamanho_invalido(tam_x, tam_y):
    assert cria_mascara_agua(tam_x, tam_y, 0) is None


@pytest.mark.parametrize("xy_fonte", [-1, 4, 5, 100])
def test_cria_mascara_erro_fonte_invalida(xy_fonte):
    assert cria_mascara_agua(10, 10, xy_fonte) is None


# =============================================================================
# expandir_mascara_agua  (produtora -> int | None)
# =============================================================================

def test_expandir_ok_inundacao_parcial():
    terreno = np.array([[5, 3, 2], [10, 2, 0], [1, 0, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3) == 7


def test_expandir_ok_inundacao_minima():
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3) == 1


def test_expandir_ok_terreno_decimal():
    terreno = np.array(
        [[5, 4, 5.3], [3, 2.5, 1], [2.6, 1.1, 0.9], [2.3, 3.2, 0]], dtype=float
    )
    masc = cria_mascara_agua(4, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3.0) == 8


def test_expandir_erro_nivel_do_mar_nulo():
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 0) is None


def test_expandir_erro_nivel_do_mar_negativo():
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, -2) is None


def test_expandir_erro_tamanhos_incompativeis_mascara_menor():
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(2, 2, 2)
    assert expandir_mascara_agua(terreno, masc, 3) is None


def test_expandir_erro_tamanhos_incompativeis_terreno_maior():
    terreno = np.array(
        [[5, 1, 2, 3], [1, 4, 10, 3], [1, 10, 0, 3]], dtype=float
    )
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3) is None


def test_expandir_erro_mascara_diferente_da_armazenada():
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    cria_mascara_agua(3, 3, 2)  # define a máscara armazenada no módulo
    # Máscara de mesmo tamanho, mas que não corresponde à armazenada.
    masc_estranha = np.zeros((3, 3), dtype=float)
    assert expandir_mascara_agua(terreno, masc_estranha, 3) is None


# =============================================================================
# acha_nascente  (produtora -> tuple | None)
# =============================================================================

def test_acha_nascente_ok_encontra_canto_com_zero():
    mat = np.array([[5, 5], [5, 0]], dtype=float)
    assert acha_nascente(mat) == (1, 1)


def test_acha_nascente_erro_nenhum_canto_zero():
    mat = np.ones((2, 2), dtype=float)
    assert acha_nascente(mat) is None


# =============================================================================
# carrega_dados  (ação -> int)
# =============================================================================

def test_carrega_dados_ok_mascara_valida():
    conteudo = {"masc_agua": [[1, 0], [0, 0]]}
    with patch("builtins.open", mock_open()), \
            patch("agua.agua.load", return_value=conteudo):
        assert carrega_dados("ultima_execucao.json") == 0
    # Estado encapsulado deve ter sido carregado.
    assert _dados["mascara"] is not None
    assert _dados["nascente"] is not None


def test_carrega_dados_erro_sem_chave_masc_agua():
    with patch("builtins.open", mock_open()), \
            patch("agua.agua.load", return_value={"outra_coisa": 1}):
        assert carrega_dados("ultima_execucao.json") == 1


def test_carrega_dados_erro_nascente_ausente():
    # Máscara sem nenhum canto igual a 0 -> nascente não encontrada.
    conteudo = {"masc_agua": [[1, 1], [1, 1]]}
    with patch("builtins.open", mock_open()), \
            patch("agua.agua.load", return_value=conteudo):
        assert carrega_dados("ultima_execucao.json") == 1


def test_carrega_dados_erro_falha_ao_abrir_arquivo():
    with patch("builtins.open", side_effect=OSError("arquivo ausente")):
        assert carrega_dados("inexistente.json") == 2
