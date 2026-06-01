__all__ = ["cria_mascara_agua", "expandir_mascara_agua"]


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
    
    ret = [
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
    ret[linha][col] = 1
    
    return ret

def expandir_mascara_agua(terreno, masc_agua: list[list[int]], nivel_do_mar: int) -> float:
    return