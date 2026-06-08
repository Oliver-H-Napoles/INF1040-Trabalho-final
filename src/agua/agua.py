__all__ = ["cria_mascara_agua", "expandir_mascara_agua", "carrega_dados"]

# Import das bibliotecas necessárias
from collections import deque
from copy import deepcopy
import numpy as np
from json import load


# Dados encapsulados
_dados: dict = {
    "mascara": None,
    "nascente": 0
}


# Funções
def carrega_dados(path_arq: str) -> int:
    '''
        Objetivo: Carregar os dados caso a execução seja interrompida

        @params:
            "path_arq" -> String contendo o caminho para o arquivo com as informações da última execução a ser recuperada
        
        @returns:
            0 -> Se tudo foi carregado sem nenhum problema;
            1 -> Não encontrou dados sobre a máscara d`água.
            2 -> Erro ao carregar os arquivos
        
        Assertiva de entrada:
            O parâmetro "path_arq" tem que ser um caminho válido para um arquivo JSON 
        
        Assertiva de saída:
            A variável global _dados deve estar carregada com a máscara e com a nascente
            Deve retornar um inteiro indicando o status da execução
    '''
    print("Carregando dados da última execução")
    data: dict
    with open(path_arq, "r") as file:
        data = load(file)
    
    if "masc_agua" in data.keys():
        global _dados

        try:
            _dados["mascara"] = data["masc_agua"]
            _dados["nascente"] = acha_nascente(_dados["mascara"])
        except Exception as e:
            raise e
        
    return 1


def acha_nascente(mat: np.ndarray) -> tuple[int, int]:
    print("Procurando a nascente na máscara de água")
    tam_x, tam_y = mat.shape
    pos_fonte: dict = {
        0: (0, 0),
        1: (0, tam_y - 1),
        2: (tam_x - 1, tam_y - 1),
        3: (tam_x - 1, 0)
    }
    
    for (x, y) in pos_fonte.values():
        if mat[x][y] == 0:
            return (x, y)
    
    raise Exception("Nascente não encontrada na máscara de água carregada.")


def cria_mascara_agua(tam_x: int, tam_y: int, xy_fonte: int) -> np.ndarray:
    '''
        Objetivo: Criar a máscara (matriz) de água com nascente em um dos cantos

        @params:
            "tam_x" -> Valor inteiro positivo não nulo, ou seja maior do que 0, que representa a quantidade de linhas que a matriz terá;
            "tam_y" -> Valor inteior positivo não nulo, ou seja maior do que 0, que representa a quantidade de colunas que a matriz terá;
            "xy_fonte" -> Valor inteiro que representa em qual canto a nascente d`água está na matriz, ou seja, de onde a água se espalhará inicialmente.
        
        @return:
            [3] -> Erro em relação ao parâmetro "xy_fonte";
            [4] -> Erro em relação aos parâmetros "tam_x" e "tam_y";
            Demais casos -> Numpy 2-dimension array com todas as células com 0, exceto a nascente com 1.

        Asserivas de entrada:
            Os parâmetros "tam_x" e "tam_y" devem ser, ambos, positivos não nulos;
            O parâmetro "xy_fonte" deve estar no intervalo [0, 3], ambos extremos inclusos.
        
        Assertivas de saída:
            O retorno dessa função deve ser uma matriz de dimensões (tam_x, tam_y) com todos os valores em 0, exceto pelo canto em que a nascente d`água está presente;
            Cada célula da matriz deve ter apenas um inteiro.
    '''
    print("Criando máscara de água")
    tamanhoValido: bool = (tam_x > 0) and (tam_y > 0)
    if not tamanhoValido:
        return np.array([4], dtype=float)
    
    fonteValida: bool = xy_fonte in [0, 1, 2, 3]
    if not fonteValida:
        return np.array([3], dtype=float)
    
    global _dados
    
    _dados["mascara"] = np.array(
        [
            [0] * tam_y
            for _ in range(tam_x)
        ], dtype=float
    )

    pos_fonte = {
        0: (0,0),
        1: (0, tam_y-1),
        2: (tam_x - 1, tam_y - 1),
        3: (tam_x - 1, 0)
    }

    linha, col = _dados["nascente"] = pos_fonte[xy_fonte]
    _dados["mascara"][linha][col] = 1
    
    return deepcopy(_dados["mascara"])


def expandir_mascara_agua(terreno: np.ndarray, masc_agua: np.ndarray, nivel_do_mar: float) -> float:
    '''
        Objetivo: Expandir a máscara d`água para ver o percentual de inundação dado certo nível do mar

        @params:
            "terreno" -> Numpy 2-dimensional array, em que cada célula consta os valores de altitude daquela região
            "masc_agua" -> Máscara criada pela função "cria_mascara_agua" 
            "nivel_do_mar" -> Float que indica o nível de inundação a ser simulado

        @returns:
            -1.0 -> Erro em relação ao tamanho das matrizes "terreno" e "masc_agua";
            -2.0 -> Erro em relação ao parâmetro "nivel_do_mar";
            -3.0 -> Erro em relação ao parâmetro "masc_agua", o qual não corresponde à variável armazenada nesse módulo;
            Demais casos -> A porcentagem de células inundadas para aquele nível do mar.

        Assertivas de entradas:
            O parâmetro "terreno" deve seguir todas as assertivas do raster;
            O parâmetro "masc_agua" deve seguir todas as assertivas da máscara d`água, definido na função "cria_mascara_agua";
            O parâmetro de "nivel_do_mar" é um float positivo, não nulo.
        
        Assertivas de saída:
            O retorno dessa função será um float não nulo;
    '''
    print("Expandindo máscara de água")
    if nivel_do_mar <= 0:
        return -2.0
    
    tam_x, tam_y = masc_agua.shape
    has_same_size: bool = (tam_x, tam_y) == terreno.shape
    if not has_same_size:
        return -1.0
    
    global _dados
    
    if not np.array_equal(masc_agua, _dados["mascara"]):
        return -3.0

    # Para o BFS
    neighbors: deque[tuple[int, int]] = deque()
    qtd: int = 1 # Já considerando a nascente

    neighbors.append(_dados["nascente"]) # Canto inferior direito (conforme especificação)
    while bool(neighbors):
        x, y = neighbors.popleft()
        # print(f"Expansão para a célula ({x}, {y}) {len(neighbors)} restantes")

    
        for new_x, new_y in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if not (0 <= new_x < tam_x and 0 <= new_y < tam_y):
                continue
            if (masc_agua[new_x][new_y] == 0 and terreno[new_x][new_y] <= nivel_do_mar):
                masc_agua[new_x][new_y] = 1
                qtd += 1
                neighbors.append((new_x, new_y))

    
    return float(qtd/(tam_x * tam_y) * 100)