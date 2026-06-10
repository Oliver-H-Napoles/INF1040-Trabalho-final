"""
persistencia.py
---------------
Gerencia a persistência de dados entre execuções do simulador de enchentes.

Estrutura do state.json:
{
  "state": <int>,        -- última etapa concluída (0 = nenhuma)
  "uf": <str>,           -- UF da última execução
  "elevacao": <int>,     -- elevação usada na última execução
  "files": {
    "raster_isolado":    "data/persistencia/raster_isolado.npy",
    "mascara_agua":      "data/persistencia/mascara_agua.npy",
    "xy_fonte":          (guardado em metadata, não arquivo)
  },
  "metadata": {
    "xy_fonte": <int>,   -- canto da nascente
    "area_inundada": <int>
  }
}

Etapas do simulador:
  0 -- nenhuma etapa concluída (primeira execução ou reset)
  1 -- terreno carregado (raster_isolado disponível)
  2 -- máscara criada (mascara_agua disponível)
  3 -- simulação concluída (area_inundada disponível)
"""

import json
import os
import pickle
import numpy as np
from typing import Any

from agua import carrega_dados

__all__ = [
    "carregar_estado",
    "salvar_estado",
    "avancar_etapa",
    "carregar_dados_salvos",
    "salvar_arquivo",
    "resetar_estado",
    "ETAPA_INICIAL",
    "ETAPA_TERRENO",
    "ETAPA_MASCARA",
    "ETAPA_SIMULACAO",
]

# ---------------------------------------------------------------------------
# Constantes de etapa — usadas na main para comparar state
# ---------------------------------------------------------------------------
ETAPA_INICIAL   = 0   # nenhuma etapa concluída
ETAPA_TERRENO   = 1   # raster_isolado disponível
ETAPA_MASCARA   = 2   # mascara_agua disponível
ETAPA_SIMULACAO = 3   # simulação concluída

STATE_FILE   = "state.json"
DATA_DIR     = os.path.join("data", "persistencia")

_ESTADO_VAZIO: dict = {
    "state":    ETAPA_INICIAL,
    "uf":       None,
    "elevacao": None,
    "files":    {},
    "metadata": {},
}


# ---------------------------------------------------------------------------
# Leitura e gravação do state.json
# ---------------------------------------------------------------------------

def carregar_estado() -> dict:
    """
    Lê o arquivo state.json do disco e retorna o dicionário de estado.
    Se o arquivo não existir ou estiver corrompido, retorna um estado vazio.

    Assertiva de entrada (Pré-condição):
    - Nenhuma restrição. O método lida de forma segura com a ausência do arquivo.

    Assertiva de saída (Pós-condição):
    - Sempre retorna um dicionário válido contendo as chaves obrigatórias:
      'state', 'uf', 'elevacao', 'files', 'metadata'.

    @return: Dicionário contendo o estado atual do simulador.
    """
    if not os.path.exists(STATE_FILE):
        return _estado_vazio()
    
    carrega_dados(os.path.abspath(STATE_FILE))

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            estado = json.load(f)
        # garante chaves obrigatórias mesmo em arquivos de versões antigas
        estado.setdefault("state",    ETAPA_INICIAL)
        estado.setdefault("uf",       None)
        estado.setdefault("elevacao", None)
        estado.setdefault("files",    {})
        estado.setdefault("metadata", {})
        return estado

    except (json.JSONDecodeError, IOError) as erro:
        print(f"[persistencia] Aviso: state.json inválido ({erro}). Iniciando do zero.")
        return _estado_vazio()


