import numpy as np
import matplotlib.pyplot as plt

from visualizacao.visualizacao import projetar_camadas, gerar_heatmap, plot_layers


def test_projetar_camadas_sucesso():
    terreno = np.array([[1, 2], [3, 4]])
    masc_agua = np.array([[0, 1], [0, 1]])

    assert projetar_camadas(terreno, masc_agua) == 0


def test_projetar_camadas_terreno_invalido():
    masc_agua = np.array([[0, 1], [0, 1]])

    assert projetar_camadas(None, masc_agua) == 1


def test_projetar_camadas_mascara_invalida():
    terreno = np.array([[1, 2], [3, 4]])

    assert projetar_camadas(terreno, None) == 2


def test_projetar_camadas_dimensoes_incompativeis():
    terreno = np.array([[1, 2], [3, 4]])
    masc_agua = np.array([[0, 1, 0]])

    assert projetar_camadas(terreno, masc_agua) == 3


def test_gerar_heatmap_sucesso():
    mapa = np.array([[1, 2], [3, 4]])

    plot_obj = gerar_heatmap(mapa)

    assert plot_obj is not None


def test_gerar_heatmap_mapa_invalido():
    assert gerar_heatmap(None) is None


def test_gerar_heatmap_mapa_vazio():
    mapa = np.array([])

    assert gerar_heatmap(mapa) is None


def test_plot_layers_sucesso():
    fig, _ = plt.subplots()

    assert plot_layers(fig) == 0


def test_plot_layers_objeto_invalido():
    assert plot_layers(None) == 1