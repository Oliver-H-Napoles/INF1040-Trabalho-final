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

        @returns (convenção de ação — int):
            0 -> Se tudo foi carregado sem nenhum problema;
            1 -> Não encontrou dados sobre a máscara d`água (ou nascente ausente);
            2 -> Erro ao carregar os arquivos.

        Assertiva de entrada:
            O parâmetro "path_arq" tem que ser um caminho válido para um arquivo JSON

        Assertiva de saída:
            Em caso de êxito (0), a variável global _dados estará carregada com a máscara e com a nascente.
            Deve retornar um inteiro indicando o status da execução.
    '''
    print("Carregando dados da última execução")

    try:
        with open(path_arq, "r", encoding="utf-8") as file:
            data = load(file)
    except Exception as erro:
        print(f"Erro ao carregar state.json: {erro}")
        return 2

    try:
        caminho_mascara = data["files"]["mascara_agua"]
    except KeyError:
        return 1

    try:
        mascara = np.load(caminho_mascara, allow_pickle=False)
    except Exception as erro:
        print(f"Erro ao carregar máscara: {erro}")
        return 2

    nascente = acha_nascente(mascara)

    if nascente is None:
        return 1

    global _dados
    _dados["mascara"] = mascara
    _dados["nascente"] = nascente

    return 0


def acha_nascente(mat: np.ndarray) -> tuple[int, int] | None:
    '''
        Objetivo: Localizar a nascente (canto com valor 0) na máscara de água.

        @returns (convenção de produtora):
            (x, y) -> Tupla com a posição da nascente em caso de êxito;
            None   -> Se nenhum dos cantos da máscara contiver uma nascente.
    '''
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

    return None


def cria_mascara_agua(tam_x: int, tam_y: int, xy_fonte: int) -> np.ndarray | None:
    '''
        Objetivo: Criar a máscara (matriz) de água com nascente em um dos cantos

        @params:
            "tam_x" -> Valor inteiro positivo não nulo, ou seja maior do que 0, que representa a quantidade de linhas que a matriz terá;
            "tam_y" -> Valor inteior positivo não nulo, ou seja maior do que 0, que representa a quantidade de colunas que a matriz terá;
            "xy_fonte" -> Valor inteiro que representa em qual canto a nascente d`água está na matriz, ou seja, de onde a água se espalhará inicialmente.
        
        @return (convenção de produtora):
            None -> Erro em relação aos parâmetros (tamanho inválido ou "xy_fonte" fora de [0, 3]);
            Numpy 2-dimension array com todas as células com 0, exceto a nascente com 1, em caso de êxito.

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
        return None

    fonteValida: bool = xy_fonte in [0, 1, 2, 3]
    if not fonteValida:
        return None
    
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


def expandir_mascara_agua(terreno: np.ndarray, masc_agua: np.ndarray, nivel_do_mar: float) -> int | None:
    '''
        Objetivo: Expandir a máscara d`água para ver o percentual de inundação dado certo nível do mar

        @params:
            "terreno" -> Numpy 2-dimensional array, em que cada célula consta os valores de altitude daquela região
            "masc_agua" -> Máscara criada pela função "cria_mascara_agua" 
            "nivel_do_mar" -> Inteiro que indica o nível de inundação a ser simulado

        @returns (convenção de produtora):
            None -> Erro de parâmetro: nível do mar não positivo, tamanhos de "terreno"/"masc_agua"
                    incompatíveis, ou "masc_agua" diferente da máscara armazenada neste módulo;
            int  -> A quantidade de células inundadas para aquele nível do mar, em caso de êxito.

        Assertivas de entradas:
            O parâmetro "terreno" deve seguir todas as assertivas do raster;
            O parâmetro "masc_agua" deve seguir todas as assertivas da máscara d`água, definido na função "cria_mascara_agua";
            O parâmetro de "nivel_do_mar" é um inteiro positivo, não nulo.
        
        Assertivas de saída:
            O retorno dessa função será um int não nulo em caso de êxito, ou None em caso de erro;
    '''
    print("Expandindo máscara de água")
    if nivel_do_mar <= 0:
        return None

    tam_x, tam_y = masc_agua.shape
    has_same_size: bool = (tam_x, tam_y) == terreno.shape
    if not has_same_size:
        return None

    global _dados

    if not np.array_equal(masc_agua, _dados["mascara"]):
        return None

    # Para o BFS
    neighbors: deque[tuple[int, int]] = deque()
    qtd: int = 1 # Já considerando a nascente

    neighbors.append(_dados["nascente"])
    while bool(neighbors):
        x, y = neighbors.popleft()
        # print(f"Expansão para a célula ({x}, {y}) {len(neighbors)} restantes")

    
        for new_x, new_y in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if not (0 <= new_x < tam_x and 0 <= new_y < tam_y):
                continue
            if (masc_agua[new_x][new_y] == 0 and terreno[new_x][new_y] <= nivel_do_mar):
                masc_agua[new_x][new_y] = 1
                if terreno[new_x][new_y] > -1:
                    qtd += 1 
                neighbors.append((new_x, new_y))

    return qtd