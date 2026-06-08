import pytest
import numpy as np
import os
import json

from terreno import (
    obter_caminhos_arquivos,
    carregar_dados_topograficos,
    carregar_fronteiras,
    aplicar_mascara_isolamento,
    carregar_estado,
    _arquivos_carregados
)

# --- CONFIGURAÇÃO DE DIRETÓRIOS ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))  # .../src/terreno
DIRETORIO_SRC   = os.path.dirname(DIRETORIO_ATUAL)            # .../src
DIRETORIO_RAIZ  = os.path.dirname(DIRETORIO_SRC)              # .../ (raiz do projeto)
DIRETORIO_DATA  = os.path.join(DIRETORIO_RAIZ, "data")        # .../data  ✓

ESTADO_TESTE = "SP"
ESTADO_DISTANTE = "RS" # Usado no Caso 2 da máscara de isolamento

@pytest.fixture(autouse=True)
def configurar_diretorio_e_limpar_cache(monkeypatch):
    """
    Muda o diretório de execução para a pasta 'data' e limpa o cache da memória RAM.
    """
    monkeypatch.chdir(DIRETORIO_DATA)
    _arquivos_carregados["rasters"].clear()
    _arquivos_carregados["poligonos"].clear()

# =============================================================================
# 1. Testes: obter_caminhos_arquivos [cite: 162-165]
# =============================================================================

def test_01_obter_caminhos_arquivos_ok_caminho_valido():
    print("\nCaso de Teste 01 - Informar UF litoranea valida e retornar tupla com os caminhos corretos")
    topo, front = obter_caminhos_arquivos(ESTADO_TESTE)
    
    assert topo is not None
    assert front is not None
    assert os.path.exists(topo)
    assert os.path.exists(front)

# =============================================================================
# 2. Testes: carregar_dados_topograficos [cite: 167-175]
# =============================================================================

def test_02_carregar_dados_topograficos_ok_arquivo_integro():
    print("\nCaso de Teste 02 - Informar um caminho de diretorio valido contendo um arquivo integro")
    topo, _ = obter_caminhos_arquivos(ESTADO_TESTE)
    raster_terreno, transform = carregar_dados_topograficos(topo)
    
    assert raster_terreno is not None
    assert isinstance(raster_terreno, np.ndarray)
    assert transform is not None

def test_03_carregar_dados_topograficos_nok_arquivo_inexistente():
    print("\nCaso de Teste 03 - Informar caminho apontando para arquivo inexistente")
    raster_terreno, transform = carregar_dados_topograficos("caminho_inexistente/falso.tif")
    
    assert raster_terreno is None
    assert transform is None

def test_04_carregar_dados_topograficos_nok_arquivo_corrompido(tmp_path):
    print("\nCaso de Teste 04 - Informar caminho valido para arquivo corrompido ou formato incorreto")
    arquivo_corrompido = tmp_path / "falso_raster.tif"
    arquivo_corrompido.write_text("Arquivo txt renomeado simulando um raster corrompido")
    
    raster_terreno, transform = carregar_dados_topograficos(str(arquivo_corrompido))
    
    assert raster_terreno is None
    assert transform is None

# =============================================================================
# 3. Testes: carregar_fronteiras [cite: 176-183]
# =============================================================================

def test_05_carregar_fronteiras_ok_leitura_sucesso():
    print("\nCaso de Teste 05 - Informar arquivo valido e UF alvo existente que possua ilhas")
    _, front = obter_caminhos_arquivos(ESTADO_TESTE)
    poligono_fronteira = carregar_fronteiras(front, ESTADO_TESTE)
    
    assert poligono_fronteira is not None

def test_06_carregar_fronteiras_nok_uf_ausente():
    print("\nCaso de Teste 06 - Informar arquivo valido, mas UF alvo inexistente na tabela")
    _, front = obter_caminhos_arquivos(ESTADO_TESTE)
    poligono_fronteira = carregar_fronteiras(front, "XX")
    
    assert poligono_fronteira is None

def test_07_carregar_fronteiras_nok_formato_invalido(tmp_path):
    print("\nCaso de Teste 07 - Informar UF valida e arquivo existente, mas de formato incorreto")
    arquivo_corrompido = tmp_path / "falso_shape.shp"
    arquivo_corrompido.write_text("Conteudo de texto bloqueando a leitura do shapefile")
    
    poligono_fronteira = carregar_fronteiras(str(arquivo_corrompido), ESTADO_TESTE)
    
    assert poligono_fronteira is None

def test_08_carregar_fronteiras_nok_arquivo_inexistente():
    print("\nCaso de Teste 08 - Informar UF valida, mas caminho de arquivo inexistente")
    poligono_fronteira = carregar_fronteiras("caminho_inexistente/front_falso.shp", ESTADO_TESTE)
    
    assert poligono_fronteira is None

