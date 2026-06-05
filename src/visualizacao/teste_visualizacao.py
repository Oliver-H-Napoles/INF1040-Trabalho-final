import unittest
import numpy as np
import matplotlib.pyplot as plt

from src.visualizacao.visualizacao import (
    projetar_camadas,
    gerar_heatmap,
    plot_layers
)

class TesteVisualizacao(unittest.TestCase):
    """
    Testes automatizados do módulo de visualização.

    A validação final dos mapas e heatmaps gerados é manual,
    mas estes testes verificam os retornos das funções de acesso.
    """

    def test_projetar_camadas_sucesso(self):
        terreno = np.array([[1, 2], [3, 4]])
        masc_agua = np.array([[0, 1], [0, 1]])

        self.assertEqual(projetar_camadas(terreno, masc_agua), 0)

    def test_projetar_camadas_terreno_invalido(self):
        masc_agua = np.array([[0, 1], [0, 1]])

        self.assertEqual(projetar_camadas(None, masc_agua), 1)

    def test_projetar_camadas_mascara_invalida(self):
        terreno = np.array([[1, 2], [3, 4]])

        self.assertEqual(projetar_camadas(terreno, None), 2)

    def test_projetar_camadas_dimensoes_incompativeis(self):
        terreno = np.array([[1, 2], [3, 4]])
        masc_agua = np.array([[0, 1, 0]])

        self.assertEqual(projetar_camadas(terreno, masc_agua), 3)

    def test_gerar_heatmap_sucesso(self):
        mapa = np.array([[1, 2], [3, 4]])

        plot_obj = gerar_heatmap(mapa)

        self.assertIsNotNone(plot_obj)

    def test_gerar_heatmap_mapa_invalido(self):
        self.assertIsNone(gerar_heatmap(None))

    def test_gerar_heatmap_mapa_vazio(self):
        mapa = np.array([])

        self.assertIsNone(gerar_heatmap(mapa))

    def test_plot_layers_sucesso(self):
        fig, _ = plt.subplots()

        self.assertEqual(plot_layers(fig), 0)

    def test_plot_layers_objeto_invalido(self):
        self.assertEqual(plot_layers(None), 1)


def main():
    unittest.main()


if __name__ == "__main__":
    main()