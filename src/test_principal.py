"""
Testes unitários do Módulo Principal.

Convenção de saídas validada por estes testes:
    - obter_elevacao (produtora): retorna int em caso de êxito e levanta
      ValueError para entrada não-inteira;
    - main (ação -> int): 0 êxito; 1 UF inválida; 2 elevação inválida;
      3 falha no terreno; 4 falha na simulação da água.

Mock: `input()` é substituído para simular a digitação do usuário e todas as
dependências de outros módulos (incluindo as funções de acesso do TAD) são dubladas, 
isolando o fluxo de orquestração.
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import principal

# =============================================================================
# obter_elevacao  (produtora -> int | ValueError)
# =============================================================================

def test_obter_elevacao_ok_inteiro():
    """Usuário digita '42' -> retorna o inteiro 42."""
    with patch("builtins.input", return_value="42"):
        assert principal.obter_elevacao() == 42


def test_obter_elevacao_erro_entrada_nao_inteira():
    """Usuário digita 'abc' (não-inteiro) -> levanta ValueError."""
    with patch("builtins.input", return_value="abc"):
        with pytest.raises(ValueError):
            principal.obter_elevacao()


# =============================================================================
# main  (ação -> int)
# =============================================================================

def _dependencias_ok():
    """Conjunto de dublês que representa um fluxo bem-sucedido de ponta a ponta."""
    return dict(
        valida_uf=MagicMock(return_value=0),
        obter_elevacao=MagicMock(return_value=5),
        valida_elevacao=MagicMock(return_value=0),
        isolar_estado=MagicMock(return_value=np.zeros((3, 3))),
        cria_mascara_agua=MagicMock(return_value=np.zeros((3, 3))),
        expandir_mascara_agua=MagicMock(return_value=100),
        projetar_camadas=MagicMock(return_value=0),
        gerar_heatmap=MagicMock(return_value=MagicMock()),
        plot_layers=MagicMock(return_value=0),

        # Dublês estruturais da persistência
        carregar_estado=MagicMock(return_value={"mock": "estado_vazio"}),
        carregar_dados_salvos=MagicMock(return_value={"mock": "dados_vazios"}),
        avancar_etapa=MagicMock(),
        resetar_estado=MagicMock(return_value={"mock": "estado_resetado"}),

        # Dublês das novas funções de acesso do TAD
        obter_etapa_atual=MagicMock(return_value=0),
        obter_uf_salva=MagicMock(return_value=None),
        obter_elevacao_salva=MagicMock(return_value=None),
        obter_metadado=MagicMock(return_value=None),
        obter_dado_carregado=MagicMock(return_value=None),
        obter_metadado_carregado=MagicMock(return_value=None),
        definir_parametros_base=MagicMock(),
    )


def test_main_ok_fluxo_completo():
    """Todas as etapas bem-sucedidas -> 0 (êxito)."""
    with patch.multiple(principal, **_dependencias_ok()):
        assert principal.main("RS") == 0


def test_main_erro_uf_invalida():
    """valida_uf reprova a UF -> 1 (UF inválida)."""
    deps = _dependencias_ok()
    deps["valida_uf"] = MagicMock(return_value=1)
    with patch.multiple(principal, **deps):
        assert principal.main("ZZ") == 1


def test_main_erro_elevacao_nao_inteira():
    """obter_elevacao levanta ValueError -> 2 (elevação inválida)."""
    deps = _dependencias_ok()
    deps["obter_elevacao"] = MagicMock(side_effect=ValueError("apenas inteiros"))
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 2


def test_main_erro_elevacao_invalida():
    """valida_elevacao reprova o valor -> 2 (elevação inválida)."""
    deps = _dependencias_ok()
    deps["obter_elevacao"] = MagicMock(return_value=-5)
    deps["valida_elevacao"] = MagicMock(return_value=1)
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 2


def test_main_erro_falha_no_terreno():
    """isolar_estado retorna None -> 3 (falha no terreno)."""
    deps = _dependencias_ok()
    deps["isolar_estado"] = MagicMock(return_value=None)
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 3


def test_main_erro_falha_ao_criar_mascara():
    """cria_mascara_agua retorna None -> 4 (falha na simulação da água)."""
    deps = _dependencias_ok()
    
    # Em vez de criar um mock novo, alteramos o retorno do mock que já existe!
    deps["cria_mascara_agua"].return_value = None
    
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 4


def test_main_erro_falha_ao_expandir_mascara():
    """expandir_mascara_agua retorna None -> 4 (falha na simulação da água)."""
    deps = _dependencias_ok()
    deps["expandir_mascara_agua"] = MagicMock(return_value=None)
    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 4

# =============================================================================
# Testes da Máquina de Estados (Orquestração da Persistência)
# =============================================================================

def test_main_ok_pula_etapa_terreno_se_estado_avancado():
    """
    Se a função obter_etapa_atual indicar que a Etapa 1 (terreno) já foi feita,
    a função isolar_estado NÃO deve ser chamada novamente.
    """
    deps = _dependencias_ok()
    
    # Simulamos via Getters que o programa já rodou antes para o 'RS' e parou na etapa 1
    deps["obter_etapa_atual"] = MagicMock(return_value=1)
    deps["obter_uf_salva"] = MagicMock(return_value="RS")
    deps["obter_elevacao_salva"] = MagicMock(return_value=5)
    
    # Simulamos o carregamento da matriz que já estaria no disco
    def mock_obter_dado(dados, chave):
        if chave == "raster_isolado":
            return np.zeros((3, 3))
        return None
        
    deps["obter_dado_carregado"] = MagicMock(side_effect=mock_obter_dado)

    with patch.multiple(principal, **deps):
        assert principal.main("RS") == 0
        
        # A PROVA: O módulo de terreno não foi acionado, economizando processamento!
        deps["isolar_estado"].assert_not_called()


def test_main_ok_reseta_estado_se_uf_diferente():
    """
    Se a UF salva (ex: RJ) for diferente da UF atual (ex: RS),
    o programa deve chamar resetar_estado() para começar do zero.
    """
    deps = _dependencias_ok()
    
    # O side_effect envia 2 na primeira vez (início da main) e 0 na segunda (após o reset)
    deps["obter_etapa_atual"] = MagicMock(side_effect=[2, 0])
    deps["obter_uf_salva"] = MagicMock(return_value="RJ")
    deps["obter_elevacao_salva"] = MagicMock(return_value=5)

    with patch.multiple(principal, **deps):
        # O usuário agora digitou RS
        assert principal.main("RS") == 0
        
        # A PROVA: O orquestrador percebeu a mudança e mandou limpar tudo!
        deps["resetar_estado"].assert_called_once()
        
        # Como o estado foi resetado, ele teve que recalcular o terreno do zero
        deps["isolar_estado"].assert_called_once()