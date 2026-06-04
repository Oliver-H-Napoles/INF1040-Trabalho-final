import rasterio
from rasterio import features # CORREÇÃO: Import necessário para a máscara
import numpy as np
import shapefile
import json
from typing import Tuple, Any

__all__ = [
    "obter_caminhos_arquivos",
    "carregar_dados_topograficos",
    "carregar_fronteiras",
    "aplicar_mascara_isolamento"
]

_arquivos_carregados = {
    "rasters": [],
    "poligonos": []
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
    uf_formatada = uf.strip().upper()
    try:
        with open('estados.json', 'r', encoding='utf-8') as estados:
            mapa_estados = json.load(estados)
            
        dados_estado = mapa_estados[uf_formatada]
        return dados_estado["arquivo_topo"], dados_estado["arquivo_front"]

    except FileNotFoundError:
        print("Arquivo de configuração estados.json não encontrado.")
        return None, None
    except KeyError:
        print(f"Dados para a UF {uf_formatada} não configurados no JSON.")
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
    try:
        with rasterio.open(caminho_arq_topo) as dataset:
            raster_terreno = dataset.read(1)
            transform = dataset.transform
            
        _arquivos_carregados["rasters"].append({"matriz": raster_terreno, "transform": transform})
        return raster_terreno, transform

    except FileNotFoundError:
        print("Arquivo não encontrado.")
        return None, None
    except rasterio.errors.RasterioIOError:
        print("Erro de leitura do arquivo.")
        return None, None
    except Exception as e:
        print(f"Erro inesperado ao carregar topografia: {e}")
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

    except shapefile.ShapefileException:
        print("Formato de arquivo inválido para leitura")
        return None
    except FileNotFoundError:
        print("Arquivo não encontrado")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar fronteira: {e}")
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
    
    VALOR_BARREIRA = 10000
    
    try:
        formato_matriz = raster_terreno.shape
        
        # CORREÇÃO: Uso do __geo_interface__ para compatibilidade com rasterio
        mascara_booleana = features.geometry_mask(
            geometries=[poligono_fronteira.__geo_interface__], 
            out_shape=formato_matriz,
            transform=transform,
            invert=False
        )
        
        raster_delimitado = np.where(mascara_booleana, VALOR_BARREIRA, raster_terreno)
        return raster_delimitado

    except Exception as e:
        print(f"Erro ao aplicar máscara de isolamento: {e}")
        return None