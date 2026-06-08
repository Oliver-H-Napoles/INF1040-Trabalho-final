"""
Testes unitários do Módulo Principal.

Convenção de saídas validada por estes testes:
    - obter_uf (produtora): retorna a UF normalizada (str);
    - obter_elevacao (produtora): retorna int em caso de êxito e levanta
      ValueError para entrada não-inteira;
    - main (ação -> int): 0 êxito; 1 UF inválida; 2 elevação inválida;
      3 falha no terreno; 4 falha na simulação da água.

Mock: `input()` é substituído para simular a digitação do usuário e todas as
dependências de outros módulos são dubladas, isolando o fluxo de orquestração.
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import principal


# =============================================================================
# obter_uf  (produtora -> str)
# =============================================================================

def test_obter_uf_ok_retorna_sigla():
    with patch("builtins.input", return_value="RS"):
        assert principal.obter_uf() == "RS"


def test_obter_uf_ok_normaliza_espacos_e_maiusculas():
    with patch("builtins.input", return_value="  rj  "):
        assert principal.obter_uf() == "RJ"


# =============================================================================
# obter_elevacao  (produtora -> int | ValueError)
# =============================================================================

def test_obter_elevacao_ok_inteiro():
    with patch("builtins.input", return_value="42"):
        assert principal.obter_elevacao() == 42


def test_obter_elevacao_erro_entrada_nao_inteira():
    with patch("builtins.input", return_value="abc"):
        with pytest.raises(ValueError):
            principal.obter_elevacao()


# =============================================================================
# main  (ação -> int)
# =============================================================================

def _dependencias_ok():
    """Conjunto de dublês que representa um fluxo bem-sucedido de ponta a ponta."""
    return dict(
        valida_uf=MagicMock(return_value=0),
        obter_elevacao=MagicMock(return_value=5),
        valida_elevacao=MagicMock(return_value=0),
        carregar_estado=MagicMock(return_value=np.zeros((3, 3))),
        cria_mascara_agua=MagicMock(return_value=np.zeros((3, 3))),
        expandir_mascara_agua=MagicMock(return_value=100),
        projetar_camadas=MagicMock(return_value=0),
        gerar_heatmap=MagicMock(return_value=MagicMock()),
        plot_layers=MagicMock(return_value=0),
    )


def test_main_ok_fluxo_completo():
    with patch.multiple(principal, **_dependencias_ok()):
        assert principal.main("RS") == 0


def test_main_erro_uf_invalida():
    deps = _dependencias_ok()
    deps["valida_uf"] = MagicMock(return_value=1)
    with patch.multiple(principal, **deps):
        assert principal.main("ZZ") == 1


def test_main_erro_elevacao_nao_inteira():
    deps = _dependencias_ok()
    deps["obter_elevacao"] = MagicMock(side_effect=ValueError("apenas inteiros"))
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 2


def test_main_erro_elevacao_invalida():
    deps = _dependencias_ok()
    deps["obter_elevacao"] = MagicMock(return_value=-5)
    deps["valida_elevacao"] = MagicMock(return_value=1)
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 2


def test_main_erro_falha_no_terreno():
    deps = _dependencias_ok()
    deps["carregar_estado"] = MagicMock(return_value=None)
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 3


def test_main_erro_falha_ao_criar_mascara():
    deps = _dependencias_ok()
    deps["cria_mascara_agua"] = MagicMock(return_value=None)
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 4


def test_main_erro_falha_ao_expandir_mascara():
    deps = _dependencias_ok()
    deps["expandir_mascara_agua"] = MagicMock(return_value=None)
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 4
