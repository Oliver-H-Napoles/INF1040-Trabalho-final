import rasterio
from rasterio import features 
import numpy as np
import shapefile
import json
from typing import Tuple, Any

__all__ = [
    "carregar_estado",
]

_arquivos_carregados = {
    "rasters": [],
    "poligonos": [],
    "raster_delimitados": []
}

def obter_caminhos_arquivos(uf: str) -> Tuple[str, str]:
    """
    Obtém os caminhos de arquivo que serão utilizados nas demais funções, buscando no 
    arquivo de configuração (estados.json) os arquivos correspondentes à Unidade Federativa.

    Assertiva de entrada (Pré-condição):
    - 'uf' deve ser do tipo string, contendo a sigla de uma Unidade Federativa litorânea.
    - Conforme especificação [cite: 164-165], assume-se que 'uf' é válida (já triada pelo Módulo Validação).

    Assertiva de saída (Pós-condição):
    - Se a leitura do JSON for bem-sucedida, retorna uma tupla de strings (caminho_arq_topo, caminho_arq_front).
    - Se o arquivo JSON não existir ou a chave 'uf' não for encontrada, a função é interrompida de forma segura e retorna (None, None).

    @param uf: String contendo a sigla da Unidade Federativa alvo.
    @return: Tupla com (caminho_topo, caminho_front) ou (None, None).
    """
    print("Obtendo caminhos dos arquivos para a UF:", uf)
    uf_formatada = uf.strip().upper()
    try:
        with open('data/estados.json', 'r', encoding='utf-8') as estados:
            mapa_estados = json.load(estados)
            
            dados_estado = mapa_estados[uf_formatada]
        return "data/" + dados_estado["arquivo_topo"], "data/" + dados_estado["arquivo_front"]

    except Exception as erro:
        print(f"Erro ao obter caminhos para a UF '{uf}': {erro}")
        return None, None

def carregar_dados_topograficos(caminho_arq_topo: str) -> Tuple[np.ndarray, Any]:
    """
    Carrega os dados de topografia a partir do arquivo raster e salva em memória encapsulada.

    Assertiva de entrada (Pré-condição):
    - 'caminho_arq_topo' deve ser uma string apontando para o diretório de um arquivo .tif.

    Assertiva de saída (Pós-condição):
    - Se o arquivo for íntegro e legível, a matriz de elevação (numpy array) e os metadados 
      de transformação são adicionados à estrutura encapsulada '_arquivos_carregados["rasters"]'.
    - Retorna a tupla (raster_terreno, transform) contendo a matriz lida e os metadados.
    - Se o arquivo for inexistente, corrompido ou de formato inválido, a falha é tratada e retorna (None, None) [cite: 173-175].

    @param caminho_arq_topo: Caminho para o arquivo raster.
    @return: Tupla (matriz_elevacao, transformacao_espacial) ou (None, None).
    """
    print("Carregando dados topográficos")
    try:
        with rasterio.open(caminho_arq_topo) as dataset:
            raster_terreno = dataset.read(1)
            transform = dataset.transform
            
            _arquivos_carregados["rasters"].append({"matriz": raster_terreno, "transform": transform})
            
        return raster_terreno, transform

    except Exception as erro:
        print(f"Erro ao carregar dados topograficos de '{caminho_arq_topo}': {erro}")
        return None, None

def carregar_fronteiras(caminho_arq_front: str, uf_alvo: str):
    """
    Carrega a geometria de fronteira do estado a partir de um shapefile e encapsula em memória.

    Assertiva de entrada (Pré-condição):
    - 'caminho_arq_front' deve ser uma string apontando para o diretório de um arquivo .shp.
    - 'uf_alvo' deve ser uma string válida correspondente à UF desejada.

    Assertiva de saída (Pós-condição):
    - Se o estado for encontrado na tabela do shapefile, a geometria (MultiPolygon) é salva 
      na estrutura encapsulada '_arquivos_carregados["poligonos"]'.
    - Retorna o objeto geométrico da fronteira.
    - Se o arquivo não existir, o formato for inválido ou a UF não constar na tabela de dados, 
      o erro é reportado no terminal e a função retorna None [cite: 179-183].

    @param caminho_arq_front: Caminho para o arquivo de fronteira.
    @param uf_alvo: Sigla do estado cujas coordenadas serão extraídas.
    @return: Objeto poligono com a geometria do estado ou None.
    """
    print("Carregando fronteiras")
    try:
        with shapefile.Reader(caminho_arq_front) as sf:
            indice_uf = -1
            
            for i, record in enumerate(sf.records()):
                if uf_alvo.strip().upper() in [str(val).strip().upper() for val in record]:
                    indice_uf = i
                    break
            
            if indice_uf == -1:
                print("Sigla de UF não encontrada na tabela do arquivo selecionado")
                return None
                
            poligono_fronteira = sf.shape(indice_uf)
            _arquivos_carregados["poligonos"].append({uf_alvo: poligono_fronteira})
            
            return poligono_fronteira

    except Exception as erro:
        print(f"Erro ao carregar fronteiras de '{caminho_arq_front}': {erro}")
        return None


