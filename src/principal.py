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

def main(uf):
    print("\nSIMULADOR DE ELEVAÇÃO DO NÍVEL DO MAR\n")

    status_uf = valida_uf(uf)

    # ------------------------------------------------------
    # Entrada do usuário
    # ------------------------------------------------------

    elevacao = obter_elevacao()
    

    if status_uf != 0:
        print("Erro: UF inválida.")
        return

    status_elevacao = valida_elevacao(elevacao)

    if status_elevacao != 0:
        print("Erro: Elevação inválida.")
        return

    # ------------------------------------------------------
    # Terreno
    # ------------------------------------------------------

    raster_isolado = carregar_estado(uf_alvo)

    # ------------------------------------------------------
    # Água
    # ------------------------------------------------------

    tam_x = raster_isolado.shape[0]
    tam_y = raster_isolado.shape[1]

    # canto inferior direito (conforme especificação)
    xy_fonte = 2

    masc_agua = cria_mascara_agua(
        tam_x,
        tam_y,
        xy_fonte
    )

    area_inundada = expandir_mascara_agua(
        raster_isolado,
        masc_agua,
        elevacao
    )

    print(
        f"\nÁrea inundada: {area_inundada:.2f}%"
    )

    # ------------------------------------------------------
    # Visualização
    # ------------------------------------------------------

    mapa = projetar_camadas(
        raster_isolado,
        masc_agua
    )

    heatmap = gerar_heatmap(
        mapa
    )

    plot_layers(
        heatmap
    )

    print("\nSimulação concluída com sucesso.")




if __name__ == "__main__":
     
    if len(sys.argv) > 1:
        uf_alvo = sys.argv[1]
    else:
        print("Erro: UF não fornecida. Use: python principal.py <UF>")
        sys.exit(1)
    main(uf_alvo)