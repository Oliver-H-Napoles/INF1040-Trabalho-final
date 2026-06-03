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