def salvar_estado(estado: dict) -> None:
    """
    Grava o dicionário de estado no arquivo state.json de forma atômica.
    Usa arquivo temporário + rename para evitar corrupção em caso de queda de energia ou falha.

    Assertiva de entrada (Pré-condição):
    - 'estado' deve ser um dicionário (dict) cujos valores internos sejam serializáveis em JSON.

    Assertiva de saída (Pós-condição):
    - O arquivo state.json no disco reflete exatamente o conteúdo de 'estado' após a chamada.

    @param estado: Dicionário contendo os dados e rastreio de arquivos do simulador.
    @return: None
    """
    os.makedirs(os.path.dirname(STATE_FILE) if os.path.dirname(STATE_FILE) else ".", exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_FILE)  # atômico no Linux/Windows


# ---------------------------------------------------------------------------
# Avanço de etapa (combina salvar arquivo + atualizar estado)
# ---------------------------------------------------------------------------

def avancar_etapa(
    estado: dict,
    nova_etapa: int,
    novos_arquivos: dict[str, Any] | None = None,
    novos_metadados: dict[str, Any] | None = None,
) -> dict:
    """
    Persiste os dados de uma etapa recém-concluída e avança o contador de estado.

    Fluxo interno:
      1. Salva cada dado em `novos_arquivos` no disco (numpy ou pickle).
      2. Registra os caminhos no estado["files"].
      3. Registra escalares em estado["metadata"].
      4. Atualiza estado["state"] para `nova_etapa`.
      5. Grava state.json.

    Assertiva de entrada (Pré-condição):
    - 'nova_etapa' deve ser >= estado["state"] (avanço progressivo).
    - Os valores em 'novos_arquivos' devem ser np.ndarray (→ salvos em .npy) ou objetos
      serializáveis nativamente (→ salvos em .pkl).

    Assertiva de saída (Pós-condição):
    - Todos os arquivos informados no dicionário de entrada foram gravados em DATA_DIR.
    - O arquivo state.json foi atualizado com os novos caminhos e metadados.
    - Retorna o estado atualizado para uso imediato na memória.

    @param estado:          Dicionário de estado atual, retornado por carregar_estado().
    @param nova_etapa:      Novo valor inteiro para estado["state"].
    @param novos_arquivos:  Dicionário {nome_chave: dado} contendo dados pesados para arquivo.
    @param novos_metadados: Dicionário {nome_chave: valor} contendo escalares para o JSON.
    @return:                Dicionário de estado atualizado.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if novos_arquivos:
        for chave, dado in novos_arquivos.items():
            ext     = ".npy" if isinstance(dado, np.ndarray) else ".pkl"
            caminho = os.path.join(DATA_DIR, chave + ext)
            salvar_arquivo(caminho, dado)
            estado["files"][chave] = caminho
            print(f"[persistencia] '{chave}' salvo em '{caminho}'")

    if novos_metadados:
        estado["metadata"].update(novos_metadados)

    estado["state"] = nova_etapa
    salvar_estado(estado)
    print(f"[persistencia] Etapa avançada para {nova_etapa}.")
    return estado


# ---------------------------------------------------------------------------
# Carregamento em lote (chamado na inicialização da main)
# ---------------------------------------------------------------------------

def carregar_dados_salvos(estado: dict) -> dict:
    """
    Carrega do disco todos os arquivos (matrizes e dados pesados) registrados no estado.

    Assertiva de entrada (Pré-condição):
    - 'estado' deve ser um dicionário válido retornado por carregar_estado(), 
      contendo a chave 'files'.

    Assertiva de saída (Pós-condição):
    - As chaves do dicionário retornado correspondem exatamente às chaves registradas em
      estado["files"], acrescido da chave "_metadata".
    - Se um arquivo registrado não existir fisicamente no disco, seu valor será None.

    @param estado: Dicionário contendo o mapeamento de arquivos e metadados.
    @return:       Dicionário {chave: dado_carregado} com todos os dados persistidos.
    """
    dados: dict = {}
    for chave, caminho in estado["files"].items():
        dados[chave] = _carregar_arquivo(caminho)

    dados["_metadata"] = estado.get("metadata", {})
    return dados

def salvar_arquivo(caminho: str, dado: Any) -> None:
    """
    Salva 'dado' no caminho indicado baseando-se na extensão do arquivo.
    - np.ndarray → formato .npy (binário compacto, otimizado para matrizes).
    - qualquer outro objeto Python → .pkl (pickle genérico).

    Assertiva de entrada (Pré-condição):
    - O argumento 'caminho' deve ser uma string terminada em .npy ou .pkl.
    - Se o caminho for .npy, 'dado' deve ser obrigatoriamente uma matriz NumPy.

    Assertiva de saída (Pós-condição):
    - O arquivo especificado passa a existir fisicamente no disco com os dados fornecidos.

    @param caminho: String com o caminho completo de destino do arquivo.
    @param dado:    O objeto em memória a ser persistido.
    @return:        None
    @raises TypeError:  Se o caminho for .npy mas o dado não for um np.ndarray.
    @raises ValueError: Se a extensão do arquivo não for nem .npy nem .pkl.
    """
    os.makedirs(os.path.dirname(caminho) if os.path.dirname(caminho) else ".", exist_ok=True)

    if caminho.endswith(".npy"):
        if not isinstance(dado, np.ndarray):
            raise TypeError(f"[persistencia] .npy exige np.ndarray, recebeu {type(dado)}")
        np.save(caminho, dado)

    elif caminho.endswith(".pkl"):
        with open(caminho, "wb") as f:
            pickle.dump(dado, f)

    else:
        raise ValueError(
            f"[persistencia] Extensão não suportada: '{caminho}'. Use .npy ou .pkl."
        )


def _carregar_arquivo(caminho: str) -> Any:
    """
    Carrega o conteúdo de um arquivo (.npy ou .pkl) armazenado no disco.

    Assertiva de entrada (Pré-condição):
    - 'caminho' deve ser uma string terminando em .npy ou .pkl.

    Assertiva de saída (Pós-condição):
    - Retorna o conteúdo original do arquivo desserializado.
    - Se o arquivo for inexistente no disco, retorna None de forma segura.

    @param caminho: Caminho completo para o arquivo a ser lido.
    @return:        O dado carregado (np.ndarray, dict, list, etc.) ou None em caso de ausência.
    @raises ValueError: Se a extensão do arquivo fornecido for desconhecida.
    """
    if not os.path.exists(caminho):
        print(f"[persistencia] Aviso: '{caminho}' registrado mas ausente no disco.")
        return None

    if caminho.endswith(".npy"):
        return np.load(caminho, allow_pickle=False)

    if caminho.endswith(".pkl"):
        with open(caminho, "rb") as f:
            return pickle.load(f)

    raise ValueError(f"[persistencia] Extensão não suportada: '{caminho}'.")

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def resetar_estado() -> dict:
    """
    Remove o arquivo state.json do disco e restaura as configurações iniciais.
    Útil para reiniciar a simulação do zero (ex: quando há troca da UF base).

    Assertiva de entrada (Pré-condição):
    - Nenhuma. O método lida com arquivos inexistentes sem gerar exceções.

    Assertiva de saída (Pós-condição):
    - O arquivo state.json garante não existir após a chamada.
    - O retorno é um dicionário limpo com state == ETAPA_INICIAL.

    @return: Dicionário contendo o estado vazio.
    """
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print("[persistencia] Estado resetado.")
    return _estado_vazio()


def _estado_vazio() -> dict:
    """
    Gera uma cópia independente do dicionário de estado inicial.

    Assertiva de entrada (Pré-condição):
    - Nenhuma.
    
    Assertiva de saída (Pós-condição):
    - Retorna um dicionário que não compartilha referências de memória com a 
      constante original (_ESTADO_VAZIO), prevenindo mutações indesejadas (side-effects).

    @return: Dicionário novo com a estrutura base de estado.
    """
    import copy
    return copy.deepcopy(_ESTADO_VAZIO)