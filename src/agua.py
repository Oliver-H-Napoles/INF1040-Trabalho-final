def cria_mascara_agua(tam_x: int, tam_y: int, xy_fonte: int) -> list[list[int]]:
    '''
    
    '''

    tamanhoValido: bool = (tam_x > 0) and (tam_y > 0)
    if not tamanhoValido:
        return [4]
    
    fonteValida: bool = (xy_fonte >= 0) and (xy_fonte < 4)
    if not fonteValida:
        return [3]
    
    ret = [
        [
            0
            for _ in range(tam_y)
        ]
        for i in range(tam_x)
    ]

    if xy_fonte == 0:
        ret[0][0] = 1
    elif xy_fonte == 1:
        ret[0][-1] = 1
    elif xy_fonte == 2:
        ret[-1][-1] = 1
    else:
        ret[-1][0] = 1
    
    return ret

def expandir_mascara_agua(terreno, masc_agua: list[list[int]], nivel_do_mar: int) -> float:
    return