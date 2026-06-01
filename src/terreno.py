import rasterio
import numpy as np
import shapefile
import json
from typing import Tuple

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
    Recebe a sigla da UF (já validada) e busca no JSON de configuração os caminhos
    corretos do arquivo .tif e .shp correspondentes .
    """
    uf_formatada = uf.strip().upper()
    
    try:
        # Abre o arquivo JSON apenas como leitura ('r')
        with open('estados.json', 'r', encoding='utf-8') as estados:
            mapa_estados = json.load(estados)
            
        # Acessa a chave do estado correspondente e pega os caminhos
        dados_estado = mapa_estados[uf_formatada]
        caminho_arq_topo = dados_estado["arquivo_topo"]
        caminho_arq_front = dados_estado["arquivo_front"]
        
        return caminho_arq_topo, caminho_arq_front

    except FileNotFoundError:
        print("Arquivo de configuração estados.json não encontrado.")
        return None, None
        
    except KeyError:
        # Caso a UF validada não tenha sido mapeada dentro do JSON por algum motivo
        print(f"Dados para a UF {uf_formatada} não configurados no JSON.")
        return None, None

def carregar_dados_topograficos(caminho_arq_topo: str):
    """
    Carrega os dados de topografia a partir do caminho do arquivo em formato raster.
    Retorna a matriz (numpy array) com as elevações.
    """
    try:
        with rasterio.open(caminho_arq_topo) as dataset:
            raster_terreno = dataset.read(1)
            transform = dataset.transform
            
        # Salvando na nossa estrutura encapsulada para não precisar ler do disco novamente
        _arquivos_carregados["rasters"].append({"matriz": raster_terreno, "transform": transform})
        return raster_terreno, transform

    except FileNotFoundError:
        # Tratamento para o Caso 2: Arquivo inexistente [cite: 504]
        print("Arquivo não encontrado.")
        return None
        
    except rasterio.errors.RasterioIOError:
        # Tratamento para o Caso 3: Arquivo corrompido ou formato incorreto [cite: 505]
        print("Erro de leitura do arquivo.")
        return None
        
    except Exception as e:
        # Captura de segurança para qualquer outro erro não mapeado
        print(f"Erro inesperado ao carregar topografia: {e}")
        return None
    
    
def carregar_fronteiras(caminho_arq_front: str, uf_alvo: str):
    """
    Carrega os dados de fronteira a partir do caminho do arquivo em formato de polígono.
    Retorna a geometria (MultiPolygon) do estado alvo.
    """
    try:
        # Tenta abrir o arquivo garantindo o fechamento seguro após a leitura
        with shapefile.Reader(caminho_arq_front) as sf:
            
            indice_uf = -1
            
            # Itera sobre a "tabela" do shapefile para achar o índice da nossa UF alvo
            for i, record in enumerate(sf.records()):
                # O record comporta-se como uma lista. Verificamos se a nossa sigla está lá
                # O strip() e upper() garantem que espaços ou letras minúsculas não quebrem a lógica
                if uf_alvo.strip().upper() in [str(val).strip().upper() for val in record]:
                    indice_uf = i
                    break
            
            # Tratamento do Caso 2: Caminho válido, mas UF não existe na tabela [cite: 509, 510]
            if indice_uf == -1:
                print("Sigla de UF não encontrada na tabela do arquivo selecionado")
                return None
                
            # Sabendo o índice, extraímos a geometria correspondente que possui as coordenadas
            # Isso atende ao Caso 1: Retornar a geometria do estado [cite: 507, 508]
            poligono_fronteira = sf.shape(indice_uf)
            
            # Encapsulando o dado na estrutura privada do módulo
            _arquivos_carregados["poligonos"].append({uf_alvo: poligono_fronteira})
            
            return poligono_fronteira

    except shapefile.ShapefileException:
        # Tratamento do Caso 3: Arquivo existente, mas com formato incorreto [cite: 511, 512]
        print("Formato de arquivo inválido para leitura")
        return None
        
    except FileNotFoundError:
        # Tratamento do Caso 4: Caminho de arquivo inexistente [cite: 513]
        print("Arquivo não encontrado")
        return None
        
    except Exception as e:
        print(f"Erro inesperado ao carregar fronteira: {e}")
        return None
    
def aplicar_mascara_isolamento(raster_terreno, poligono_fronteira, transform):
    """
    Sobrepõe o polígono de fronteira sobre o raster topográfico[cite: 438].
    Preserva os dados originais dentro da UF e cria barreiras externas .
    """
    # O valor estipulado no Caso de Teste 1 do Módulo Terreno é 10000 [cite: 518-519]
    VALOR_BARREIRA = 10000
    
    try:
        # Extrai as dimensões da matriz do terreno (linhas e colunas)
        formato_matriz = raster_terreno.shape
        
        # A função geometry_mask cria uma matriz booleana do exato tamanho do raster.
        # Por padrão (invert=False), ela marca True para pixels FORA do polígono 
        # e False para pixels DENTRO do polígono.
        mascara_booleana = features.geometry_mask(
            geometries=[poligono_fronteira],
            out_shape=formato_matriz,
            transform=transform,
            invert=False
        )
        
        # A função np.where do numpy funciona como um if/else vetorizado e de alta performance:
        # np.where(condição, valor_se_verdadeiro, valor_se_falso)
        # Onde a máscara for True (fora do estado), colocamos 10000.
        # Onde for False (dentro do estado), mantemos o valor do raster_terreno.
        raster_delimitado = np.where(mascara_booleana, VALOR_BARREIRA, raster_terreno)
        
        return raster_delimitado

    except Exception as e:
        print(f"Erro ao aplicar máscara de isolamento: {e}")
        return None   