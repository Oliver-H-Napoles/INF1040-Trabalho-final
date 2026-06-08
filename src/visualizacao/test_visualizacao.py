"""
Testes unitários do Módulo Visualização.

Convenção de saídas validada por estes testes:
    - projetar_camadas / plot_layers (ações -> int):
        0 -> êxito; >= 1 -> códigos de erro documentados.
    - gerar_heatmap (produtora -> figura | None):
        retorna o objeto de figura em caso de êxito e `None` em caso de erro.

Mock: o `matplotlib.pyplot` é substituído para que nenhuma janela de gráfico
seja aberta e para que seja possível simular falhas de renderização.
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from visualizacao.visualizacao import projetar_camadas, gerar_heatmap, plot_layers


# =============================================================================
# projetar_camadas  (ação -> int)
# =============================================================================

def test_projetar_camadas_ok_sucesso():
    terreno = np.array([[1, 2], [3, 4]])
    masc_agua = np.array([[0, 1], [0, 1]])
    with patch("visualizacao.visualizacao.plt"):
        assert projetar_camadas(terreno, masc_agua) == 0


def test_projetar_camadas_erro_terreno_none():
    assert projetar_camadas(None, np.array([[0, 1], [0, 1]])) == 1


def test_projetar_camadas_erro_terreno_sem_shape():
    assert projetar_camadas([[1, 2], [3, 4]], np.array([[0, 1], [0, 1]])) == 1


def test_projetar_camadas_erro_mascara_none():
    assert projetar_camadas(np.array([[1, 2], [3, 4]]), None) == 2


def test_projetar_camadas_erro_mascara_sem_shape():
    assert projetar_camadas(np.array([[1, 2], [3, 4]]), [[0, 1]]) == 2


def test_projetar_camadas_erro_dimensoes_incompativeis():
    terreno = np.array([[1, 2], [3, 4]])
    masc_agua = np.array([[0, 1, 0]])
    assert projetar_camadas(terreno, masc_agua) == 3


def test_projetar_camadas_erro_falha_na_renderizacao():
    terreno = np.array([[1, 2], [3, 4]])
    masc_agua = np.array([[0, 1], [0, 1]])
    with patch("visualizacao.visualizacao.plt") as mock_plt:
        mock_plt.show.side_effect = RuntimeError("falha no backend")
        assert projetar_camadas(terreno, masc_agua) == 4


# =============================================================================
# gerar_heatmap  (produtora -> figura | None)
# =============================================================================

def test_gerar_heatmap_ok_sucesso():
    mapa = np.array([[1, 2], [3, 4]])
    fig_fake, ax_fake = MagicMock(name="fig"), MagicMock(name="ax")
    with patch("visualizacao.visualizacao.plt") as mock_plt:
        mock_plt.subplots.return_value = (fig_fake, ax_fake)
        assert gerar_heatmap(mapa) is fig_fake


def test_gerar_heatmap_erro_mapa_none():
    assert gerar_heatmap(None) is None


def test_gerar_heatmap_erro_mapa_sem_shape():
    assert gerar_heatmap([[1, 2], [3, 4]]) is None


def test_gerar_heatmap_erro_mapa_vazio():
    assert gerar_heatmap(np.array([])) is None


def test_gerar_heatmap_erro_falha_na_renderizacao():
    mapa = np.array([[1, 2], [3, 4]])
    with patch("visualizacao.visualizacao.plt") as mock_plt:
        mock_plt.subplots.side_effect = RuntimeError("falha no backend")
        assert gerar_heatmap(mapa) is None


# =============================================================================
# plot_layers  (ação -> int)
# =============================================================================

def test_plot_layers_ok_sucesso():
    plot_obj = MagicMock()
    assert plot_layers(plot_obj) == 0
    plot_obj.show.assert_called_once()


def test_plot_layers_erro_objeto_none():
    assert plot_layers(None) == 1


def test_plot_layers_erro_falha_ao_exibir():
    plot_obj = MagicMock()
    plot_obj.show.side_effect = RuntimeError("falha ao exibir")
    assert plot_layers(plot_obj) == 2
