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
from terreno.terreno import isolar_estado

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

from persistencia.persistencia import (
    carregar_estado,
    avancar_etapa,
    carregar_dados_salvos,
    resetar_estado,
    ETAPA_INICIAL,
    ETAPA_TERRENO,
    ETAPA_MASCARA,
    ETAPA_SIMULACAO,
    salvar_estado,
)

# ==========================================================
# MÓDULO PRINCIPAL
# ==========================================================

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
    """
    print("\nSIMULADOR DE ELEVAÇÃO DO NÍVEL DO MAR\n")

    # 1. Carregamento inicial
    estado = carregar_estado()
    dados  = carregar_dados_salvos(estado)
 
    if estado["state"] > ETAPA_INICIAL:
        print(
            f"[main] Retomando execução anterior: etapa {estado['state']}, "
            f"UF={estado['uf']}, elevação={estado['elevacao']}m.\n"
        )
 
    raster_isolado = dados.get("raster_isolado")   
    mascara_agua   = dados.get("mascara_agua")     
    area_inundada  = dados.get("_metadata", {}).get("area_inundada")

    # 2. Validações iniciais
    if valida_uf(uf) != 0:
        print("Erro: UF inválida.")
        return 1

    try:
        elevacao = obter_elevacao()
    except ValueError as erro:
        print(f"Erro: {erro}")
        return 2

    if valida_elevacao(elevacao) != 0:
        print("Erro: Elevação inválida.")
        return 2
       
    if estado["state"] == ETAPA_MASCARA and raster_isolado is not None:
        xy_fonte = estado["metadata"].get("xy_fonte", 2)
        tam_x, tam_y = raster_isolado.shape
        mascara_agua = cria_mascara_agua(tam_x, tam_y, xy_fonte)

    uf_salva = estado.get("uf")
    elevacao_salva = estado.get("elevacao")

    if uf_salva is not None:
        if uf_salva != uf or (elevacao_salva is not None and elevacao_salva != elevacao):
            print(f"[main] Parâmetros (UF ou Elevação) alterados. Reiniciando do zero.\n")
            estado = resetar_estado()
            dados  = {}
            raster_isolado = None
            mascara_agua   = None
            area_inundada  = None

    # Inicializa as variáveis de controle ANTES do try
    arquivos_para_salvar = {}
    metadados_para_salvar = {}
    novo_estado_num = estado["state"]

    # 3. Bloco principal protegido
    try:
        # ------------------------------------------------------
        # Terreno
        # ------------------------------------------------------
        if estado["state"] < ETAPA_TERRENO:
            print("[main] Etapa 1: carregando terrain...")
            raster_isolado = isolar_estado(uf)
            if raster_isolado is None:
                print("Erro: não foi possível carregar o terreno.")
                return 3
            
            arquivos_para_salvar["raster_isolado"] = raster_isolado
            metadados_para_salvar["shape"] = list(raster_isolado.shape)
            novo_estado_num = ETAPA_TERRENO
        else:
            print(f"[main] Etapa 1 já concluída — raster carregado do disco.")

        # ------------------------------------------------------
        # Água
        # ------------------------------------------------------
        if novo_estado_num < ETAPA_MASCARA:
            print("[main] Etapa 2: criando máscara de água...")
            tam_x, tam_y = raster_isolado.shape
            xy_fonte     = 2  
    
            mascara_agua = cria_mascara_agua(tam_x, tam_y, xy_fonte)
            if mascara_agua is None:
                print("Erro: não foi possível criar a máscara de água.")
                return 4
    
            arquivos_para_salvar["mascara_agua"] = mascara_agua
            metadados_para_salvar["xy_fonte"] = xy_fonte
            novo_estado_num = ETAPA_MASCARA
        else:
            print("[main] Etapa 2 já concluída — máscara carregada do disco.")

        # ------------------------------------------------------
        # Simulação
        # ------------------------------------------------------
        elevacao_anterior = estado["metadata"].get("elevacao_simulada")
        simulacao_atualizada = (
            novo_estado_num >= ETAPA_SIMULACAO
            and elevacao_anterior == elevacao
        )

        if not simulacao_atualizada:
            print("[main] Etapa 3: executando simulação de enchente...")
            area_inundada = expandir_mascara_agua(raster_isolado, mascara_agua, elevacao)
            if area_inundada is None:
                print("Erro: não foi possível expandir a máscara de água.")
                return 4
    
            metadados_para_salvar["area_inundada"] = area_inundada
            metadados_para_salvar["elevacao_simulada"] = elevacao
            novo_estado_num = ETAPA_SIMULACAO
        else:
            area_inundada = estado["metadata"]["area_inundada"]
            print(f"[main] Etapa 3 já concluída para elevação={elevacao}m.")

        # ------------------------------------------------------------------
        # Resultados e Visualização (Ocorre apenas se não houver interrupção)
        # ------------------------------------------------------------------
        print(
            f"\nÁrea inundada: {area_inundada * 900 / 1_000_000:.2f} km² "
            f"({area_inundada} células)"
        )
    
        projetar_camadas(raster_isolado, mascara_agua)
        heatmap = gerar_heatmap(raster_isolado)
        plot_layers(heatmap)
    
        print("\nSimulação concluída com sucesso.")
        return 0

    except KeyboardInterrupt:
        print("\n[Aviso] Processo interrompido pelo usuário (Ctrl+C). Salvando progresso...")
        return 130 # Código padrão de saída em sistemas Unix para KeyboardInterrupt

    finally:
        # ------------------------------------------------------------------
        # PERSISTÊNCIA — Executada independentemente de sucesso, erro ou Ctrl+C
        # ------------------------------------------------------------------
        if arquivos_para_salvar or metadados_para_salvar:
            print("\n[main] Gravando dados encapsulados no arquivo antes de encerrar...")
            estado["uf"]       = uf
            estado["elevacao"] = elevacao
            
            avancar_etapa(
                estado,
                nova_etapa      = novo_estado_num,
                novos_arquivos  = arquivos_para_salvar,
                novos_metadados = metadados_para_salvar,
            )

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        uf_alvo = sys.argv[1]
    else:
        print("Erro: UF não fornecida. Use: python principal.py <UF>")
        sys.exit(1)
    
    sys.exit(main(uf_alvo))
