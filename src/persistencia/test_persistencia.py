import os
import json
import pytest
import numpy as np

# Importa o seu módulo. Certifique-se de que o arquivo se chama persistencia.py
import persistencia

# ===========================================================================
# FIXTURE: PREPARAÇÃO DO AMBIENTE DE TESTES
# ===========================================================================
@pytest.fixture(autouse=True)
def configurar_ambiente_temporario(tmp_path, monkeypatch):
    """
    Esta fixture roda automaticamente antes de CADA teste.
    Ela altera as variáveis globais do módulo persistencia para que ele
    leia e grave arquivos em uma pasta temporária do sistema, evitando
    poluir ou deletar os dados reais do seu projeto.
    """
    arquivo_estado_temp = tmp_path / "state_teste.json"
    diretorio_dados_temp = tmp_path / "data_teste"

    monkeypatch.setattr(persistencia, "STATE_FILE", str(arquivo_estado_temp))
    monkeypatch.setattr(persistencia, "DATA_DIR", str(diretorio_dados_temp))
    
    return tmp_path

# ===========================================================================
# TESTES DA MÁQUINA DE ESTADOS E LEITURA/GRAVAÇÃO DO JSON
# ===========================================================================

def test_carregar_estado_arquivo_inexistente():
    """Se o state.json não existe, deve retornar o estado inicial (vazio)."""
    estado = persistencia.carregar_estado()
    assert estado["state"] == persistencia.ETAPA_INICIAL
    assert estado["uf"] is None
    assert estado["files"] == {}

def test_salvar_e_carregar_estado():
    """Garante que salvar um estado no disco e carregá-lo traz os mesmos dados."""
    estado_base = persistencia.resetar_estado()
    estado_base["uf"] = "RJ"
    estado_base["elevacao"] = 5
    estado_base["state"] = persistencia.ETAPA_TERRENO

    persistencia.salvar_estado(estado_base)
    
    estado_carregado = persistencia.carregar_estado()
    assert estado_carregado["uf"] == "RJ"
    assert estado_carregado["elevacao"] == 5
    assert estado_carregado["state"] == persistencia.ETAPA_TERRENO

def test_carregar_estado_json_corrompido(tmp_path):
    """Testa a resiliência do código se o state.json estiver corrompido."""
    # Cria um arquivo JSON com sintaxe inválida
    arquivo = tmp_path / "state_teste.json"
    arquivo.write_text("{ isso_nao_e_um_json_valido }")

    # A função deve ignorar o erro, printar um aviso e retornar estado vazio
    estado = persistencia.carregar_estado()
    assert estado["state"] == persistencia.ETAPA_INICIAL

def test_resetar_estado():
    """Garante que o reset exclui o arquivo e zera os dados."""
    estado = persistencia.resetar_estado()
    estado["uf"] = "SP"
    persistencia.salvar_estado(estado)
    
    # Verifica se o arquivo foi criado
    assert os.path.exists(persistencia.STATE_FILE)
    
    # Reseta
    estado_resetado = persistencia.resetar_estado()
    assert not os.path.exists(persistencia.STATE_FILE)
    assert estado_resetado["uf"] is None

# ===========================================================================
# TESTES DE I/O DE ARQUIVOS (.NPY E .PKL)
# ===========================================================================

def test_salvar_e_carregar_arquivo_npy(tmp_path):
    """Testa salvar e ler matrizes do numpy (.npy)."""
    caminho = str(tmp_path / "matriz.npy")
    matriz_original = np.array([[1, 2], [3, 4]])
    
    persistencia.salvar_arquivo(caminho, matriz_original)
    assert os.path.exists(caminho)
    
    matriz_carregada = persistencia._carregar_arquivo(caminho)
    np.testing.assert_array_equal(matriz_original, matriz_carregada)

def test_salvar_arquivo_npy_com_tipo_errado(tmp_path):
    """O sistema deve barrar a tentativa de salvar um dict em um .npy"""
    caminho = str(tmp_path / "erro.npy")
    dado_invalido = {"chave": "valor"}
    
    # O pytest verifica se a exceção TypeError foi levantada
    with pytest.raises(TypeError, match="exige np.ndarray"):
        persistencia.salvar_arquivo(caminho, dado_invalido)

def test_salvar_arquivo_extensao_nao_suportada(tmp_path):
    """O sistema deve rejeitar extensões diferentes de .npy e .pkl"""
    caminho = str(tmp_path / "arquivo.txt")
    
    with pytest.raises(ValueError, match="Extensão não suportada"):
        persistencia.salvar_arquivo(caminho, [1, 2, 3])

def test_carregar_arquivo_inexistente(tmp_path):
    """Tentar carregar um arquivo que não existe deve retornar None."""
    caminho = str(tmp_path / "fantasma.pkl")
    resultado = persistencia._carregar_arquivo(caminho)
    assert resultado is None

# ===========================================================================
# TESTES DE INTEGRAÇÃO (AVANÇAR ETAPA E CARREGAR LOTE)
# ===========================================================================

def test_avancar_etapa_com_arquivos_e_metadados():
    """Testa a função central de avanço do simulador empacotando dados."""
    estado = persistencia.resetar_estado()
    
    raster_mock = np.array([[10, 10], [10, 10]])
    dicionario_mock = {"config": "teste"}
    
    arquivos = {
        "raster_isolado": raster_mock,
        "config_extra": dicionario_mock
    }
    metadados = {
        "area_inundada": 400
    }
    
    # Simula o avanço para a etapa 1
    novo_estado = persistencia.avancar_etapa(
        estado, 
        nova_etapa=persistencia.ETAPA_TERRENO,
        novos_arquivos=arquivos,
        novos_metadados=metadados
    )
    
    # Valida o estado atualizado na RAM
    assert novo_estado["state"] == persistencia.ETAPA_TERRENO
    assert novo_estado["metadata"]["area_inundada"] == 400
    assert "raster_isolado" in novo_estado["files"]
    assert "config_extra" in novo_estado["files"]
    
    # Verifica no disco se os arquivos ganharam as extensões corretas
    assert novo_estado["files"]["raster_isolado"].endswith(".npy")
    assert novo_estado["files"]["config_extra"].endswith(".pkl")
    assert os.path.exists(novo_estado["files"]["raster_isolado"])
    assert os.path.exists(novo_estado["files"]["config_extra"])

def test_carregar_dados_salvos():
    """Testa a leitura em lote na inicialização da main."""
    estado = persistencia.resetar_estado()
    raster_mock = np.array([[5, 5], [5, 5]])
    
    # Salva um estado com dados
    estado = persistencia.avancar_etapa(
        estado,
        nova_etapa=1,
        novos_arquivos={"raster_isolado": raster_mock},
        novos_metadados={"xy_fonte": 2}
    )
    
    # Faz o carregamento em lote
    dados_carregados = persistencia.carregar_dados_salvos(estado)
    
    assert "raster_isolado" in dados_carregados
    assert "_metadata" in dados_carregados
    assert dados_carregados["_metadata"]["xy_fonte"] == 2
    np.testing.assert_array_equal(dados_carregados["raster_isolado"], raster_mock)