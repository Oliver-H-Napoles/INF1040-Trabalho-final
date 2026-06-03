import pytest
import numpy as np
import os
import json

# Altere "modulo_terreno" para o nome exato do seu arquivo
from terreno import (
    obter_caminhos_arquivos,
    carregar_dados_topograficos,
    carregar_fronteiras,
    aplicar_mascara_isolamento,
    _arquivos_carregados 
)

# Descobre o caminho absoluto do projeto para não depender de onde o terminal foi aberto
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_ATUAL) # Volta uma pasta (sai de src/ para INF1040-Trabalho-final/)
DIRETORIO_DATA = os.path.join(DIRETORIO_RAIZ, "data")

ESTADO_TESTE = "SP" # Escolha um estado que você tem certeza que os arquivos reais estão na pasta data/

@pytest.fixture(autouse=True)
def configurar_diretorio_e_limpar_cache(monkeypatch):
    """
    1. Muda o terminal temporariamente para a pasta 'data' para que o 
       open('estados.json') do seu código original funcione perfeitamente.
    2. Limpa a memória RAM entre os testes.
    """
    monkeypatch.chdir(DIRETORIO_DATA)
    _arquivos_carregados["rasters"].clear()
    _arquivos_carregados["poligonos"].clear()

# =============================================================================
# 1. Testes: obter_caminhos_arquivos
# =============================================================================

def test_obter_caminhos_arquivos_caso1():
    """
    Caso 1: Informar uma sigla de UF litorânea válida usando os dados reais.
    """
    topo, front = obter_caminhos_arquivos(ESTADO_TESTE)
    
    assert topo is not None
    assert front is not None
    # Verifica se os arquivos retornados pelo JSON de fato existem na pasta data
    assert os.path.exists(topo), f"Arquivo TIF {topo} não encontrado na pasta data/"
    assert os.path.exists(front), f"Arquivo SHP {front} não encontrado na pasta data/"

def test_obter_caminhos_arquivos_uf_inexistente():
    """Teste de segurança: UF não mapeada no JSON."""
    topo, front = obter_caminhos_arquivos("XX")
    assert topo is None
    assert front is None

# =============================================================================
# 2. Testes: carregar_dados_topograficos
# =============================================================================

def test_carregar_dados_topograficos_caso1():
    """
    Caso 1: Carregar o TIF real da UF escolhida.
    """
    topo, _ = obter_caminhos_arquivos(ESTADO_TESTE)
    raster_terreno, transform = carregar_dados_topograficos(topo)
    
    assert raster_terreno is not None
    assert isinstance(raster_terreno, np.ndarray)
    assert transform is not None

def test_carregar_dados_topograficos_caso2():
    """Caso 2: Caminho apontando para arquivo inexistente."""
    raster_terreno, transform = carregar_dados_topograficos("caminho_inexistente/falso.tif")
    
    assert raster_terreno is None
    assert transform is None

# =============================================================================
# 3. Testes: carregar_fronteiras
# =============================================================================

def test_carregar_fronteiras_caso1():
    """
    Caso 1: Carregar o SHP real da UF escolhida.
    """
    _, front = obter_caminhos_arquivos(ESTADO_TESTE)
    poligono_fronteira = carregar_fronteiras(front, ESTADO_TESTE)
    
    assert poligono_fronteira is not None

def test_carregar_fronteiras_caso2():
    """Caso 2: Caminho válido, mas buscando uma UF que não está dentro do shapefile."""
    _, front = obter_caminhos_arquivos(ESTADO_TESTE)
    poligono_fronteira = carregar_fronteiras(front, "XX")
    
    assert poligono_fronteira is None

def test_carregar_fronteiras_caso4():
    """Caso 4: UF válida mas arquivo inexistente."""
    poligono_fronteira = carregar_fronteiras("caminho_inexistente/front_falso.shp", ESTADO_TESTE)
    assert poligono_fronteira is None

# =============================================================================
# 4. Testes: aplicar_mascara_isolamento
# =============================================================================

def test_aplicar_mascara_isolamento_caso1():
    """
    Caso 1: Aplica a máscara usando o TIF e o SHP reais do mesmo estado.
    Verifica se a matriz resultante contém as barreiras aplicadas corretamente.
    """
    topo, front = obter_caminhos_arquivos(ESTADO_TESTE)
    
    raster_terreno, transform = carregar_dados_topograficos(topo)
    poligono = carregar_fronteiras(front, ESTADO_TESTE)
    
    raster_delimitado = aplicar_mascara_isolamento(raster_terreno, poligono, transform)
    
    assert raster_delimitado is not None
    # Verifica se a barreira (10000) foi aplicada fora da fronteira do estado
    assert 10000 in raster_delimitado
    # Garante que os dados do terreno original também foram preservados dentro do estado
    assert np.any(raster_delimitado != 10000)

def test_aplicar_mascara_isolamento_caso2():
    """
    Caso 2: Fornecer topografia válida de um estado e o polígono de outro distante.
    Como não há sobreposição, a matriz deve ser 100% preenchida com a barreira.
    """
    topo_rs, _ = obter_caminhos_arquivos("RS")
    _, front_sp = obter_caminhos_arquivos("SP") # Pega o polígono de SP
    
    # Carrega o terreno do RJ e tenta mascarar com o polígono de SP
    raster_terreno, transform = carregar_dados_topograficos(topo_rs)
    poligono_sp = carregar_fronteiras(front_sp, "SP")
    
    raster_delimitado = aplicar_mascara_isolamento(raster_terreno, poligono_sp, transform)
    
    assert raster_delimitado is not None
    assert np.all(raster_delimitado == 10000)