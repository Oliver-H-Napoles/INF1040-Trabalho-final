"""
Testes unitários do Módulo Água.

Convenção de saídas validada por estes testes:
    - cria_mascara_agua / expandir_mascara_agua / acha_nascente (produtoras):
        retornam o objeto/valor em caso de êxito e `None` em caso de erro.
    - carrega_dados (ação):
        0 -> êxito; 1 -> parâmetro inválido ou nascente ausente.
"""
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
    """Fonte=0 (3x2) -> nascente no canto superior esquerdo (0,0)."""
    esperado = np.array([[1, 0], [0, 0], [0, 0]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 0), esperado)


def test_cria_mascara_ok_canto_superior_direito():
    """Fonte=1 (3x2) -> nascente no canto superior direito (0,1)."""
    esperado = np.array([[0, 1], [0, 0], [0, 0]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 1), esperado)


def test_cria_mascara_ok_canto_inferior_direito():
    """Fonte=2 (3x2) -> nascente no canto inferior direito (2,1)."""
    esperado = np.array([[0, 0], [0, 0], [0, 1]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 2), esperado)


def test_cria_mascara_ok_canto_inferior_esquerdo():
    """Fonte=3 (3x2) -> nascente no canto inferior esquerdo (2,0)."""
    esperado = np.array([[0, 0], [0, 0], [1, 0]], dtype=float)
    assert np.array_equal(cria_mascara_agua(3, 2, 3), esperado)


def test_cria_mascara_ok_dimensoes_maiores():
    """Dimensões 4x3 com fonte=2 -> matriz correta com nascente em (3,2)."""
    esperado = np.array(
        [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 1]], dtype=float
    )
    assert np.array_equal(cria_mascara_agua(4, 3, 2), esperado)


@pytest.mark.parametrize("tam_x, tam_y", [(-1, 0), (0, 0), (10, -2), (0, 5)])
def test_cria_mascara_erro_tamanho_invalido(tam_x, tam_y):
    """Tamanho inválido (dimensão <= 0) -> None (erro)."""
    assert cria_mascara_agua(tam_x, tam_y, 0) is None


@pytest.mark.parametrize("xy_fonte", [-1, 4, 5, 100])
def test_cria_mascara_erro_fonte_invalida(xy_fonte):
    """Fonte fora do intervalo [0, 3] -> None (erro)."""
    assert cria_mascara_agua(10, 10, xy_fonte) is None


# =============================================================================
# expandir_mascara_agua  (produtora -> int | None)
# =============================================================================

def test_expandir_ok_inundacao_parcial():
    """Terreno 3x3, nível 3 -> 7 células inundadas (inundação parcial)."""
    terreno = np.array([[5, 3, 2], [10, 2, 0], [1, 0, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3) == 7


def test_expandir_ok_inundacao_minima():
    """Terreno cercado por barreiras, nível 3 -> só a nascente (1 célula)."""
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3) == 1


def test_expandir_ok_terreno_decimal():
    """Terreno 4x3 com altitudes decimais, nível 3.0 -> 8 células inundadas."""
    terreno = np.array(
        [[5, 4, 5.3], [3, 2.5, 1], [2.6, 1.1, 0.9], [2.3, 3.2, 0]], dtype=float
    )
    masc = cria_mascara_agua(4, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3.0) == 8


def test_expandir_erro_nivel_do_mar_nulo():
    """Nível do mar igual a zero -> None (erro)."""
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 0) is None


def test_expandir_erro_nivel_do_mar_negativo():
    """Nível do mar negativo (-2) -> None (erro)."""
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, -2) is None


def test_expandir_erro_tamanhos_incompativeis_mascara_menor():
    """Máscara menor que o terreno -> None (erro de tamanho)."""
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    masc = cria_mascara_agua(2, 2, 2)
    assert expandir_mascara_agua(terreno, masc, 3) is None


def test_expandir_erro_tamanhos_incompativeis_terreno_maior():
    """Terreno maior que a máscara -> None (erro de tamanho)."""
    terreno = np.array(
        [[5, 1, 2, 3], [1, 4, 10, 3], [1, 10, 0, 3]], dtype=float
    )
    masc = cria_mascara_agua(3, 3, 2)
    assert expandir_mascara_agua(terreno, masc, 3) is None


def test_expandir_erro_mascara_diferente_da_armazenada():
    """Máscara não corresponde à armazenada no módulo -> None (erro)."""
    terreno = np.array([[5, 1, 2], [1, 4, 10], [1, 10, 0]], dtype=float)
    cria_mascara_agua(3, 3, 2)  # define a máscara armazenada no módulo
    # Máscara de mesmo tamanho, mas que não corresponde à armazenada.
    masc_estranha = np.zeros((3, 3), dtype=float)
    assert expandir_mascara_agua(terreno, masc_estranha, 3) is None


# =============================================================================
# acha_nascente  (produtora -> tuple | None)
# =============================================================================

def test_acha_nascente_ok_encontra_canto_com_um():
    """Máscara com canto inferior direito = 1 (água) -> nascente em (1,1)."""
    mat = np.zeros((2, 2), dtype=float)
    mat[1][1] = 1
    assert acha_nascente(mat) == (1, 1)


def test_acha_nascente_erro_nenhum_canto_com_um():
    """Máscara sem nenhum canto igual a 1 -> None (nascente não encontrada)."""
    mat = np.zeros((2, 2), dtype=float)
    assert acha_nascente(mat) is None


# =============================================================================
# carrega_dados  (ação -> int)
# =============================================================================

def test_carrega_dados_ok_mascara_valida():
    """Matriz válida com nascente -> 0 (êxito) e estado do módulo carregado."""
    mascara = np.zeros((2, 2), dtype=float)
    mascara[0][0] = 1  # Garante que a nascente existe no canto superior esquerdo
    assert carrega_dados(mascara) == 0
    assert _dados["mascara"] is not None
    assert _dados["nascente"] is not None


def test_carrega_dados_erro_parametro_invalido():
    """Passando algo que não é matriz -> 1 (erro)."""
    assert carrega_dados(None) == 1
    assert carrega_dados("string_nao_eh_matriz") == 1


def test_carrega_dados_erro_nascente_ausente():
    """Matriz válida mas sem nascente (nenhum canto 1) -> 1 (erro)."""
    mat = np.zeros((2, 2), dtype=float)
    assert carrega_dados(mat) == 1