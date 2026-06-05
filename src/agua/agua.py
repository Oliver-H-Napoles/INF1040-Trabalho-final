__all__ = ["cria_mascara_agua", "expandir_mascara_agua"]

# Import das bibliotecas necessárias
import numpy as np


# Funções
def cria_mascara_agua(tam_x: int, tam_y: int, xy_fonte: int) -> list[list[int]]:
    '''
        Cria a máscara de água com nascente em um dos cantos

        Possíveis retornos de erro:
            [3] -> Valor para a posição da fonte inválido
            [4] -> Tamanho da matriz (x e/ou y) inválido, ou seja, menor, ou igual, a 0
    '''

    tamanhoValido: bool = (tam_x > 0) and (tam_y > 0)
    if not tamanhoValido:
        return [4]
    
    fonteValida: bool = xy_fonte in [0, 1, 2, 3]
    if not fonteValida:
        return [3]
    
    _matrizAgua = [
        [0] * tam_y
        for _ in range(tam_x)
    ]

    pos_fonte = {
        0: (0,0),
        1: (0, tam_y-1),
        2: (tam_x - 1, tam_y - 1),
        3: (tam_x - 1, 0)
    }

    linha, col = pos_fonte[xy_fonte]
    _matrizAgua[linha][col] = 1
    
    return _matrizAgua


def expandir_mascara_agua(terreno: np.ndarray, masc_agua: list[list[int]], nivel_do_mar: int) -> float:
    if nivel_do_mar <= 0:
        return -2.0
    
    tam_x: int = len(masc_agua)
    tam_y: int = len(masc_agua[0])
    
    has_same_size: bool = (tam_x, tam_y) == terreno.shape
    if not has_same_size:
        return -1.0

    # Para o BFS
    neighbors: list[tuple[int, int]] = []
    visited: list[bool] = [
        [False] * tam_y
        for _ in range(tam_y)
    ]
    qtd: int = 0

    # Achar a posição em que a nascente d`água está
    pos_fonte = {
        0: (0,0),
        1: (0, tam_y-1),
        2: (tam_x - 1, tam_y - 1),
        3: (tam_x - 1, 0)
    }

    for _, (x, y) in pos_fonte.items():
        if masc_agua[x][y] == 1:
            neighbors.append((x,y))
            break

    while bool(neighbors):
        x, y = neighbors.pop(0)
        if visited[x][y]:
            continue

        visited[x][y] = True
        masc_agua[x][y] = 1
        qtd += 1

        for new_x in range(max(0,x-1),min(tam_x, x+2)):
            for new_y in range(max(0, y-1), min(tam_y, y+2)):
                if new_x == x and new_y == y:
                    continue
                if (not visited[new_x][new_y]) and (terreno[new_x][new_y] <= nivel_do_mar):
                    neighbors.append((new_x, new_y))

    
    return float(qtd/(tam_x * tam_y) * 100)