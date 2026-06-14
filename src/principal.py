# ==========================================================
# IMPORTS DOS OUTROS MÓDULOS
# ==========================================================
import sys

# Módulo Validação
from validacao.validacao import valida_uf, valida_elevacao

# Módulo Terreno
from terreno.terreno import isolar_estado

# Módulo Água
from agua import cria_mascara_agua, expandir_mascara_agua, carrega_dados

# Módulo Visualização
from visualizacao.visualizacao import projetar_camadas, gerar_heatmap, plot_layers

# Módulo Persistência
from persistencia.persistencia import (
    carregar_estado,
    avancar_etapa,
    carregar_dados_salvos,
    resetar_estado,
    ETAPA_INICIAL,
    ETAPA_TERRENO,
    ETAPA_MASCARA,
    ETAPA_SIMULACAO,
    obter_etapa_atual,
    obter_uf_salva,
    obter_elevacao_salva,
    obter_metadado,
    definir_parametros_base,
    obter_dado_carregado,
    obter_metadado_carregado
)

# ==========================================================
# MÓDULO PRINCIPAL
# ==========================================================

def obter_elevacao() -> int:
    """
    Captura a elevação informada pelo usuário.
    """
    entrada = input("Digite a elevação do nível do mar (em metros): ")
    try:
        return int(entrada)
    except ValueError:
        raise ValueError("Apenas números inteiros são aceitos.")

# ==========================================================
# FLUXO PRINCIPAL DA APLICAÇÃO
# ==========================================================

def main(uf: str) -> int:
    """
    Fluxo principal da aplicação para simulação de elevação do nível do mar.
    """
    print("\nSIMULADOR DE ELEVAÇÃO DO NÍVEL DO MAR\n")

    # 1. CARREGAMENTO INICIAL (Uso estrito do TAD)
    estado = carregar_estado()
    dados  = carregar_dados_salvos(estado)
    etapa_atual = obter_etapa_atual(estado)
 
    if etapa_atual > ETAPA_INICIAL:
        print(
            f"[main] Retomando execução anterior: etapa {etapa_atual}, "
            f"UF={obter_uf_salva(estado)}, elevação={obter_elevacao_salva(estado)}m.\n"
        )
 
    raster_isolado = obter_dado_carregado(dados, "raster_isolado")   
    mascara_agua   = obter_dado_carregado(dados, "mascara_agua")     
    area_inundada  = obter_metadado_carregado(dados, "area_inundada")

    # Restaura o estado interno do módulo de água logo no início
    if mascara_agua is not None:
        carrega_dados(mascara_agua)

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

    # Lógica de reinício
    uf_salva = obter_uf_salva(estado)

    if uf_salva is not None:
        uf_diferente = str(uf_salva).strip().upper() != str(uf).strip().upper()

        if uf_diferente:
            # UF mudou: descarta tudo, inclusive o terreno
            print("[main] UF alterada. Reiniciando a simulação do zero (Hard Reset).\n")
            estado = resetar_estado()
            dados  = {}
            etapa_atual = obter_etapa_atual(estado)
            raster_isolado = None
            mascara_agua   = None
            area_inundada  = None
        else:
            # Mesma UF (elevação igual ou diferente): sempre recria a máscara de água
            print("[main] Recriando a máscara de água.\n")
            etapa_atual = ETAPA_TERRENO
            mascara_agua  = None
            area_inundada = None

    # Inicializa as variáveis de controle ANTES do try
    arquivos_para_salvar = {}
    metadados_para_salvar = {}
    novo_estado_num = etapa_atual

    # 3. Bloco principal protegido
    try:
        # ------------------------------------------------------
        # Terreno
        # ------------------------------------------------------
        if novo_estado_num < ETAPA_TERRENO:
            print("[main] Etapa 1: carregando terrain...")
            raster_isolado = isolar_estado(uf)
            if raster_isolado is None:
                print("Erro: não foi possível carregar o terreno.")
                return 3
            
            arquivos_para_salvar["raster_isolado"] = raster_isolado
            metadados_para_salvar["shape"] = list(raster_isolado.shape)
            novo_estado_num = ETAPA_TERRENO
        else:
            print(f"[main] Etapa 1 já concluída — raster carregado do disco/memória.")

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
        # Simulação (sempre executa: máscara sempre recriada acima)
        # ------------------------------------------------------
        print("[main] Etapa 3: executando simulação de enchente...")
        area_inundada = expandir_mascara_agua(raster_isolado, mascara_agua, elevacao)
        if area_inundada is None:
            print("Erro: não foi possível expandir a máscara de água.")
            return 4

        metadados_para_salvar["area_inundada"] = area_inundada
        metadados_para_salvar["elevacao_simulada"] = elevacao
        novo_estado_num = ETAPA_SIMULACAO

        # ------------------------------------------------------------------
        # Resultados e Visualização
        # ------------------------------------------------------------------
        print(
            f"\nÁrea inundada: {area_inundada * 900 / 1_000_000:.2f} km² "
            f"({area_inundada} células)"
        )
    
        projetar_camadas(raster_isolado, mascara_agua)
        #heatmap = gerar_heatmap(raster_isolado)
        #plot_layers(heatmap)
    
        print("\nSimulação concluída com sucesso.")
        return 0

    except KeyboardInterrupt:
        print("\n[Aviso] Processo interrompido pelo usuário (Ctrl+C). Salvando progresso...")
        return 130

    finally:
        # ------------------------------------------------------------------
        # PERSISTÊNCIA
        # ------------------------------------------------------------------
        if arquivos_para_salvar or metadados_para_salvar:
            print("\n[main] Gravando dados encapsulados no arquivo antes de encerrar...")
            definir_parametros_base(estado, uf, elevacao)
            
            avancar_etapa(
                estado,
                nova_etapa      = novo_estado_num,
                novos_arquivos  = arquivos_para_salvar,
                novos_metadados = metadados_para_salvar,
            )

if __name__ == "__main__":
    if len(sys.argv) > 1:
        uf_alvo = sys.argv[1]
    else:
        print("Erro: UF não fornecida. Use: python principal.py <UF>")
        sys.exit(1)
    
    sys.exit(main(uf_alvo))