def aplicar_mascara_isolamento(raster_terreno, poligono_fronteira, transform):
    """
    Sobrepõe o polígono de fronteira sobre o raster topográfico para isolar a área de simulação.

    Assertiva de entrada (Pré-condição):
    - 'raster_terreno' deve ser uma matriz numérica (numpy.ndarray) contendo dados de elevação bidimensionais.
    - 'poligono_fronteira' deve ser um objeto de geometria válido com suporte ao protocolo geo_interface.
    - 'transform' deve ser um objeto Affine correspondente às coordenadas geográficas da matriz.

    Assertiva de saída (Pós-condição):
    - Retorna uma nova matriz do mesmo tamanho e tipo que 'raster_terreno'.
    - As coordenadas geográficas internas a 'poligono_fronteira' retêm seus valores numéricos originais.
    - As coordenadas externas recebem o valor de barreira estipulado (ex: 10000) [cite: 188-189].
    - Se ocorrer incompatibilidade de cálculo matemático ou erro de geometria, retorna None.

    @param raster_terreno: Matriz com dados de elevação.
    @param poligono_fronteira: Geometria da fronteira alvo.
    @param transform: Metadados de transformação espacial do mapa original.
    @return: Matriz com o isolamento topográfico aplicado ou None.
    """
    print("Aplicando máscara de isolamento")
    VALOR_BARREIRA = 10000
    VALOR_MAR = -1
    try:
        formato_matriz = raster_terreno.shape

        # CORREÇÃO: Uso do __geo_interface__ para compatibilidade com rasterio
        mascara_booleana = features.geometry_mask(
            geometries=[geometria], 
            out_shape=formato_matriz,
            transform=transform,
            invert=False
        )
        
        raster_estado = np.where(mascara_booleana, VALOR_BARREIRA, raster_terreno)

        with shapefile.Reader("data/coastline.shp") as sf:
            # 1. Grab the geo_interface for ALL shapes in the file, not just one
            poligono_mar = [s.__geo_interface__ for s in sf.shapes()]

        mascara_mar = features.geometry_mask(
            geometries=poligono_mar,
            out_shape=formato_matriz,
            transform=transform,
            invert=False
        )
        
        raster_delimitado = np.where(mascara_mar, VALOR_MAR, raster_estado)


        return raster_delimitado

    except Exception as erro:
        print(f"Erro ao aplicar mascara de isolamento: {erro}")
        return None


def carregar_estado(uf: str) -> np.ndarray | None:
    """
    Função principal do Módulo Terreno. Orquestra a leitura dos caminhos, 
    o carregamento da topografia, a extração das fronteiras e a aplicação do isolamento.

    Assertiva de entrada (Pré-condição):
    - 'uf' deve ser uma string contendo a sigla de uma Unidade Federativa litorânea válida.
    - O ambiente de execução deve conter a pasta 'data' com o arquivo 'estados.json' 
      e os respectivos arquivos espaciais (.tif e .shp) mapeados.

    Assertiva de saída (Pós-condição):
    - Retorna uma nova matriz bidimensional (numpy.ndarray) contendo os dados de elevação, 
      onde todas as coordenadas externas ao estado alvo foram substituídas pelo valor de barreira.
    - A matriz retornada é uma alocação de memória independente, garantindo que o cache interno 
      do módulo permaneça encapsulado e protegido contra edições externas.
    - Se qualquer etapa do fluxo falhar (UF inválida, arquivo inexistente, formato corrompido), 
      a execução é interrompida de forma segura e a função retorna None.

    @param uf: String com a sigla do estado a ser carregado (ex: "RJ").
    @return: Matriz topográfica delimitada (np.ndarray) ou None em caso de falha.
    """
    caminho_topo, caminho_front = obter_caminhos_arquivos(uf)
    if not caminho_topo or not caminho_front:
        return None

    raster, transform = carregar_dados_topograficos(caminho_topo)
    if raster is None:
        return None

    poligono = carregar_fronteiras(caminho_front, uf)
    if poligono is None:
        return None

    return aplicar_mascara_isolamento(raster, poligono, transform)
