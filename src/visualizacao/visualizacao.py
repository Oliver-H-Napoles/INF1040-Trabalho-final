__all__ = [
    "projetar_camadas",
    "gerar_heatmap",
    "plot_layers"
]

import numpy as np
import matplotlib.pyplot as plt


def projetar_camadas(terreno, masc_agua, fator_reducao=10) -> int:
    """
    Projeta a máscara de água sobre a matriz/raster do terreno.

    Assertiva de entrada (Pré-condição):
    - 'terreno' deve ser uma matriz/raster válido, contendo os dados do terreno.
    - 'masc_agua' deve ser uma matriz válida, indicando as posições alagadas.
    - 'terreno' e 'masc_agua' devem representar a mesma área e possuir as mesmas dimensões.

    Assertiva de saída (Pós-condição):
    - Se as entradas forem válidas, a função gera uma visualização com a máscara de água
      sobreposta ao terreno.
    - A validação final da imagem gerada será feita manualmente, pois os mapas não serão
      persistidos em arquivo para comparação automática.

    @param terreno: Matriz/raster com os dados do terreno.
    @param masc_agua: Matriz indicando as regiões alagadas.
    @return:
        0 -> sucesso
        1 -> terreno inválido
        2 -> máscara de água inválida
        3 -> dimensões incompatíveis
        4 -> erro inesperado ao gerar visualização
    """
    if terreno is None or not hasattr(terreno, "shape"):
        return 1

    if masc_agua is None or not hasattr(masc_agua, "shape"):
        return 2

    if terreno.shape != masc_agua.shape:
        return 3

    # Reduzindo a resolução pulando elementos da matriz (decimação)
    terreno_red = terreno[::fator_reducao, ::fator_reducao]
    masc_agua_red = masc_agua[::fator_reducao, ::fator_reducao]

    try:
        plt.figure()
        plt.imshow(terreno_red, cmap="terrain")
        agua = np.ma.masked_where(masc_agua_red == 0, masc_agua_red)

        plt.imshow(
            agua,
            cmap="Blues",
            alpha=0.7,
            interpolation="none"
        )
        plt.title(f"Projeção da inundação")
        plt.show()
        return 0
    except Exception:
        return 4


def gerar_heatmap(mapa, fator_reducao=10):
    """
    Gera um objeto de heatmap a partir de uma matriz.

    Assertiva de entrada (Pré-condição):
    - 'mapa' deve ser uma matriz válida.
    - 'mapa' deve conter dados numéricos.
    - 'mapa' não pode estar vazio.

    Assertiva de saída (Pós-condição):
    - Se a matriz for válida, a função gera e retorna um objeto de plot contendo o heatmap.
    - A validação final do heatmap gerado será feita manualmente.

    @param mapa: Matriz com os dados que serão representados em heatmap.
    @return:
        plot_obj -> objeto de plot gerado com sucesso
        None -> erro ao gerar heatmap por matriz inválida, vazia ou incompatível
    """
    if mapa is None or not hasattr(mapa, "shape"):
        return None

    if mapa.size == 0:
        return None

    # Reduzindo a resolução
    mapa_red = mapa[::fator_reducao, ::fator_reducao]

    try:
        fig, ax = plt.subplots()
        ax.imshow(mapa_red)
        ax.set_title(f"Heatmap da área (Resolução 1/{fator_reducao})")
        return fig
    except Exception as erro:
        print(f"Erro ao gerar heatmap: {erro}")
        return None


def plot_layers(plot_obj) -> int:
    """
    Exibe uma visualização a partir de um objeto de plot.

    Assertiva de entrada (Pré-condição):
    - 'plot_obj' deve ser um objeto de plot válido.

    Assertiva de saída (Pós-condição):
    - Se o objeto de plot for válido, a função exibe a visualização final.
    - A validação final da imagem exibida será feita manualmente.

    @param plot_obj: Objeto de plot gerado por uma função de visualização.
    @return:
        0 -> sucesso
        1 -> objeto de plot inválido ou nulo
        2 -> erro inesperado ao exibir visualização
    """
    if plot_obj is None:
        return 1

    try:
        plt.show()
        return 0
    except Exception:
        return 2