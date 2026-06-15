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
    "mascara_agua":      "data/persistencia/mascara_agua.npy"
  },
  "metadata": {
    "xy_fonte": <int>,   -- canto da nascente
    "area_inundada": <int>,
    "elevacao_simulada": <int>
  }
}
"""

import json
import os
import pickle
import numpy as np
from typing import Any

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
    "obter_etapa_atual",
    "obter_uf_salva",
    "obter_elevacao_salva",
    "obter_metadado",
    "definir_parametros_base",
    "obter_dado_carregado",
    "obter_metadado_carregado"
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
    """
    if not os.path.exists(STATE_FILE):
        return _estado_vazio()
    
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
    """
    os.makedirs(os.path.dirname(STATE_FILE) if os.path.dirname(STATE_FILE) else ".", exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_FILE)  


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
    """
    dados: dict = {}
    for chave, caminho in estado["files"].items():
        dados[chave] = _carregar_arquivo(caminho)

    dados["_metadata"] = estado.get("metadata", {})
    return dados

def salvar_arquivo(caminho: str, dado: Any) -> None:
    """
    Salva 'dado' no caminho indicado baseando-se na extensão do arquivo.
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
        raise ValueError(f"[persistencia] Extensão não suportada: '{caminho}'. Use .npy ou .pkl.")


def _carregar_arquivo(caminho: str) -> Any:
    """
    Carrega o conteúdo de um arquivo (.npy ou .pkl) armazenado no disco.
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
    """
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print("[persistencia] Estado resetado.")
    return _estado_vazio()


def _estado_vazio() -> dict:
    """
    Gera uma cópia independente do dicionário de estado inicial.
    """
    import copy
    return copy.deepcopy(_ESTADO_VAZIO)

# ---------------------------------------------------------------------------
# Funções de Acesso (Encapsulamento do TAD)
# ---------------------------------------------------------------------------

def obter_etapa_atual(estado: dict) -> int:
    """
    Retorna a etapa atual salva no estado.

    Assertiva de entrada (Pré-condição):
    - 'estado' deve ser um dicionário instanciado correspondente à estrutura do TAD.

    Assertiva de saída (Pós-condição):
    - Retorna um inteiro representando o nível de avanço da simulação.
    - Se a chave 'state' não existir, retorna a constante ETAPA_INICIAL (0).
    - O dicionário original não sofre nenhuma mutação.

    @param estado: Dicionário de estado atual.
    @return: Inteiro representando a etapa atual.
    """
    return estado.get("state", ETAPA_INICIAL)

def obter_uf_salva(estado: dict) -> str | None:
    """
    Retorna a UF armazenada no estado.

    Assertiva de entrada (Pré-condição):
    - 'estado' deve ser um dicionário válido do TAD.

    Assertiva de saída (Pós-condição):
    - Retorna a string da UF salva na última execução, ou None se for a primeira execução/reset.
    - O dicionário original não é alterado.

    @param estado: Dicionário de estado atual.
    @return: String contendo a UF ou None.
    """
    return estado.get("uf")

def obter_elevacao_salva(estado: dict) -> int | None:
    """
    Retorna a elevação armazenada no estado.

    Assertiva de entrada (Pré-condição):
    - 'estado' deve ser um dicionário válido do TAD.

    Assertiva de saída (Pós-condição):
    - Retorna o valor inteiro da elevação alvo da última execução, ou None se inexistente.
    - O estado original não sofre alteração de valores.

    @param estado: Dicionário de estado atual.
    @return: Inteiro contendo a elevação simulada ou None.
    """
    return estado.get("elevacao")

def obter_metadado(estado: dict, chave: str, padrao: Any = None) -> Any:
    """
    Recupera um valor específico do dicionário de metadados do estado.

    Assertiva de entrada (Pré-condição):
    - 'estado' deve ser um dicionário contendo preferencialmente a chave 'metadata'.
    - 'chave' deve ser uma string referenciando a variável desejada (ex: 'area_inundada').

    Assertiva de saída (Pós-condição):
    - Retorna o valor exato mapeado pela chave no submódulo de metadados.
    - Retorna o valor de 'padrao' se a chave ou o próprio submódulo 'metadata' não existirem.
    - Leitura limpa: nenhuma modificação é feita na estrutura.

    @param estado: Dicionário de estado atual.
    @param chave: String com o nome do metadado.
    @param padrao: Valor retornado caso a chave não exista.
    @return: Valor do metadado.
    """
    return estado.get("metadata", {}).get(chave, padrao)

def definir_parametros_base(estado: dict, uf: str, elevacao: int) -> None:
    """
    Atualiza a UF e elevação no estado atual.

    Assertiva de entrada (Pré-condição):
    - 'estado' deve ser um dicionário mutável.
    - 'uf' deve ser uma string validada da Unidade Federativa.
    - 'elevacao' deve ser um inteiro válido representando o nível do mar.

    Assertiva de saída (Pós-condição):
    - O dicionário 'estado' sofre mutação (in-place).
    - As chaves "uf" e "elevacao" no topo da hierarquia do estado passam a apontar para os novos valores.

    @param estado: Dicionário de estado atual.
    @param uf: String com a sigla da UF.
    @param elevacao: Inteiro da elevação.
    """
    estado["uf"] = uf
    estado["elevacao"] = elevacao

def obter_dado_carregado(dados: dict, chave: str) -> Any:
    """
    Retorna um dado pesado carregado do disco (ex: raster_isolado).

    Assertiva de entrada (Pré-condição):
    - 'dados' deve ser um dicionário resultante da função carregar_dados_salvos().
    - 'chave' deve ser uma string válida correspondente ao nome de um arquivo mapeado.

    Assertiva de saída (Pós-condição):
    - Retorna o objeto alocado em memória (geralmente np.ndarray) referenciado pela chave.
    - Retorna None caso a chave não tenha sido carregada.
    - Nenhuma operação de I/O de disco é realizada nesta função (apenas consulta em memória).

    @param dados: Dicionário de dados carregados do disco.
    @param chave: String com o nome do dado.
    @return: Objeto carregado ou None.
    """
    return dados.get(chave)

def obter_metadado_carregado(dados: dict, chave: str) -> Any:
    """
    Retorna um metadado que foi carregado junto com os dados.

    Assertiva de entrada (Pré-condição):
    - 'dados' deve ser um dicionário resultante da leitura dos dados persistidos.
    - 'chave' deve ser uma string procurando um dado escalar isolado.

    Assertiva de saída (Pós-condição):
    - Busca e retorna o valor contido na sub-chave '_metadata' referenciada por 'chave'.
    - Retorna None se a hierarquia '_metadata' ou a 'chave' não existirem.

    @param dados: Dicionário de dados carregados.
    @param chave: String com o nome do metadado.
    @return: Valor do metadado ou None.
    """
    return dados.get("_metadata", {}).get(chave)