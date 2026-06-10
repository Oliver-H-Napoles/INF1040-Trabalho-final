"""
Testes unitários do Módulo Terreno.

Convenção de saídas validada por estes testes (funções produtoras):
    - êxito -> retorna o objeto (tupla de caminhos, raster, polígono ou matriz);
    - falha esperada -> retorna `None` (ou `(None, None)` nas funções que
      devolvem tupla). Nenhuma função levanta exceção para erros previsíveis.

Mocks: todo o I/O (leitura de JSON, rasters via `rasterio` e shapefiles via
`shapefile`/`features`) é substituído por dublês, de modo que os testes não
dependem dos arquivos reais em `data/` nem do diretório de execução.
"""
from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pytest

import terreno.terreno as terreno
from terreno import (
    obter_caminhos_arquivos,
    carregar_dados_topograficos,
    carregar_fronteiras,
    aplicar_mascara_isolamento,
    isolar_estado,
    _arquivos_carregados,
)


@pytest.fixture(autouse=True)
def limpar_cache():
    """Limpa o cache encapsulado do módulo antes de cada teste."""
    _arquivos_carregados["rasters"].clear()
    _arquivos_carregados["poligonos"].clear()
    _arquivos_carregados["raster_delimitados"].clear()
    yield


def _context_manager(valor_entrada):
    """Cria um MagicMock que funciona como gerenciador de contexto (`with`)."""
    cm = MagicMock()
    cm.__enter__.return_value = valor_entrada
    cm.__exit__.return_value = False
    return cm


# =============================================================================
# obter_caminhos_arquivos  (-> (str, str) | (None, None))
# =============================================================================

def test_obter_caminhos_ok_uf_valida():
    """UF presente no JSON -> tupla com os caminhos de topo e fronteira."""
    mapa = {"RS": {"arquivo_topo": "RS_mosaico.tif", "arquivo_front": "front_RS.shp"}}
    with patch("builtins.open", mock_open()), \
            patch.object(terreno.json, "load", return_value=mapa):
        topo, front = obter_caminhos_arquivos("RS")

    assert topo == "data/RS_mosaico.tif"
    assert front == "data/front_RS.shp"


def test_obter_caminhos_ok_normaliza_uf():
    """UF com espaços/minúsculas ('  rs ') é normalizada -> caminho correto."""
    mapa = {"RS": {"arquivo_topo": "RS_mosaico.tif", "arquivo_front": "front_RS.shp"}}
    with patch("builtins.open", mock_open()), \
            patch.object(terreno.json, "load", return_value=mapa):
        topo, front = obter_caminhos_arquivos("  rs ")

    assert topo == "data/RS_mosaico.tif"


def test_obter_caminhos_erro_uf_ausente():
    """UF ausente do JSON ('XX') -> (None, None)."""
    with patch("builtins.open", mock_open()), \
            patch.object(terreno.json, "load", return_value={}):
        assert obter_caminhos_arquivos("XX") == (None, None)


def test_obter_caminhos_erro_arquivo_json_inexistente():
    """Falha ao abrir o estados.json -> (None, None)."""
    with patch("builtins.open", side_effect=OSError("sem estados.json")):
        assert obter_caminhos_arquivos("RS") == (None, None)


# =============================================================================
# carregar_dados_topograficos  (-> (ndarray, transform) | (None, None))
# =============================================================================

def test_carregar_topografico_ok_arquivo_integro():
    """Raster íntegro (mock) -> tupla (matriz, transform) e cache preenchido."""
    raster_fake = np.array([[1.0, 2.0], [3.0, 4.0]])
    dataset = MagicMock()
    dataset.read.return_value = raster_fake
    dataset.transform = "TRANSFORM_FAKE"

    with patch.object(terreno.rasterio, "open", return_value=_context_manager(dataset)):
        raster, transform = carregar_dados_topograficos("qualquer.tif")

    assert np.array_equal(raster, raster_fake)
    assert transform == "TRANSFORM_FAKE"
    # O resultado deve ter sido encapsulado no cache.
    assert len(_arquivos_carregados["rasters"]) == 1


def test_carregar_topografico_erro_arquivo_invalido():
    """Erro ao abrir o raster (corrompido/inexistente) -> (None, None)."""
    with patch.object(terreno.rasterio, "open", side_effect=Exception("corrompido")):
        assert carregar_dados_topograficos("falso.tif") == (None, None)


# =============================================================================
# carregar_fronteiras  (-> poligono | None)
# =============================================================================

def test_carregar_fronteiras_ok_uf_encontrada():
    """UF presente na tabela do shapefile -> polígono correspondente e cache."""
    poligono_fake = MagicMock(name="poligono")
    sf = MagicMock()
    sf.records.return_value = [["0", "Sao Paulo", "SP"], ["1", "Rio Grande do Sul", "RS"]]
    sf.shape.return_value = poligono_fake

    with patch.object(terreno.shapefile, "Reader", return_value=_context_manager(sf)):
        resultado = carregar_fronteiras("front_RS.shp", "RS")

    assert resultado is poligono_fake
    sf.shape.assert_called_once_with(1)
    assert len(_arquivos_carregados["poligonos"]) == 1


