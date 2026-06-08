# ==========================================================
# IMPORTS DOS OUTROS MÓDULOS
# ==========================================================
import sys

# Módulo Validação
from validacao.validacao import (
    valida_uf,
    valida_elevacao
)

# Módulo Terreno
from terreno.terreno import carregar_estado

# Módulo Água
from agua import (
    cria_mascara_agua,
    expandir_mascara_agua
)

# Módulo Visualização
from visualizacao.visualizacao import (
    projetar_camadas,
    gerar_heatmap,
    plot_layers
)

# ==========================================================
# MÓDULO PRINCIPAL
# ==========================================================

def obter_uf() -> str:
    """
    Captura a UF digitada pelo usuário.

    Caso 1:
        Entrada válida.

    Caso 2:
        Remove espaços e converte para maiúsculas.

    Caso 3:
        UF sem litoral.
        O tratamento final será feito pelo módulo validação.

    Caso 4:
        UF inexistente.
        O tratamento final será feito pelo módulo validação.
    """

    uf = input("Digite a sigla da UF desejada: ")

    uf = uf.strip().upper()

    return uf


def obter_elevacao() -> int:
    """
    Captura a elevação informada pelo usuário.

    Caso 1:
        Retorna inteiro válido.

    Caso 2:
        Rejeita letras, caracteres especiais e decimais.
    """

    entrada = input(
        "Digite a elevação do nível do mar (em metros): "
    )

    try:
        elevacao = int(entrada)
        return elevacao

    except ValueError:
        raise ValueError(
            "Apenas números inteiros são aceitos."
        )


# ==========================================================
# FLUXO PRINCIPAL DA APLICAÇÃO
# ==========================================================

def main(uf: str) -> int:
    """
    Fluxo principal da aplicação.

    @returns (convenção de ação — int):
        0 -> êxito;
        1 -> UF inválida;
        2 -> elevação inválida;
        3 -> falha ao carregar o terreno;
        4 -> falha na simulação da água.
    """
    print("\nSIMULADOR DE ELEVAÇÃO DO NÍVEL DO MAR\n")

    # ------------------------------------------------------
    # Validação da UF
    # ------------------------------------------------------

    if valida_uf(uf) != 0:
        print("Erro: UF inválida.")
        return 1

    # ------------------------------------------------------
    # Entrada e validação da elevação
    # ------------------------------------------------------

    try:
        elevacao = obter_elevacao()
    except ValueError as erro:
        print(f"Erro: {erro}")
        return 2

    if valida_elevacao(elevacao) != 0:
        print("Erro: Elevação inválida.")
        return 2

    # ------------------------------------------------------
    # Terreno
    # ------------------------------------------------------

    raster_isolado = carregar_estado(uf)
    if raster_isolado is None:
        print("Erro: não foi possível carregar o terreno.")
        return 3

    # ------------------------------------------------------
    # Água
    # ------------------------------------------------------

    tam_x, tam_y = raster_isolado.shape

    # canto inferior direito (conforme especificação)
    xy_fonte = 2

    masc_agua = cria_mascara_agua(tam_x, tam_y, xy_fonte)
    if masc_agua is None:
        print("Erro: não foi possível criar a máscara de água.")
        return 4

    area_inundada = expandir_mascara_agua(raster_isolado, masc_agua, elevacao)
    if area_inundada is None:
        print("Erro: não foi possível expandir a máscara de água.")
        return 4

    print(
        f"\nÁrea inundada: {area_inundada*900/1000000:.2f} km² ({area_inundada} células)"
    )

    # ------------------------------------------------------
    # Visualização
    # ------------------------------------------------------

    projetar_camadas(raster_isolado, masc_agua)

    heatmap = gerar_heatmap(raster_isolado)

    plot_layers(heatmap)

    print("\nSimulação concluída com sucesso.")
    return 0


if __name__ == "__main__":
     
    if len(sys.argv) > 1:
        uf_alvo = sys.argv[1]
    else:
        print("Erro: UF não fornecida. Use: python principal.py <UF>")
        sys.exit(1)
    sys.exit(main(uf_alvo))