# =============================================================================
# 4. Testes: aplicar_mascara_isolamento [cite: 184-190]
# =============================================================================

def test_09_aplicar_mascara_isolamento_ok_sobreposicao_padrao():
    print("\nCaso de Teste 09 - Fornecer raster valido e poligono correspondente ao mesmo estado")
    topo, front = obter_caminhos_arquivos(ESTADO_TESTE)
    
    raster_terreno, transform = carregar_dados_topograficos(topo)
    poligono = carregar_fronteiras(front, ESTADO_TESTE)
    
    raster_delimitado = aplicar_mascara_isolamento(raster_terreno, poligono, transform)
    
    assert raster_delimitado is not None
    # Verifica se a barreira (10000 metros) foi aplicada externamente
    assert 10000 in raster_delimitado
    # Garante que os dados de elevacao originais (!= 10000) foram preservados internamente
    assert np.any(raster_delimitado != 10000)

def test_10_aplicar_mascara_isolamento_nok_sobreposicao_incompativel():
    print("\nCaso de Teste 10 - Fornecer raster valido e poligono de outro estado distante")
    topo_teste, _ = obter_caminhos_arquivos(ESTADO_TESTE)
    _, front_distante = obter_caminhos_arquivos(ESTADO_DISTANTE)
    
    raster_terreno, transform = carregar_dados_topograficos(topo_teste)
    poligono_distante = carregar_fronteiras(front_distante, ESTADO_DISTANTE)
    
    raster_delimitado = aplicar_mascara_isolamento(raster_terreno, poligono_distante, transform)
    
    assert raster_delimitado is not None
    # Como as coordenadas do poligono nao se sobrepoem as do mapa, a matriz inteira vira barreira
    assert np.all(raster_delimitado == 10000)

# =============================================================================
# 5. Testes de Integração: carregar_estado (Função Pública Principal)
# =============================================================================

def test_11_carregar_estado_ok_fluxo_completo():
    print("\nCaso de Teste 11 - Fluxo completo: Informar UF valida e retornar matriz isolada")
    # Ação
    matriz_resultado = carregar_estado(ESTADO_TESTE)
    
    # Verificação
    assert matriz_resultado is not None
    assert isinstance(matriz_resultado, np.ndarray)
    assert 10000 in matriz_resultado # Garante que a máscara foi aplicada
    assert np.any(matriz_resultado != 10000) # Garante que há terreno válido

def test_12_carregar_estado_nok_falha_nos_caminhos():
    print("\nCaso de Teste 12 - Falha em cascata: UF nao existe no JSON de configuracao")
    # Ação
    matriz_resultado = carregar_estado("XX")
    
    # Verificação
    assert matriz_resultado is None

def test_13_carregar_estado_nok_falha_no_raster(monkeypatch, tmp_path):
    print("\nCaso de Teste 13 - Falha em cascata: Caminhos OK, mas TIF corrompido")
    
    # Criamos um ambiente falso onde o JSON aponta para um TIF quebrado, mas um SHP real
    arquivo_corrompido = tmp_path / "falso_mosaico.tif"
    arquivo_corrompido.write_text("Raster invalido")
    
    json_falso = {"RJ": {"arquivo_topo": str(arquivo_corrompido), "arquivo_front": "front_RJ.shp"}}
    caminho_json = tmp_path / "estados.json"
    caminho_json.write_text(json.dumps(json_falso))
    
    # Forçamos o teste a rodar nessa pasta temporária
    monkeypatch.chdir(tmp_path)
    
    # Ação
    matriz_resultado = carregar_estado("RJ")
    
    # Verificação
    assert matriz_resultado is None

def test_14_carregar_estado_nok_falha_na_fronteira(monkeypatch, tmp_path):
    print("\nCaso de Teste 14 - Falha em cascata: TIF OK, mas SHP corrompido")
    
    # O inverso do anterior: TIF real, mas SHP quebrado
    arquivo_corrompido = tmp_path / "falso_shape.shp"
    arquivo_corrompido.write_text("Shapefile invalido")
    
    # Copiamos o caminho real do TIF da pasta data para o json falso
    caminho_tif_real = os.path.join(DIRETORIO_DATA, "RJ_mosaico.tif")
    
    json_falso = {"RJ": {"arquivo_topo": caminho_tif_real, "arquivo_front": str(arquivo_corrompido)}}
    caminho_json = tmp_path / "estados.json"
    caminho_json.write_text(json.dumps(json_falso))
    
    monkeypatch.chdir(tmp_path)
    
    # Ação
    matriz_resultado = carregar_estado("RJ")
    
    # Verificação
    assert matriz_resultado is None