def test_carregar_fronteiras_erro_uf_ausente_na_tabela():
    """UF não encontrada na tabela do shapefile -> None."""
    sf = MagicMock()
    sf.records.return_value = [["0", "Sao Paulo", "SP"]]

    with patch.object(terreno.shapefile, "Reader", return_value=_context_manager(sf)):
        assert carregar_fronteiras("front_RS.shp", "RS") is None


def test_carregar_fronteiras_erro_arquivo_invalido():
    """Erro ao abrir o shapefile (formato/caminho inválido) -> None."""
    with patch.object(terreno.shapefile, "Reader", side_effect=Exception("nao e shapefile")):
        assert carregar_fronteiras("falso.shp", "RS") is None


# =============================================================================
# aplicar_mascara_isolamento  (-> ndarray | None)
# =============================================================================

def test_aplicar_mascara_ok_aplica_barreira():
    """Polígono válido -> matriz com barreira (10000) fora e dados preservados dentro."""
    raster = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    poligono = MagicMock()
    poligono.__geo_interface__ = {"type": "Polygon", "coordinates": []}

    # 1ª chamada: máscara do estado (True = fora do estado -> vira barreira).
    mascara_estado = np.array([[True, False, False],
                               [False, False, False],
                               [False, False, False]])
    # 2ª chamada: máscara do mar (nenhuma célula é mar neste cenário).
    mascara_mar = np.zeros((3, 3), dtype=bool)

    coastline_sf = MagicMock()
    coastline_sf.shapes.return_value = [MagicMock(__geo_interface__={"type": "Polygon"})]

    with patch.object(terreno.features, "geometry_mask",
                      side_effect=[mascara_estado, mascara_mar]), \
            patch.object(terreno.shapefile, "Reader",
                         return_value=_context_manager(coastline_sf)):
        resultado = aplicar_mascara_isolamento(raster, poligono, "TRANSFORM")

    assert resultado is not None
    # A célula externa ao estado deve ter virado barreira (10000).
    assert resultado[0][0] == 10000
    # As células internas preservam o valor original.
    assert resultado[1][1] == 5.0


def test_aplicar_mascara_erro_falha_geometria():
    """Falha no cálculo da geometria (geometry_mask) -> None."""
    raster = np.array([[1.0, 2.0], [3.0, 4.0]])
    poligono = MagicMock()
    poligono.__geo_interface__ = {"type": "Polygon"}

    with patch.object(terreno.features, "geometry_mask", side_effect=Exception("erro geo")):
        assert aplicar_mascara_isolamento(raster, poligono, "TRANSFORM") is None


# =============================================================================
# isolar_estado  (orquestração -> ndarray | None)
# =============================================================================

def test_isolar_estado_ok_fluxo_completo():
    """Todas as etapas bem-sucedidas -> matriz isolada final."""
    matriz_final = np.array([[10000, 1.0], [2.0, -1.0]])
    with patch.object(terreno, "obter_caminhos_arquivos", return_value=("t.tif", "f.shp")), \
            patch.object(terreno, "carregar_dados_topograficos", return_value=(np.zeros((2, 2)), "TR")), \
            patch.object(terreno, "carregar_fronteiras", return_value=MagicMock()), \
            patch.object(terreno, "aplicar_mascara_isolamento", return_value=matriz_final):
        resultado = isolar_estado("RS")

    assert np.array_equal(resultado, matriz_final)


def test_isolar_estado_erro_falha_nos_caminhos():
    """Falha ao obter caminhos (UF inexistente) -> None (curto-circuito)."""
    with patch.object(terreno, "obter_caminhos_arquivos", return_value=(None, None)):
        assert isolar_estado("XX") is None


def test_isolar_estado_erro_falha_no_raster():
    """Caminhos OK, mas falha ao carregar o raster -> None (curto-circuito)."""
    with patch.object(terreno, "obter_caminhos_arquivos", return_value=("t.tif", "f.shp")), \
            patch.object(terreno, "carregar_dados_topograficos", return_value=(None, None)):
        assert isolar_estado("RS") is None


def test_isolar_estado_erro_falha_na_fronteira():
    """Raster OK, mas falha ao carregar a fronteira -> None (curto-circuito)."""
    with patch.object(terreno, "obter_caminhos_arquivos", return_value=("t.tif", "f.shp")), \
            patch.object(terreno, "carregar_dados_topograficos", return_value=(np.zeros((2, 2)), "TR")), \
            patch.object(terreno, "carregar_fronteiras", return_value=None):
        assert isolar_estado("RS") is None


def test_isolar_estado_erro_falha_no_isolamento():
    """Fronteira OK, mas falha ao aplicar o isolamento -> None."""
    with patch.object(terreno, "obter_caminhos_arquivos", return_value=("t.tif", "f.shp")), \
            patch.object(terreno, "carregar_dados_topograficos", return_value=(np.zeros((2, 2)), "TR")), \
            patch.object(terreno, "carregar_fronteiras", return_value=MagicMock()), \
            patch.object(terreno, "aplicar_mascara_isolamento", return_value=None):
        assert isolar_estado("RS") is None
