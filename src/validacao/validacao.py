__all__ = [
    "valida_uf",
    "valida_elevacao",
    "valida_raster",
    "valida_matrizes_tamanho"
]

import json
from typing import Any


def valida_uf(uf: str) -> int:
    '''
        Objetivo: Validar uma string para que seja um UF válida.

        @params:
            "uf" -> Uma string.

        @returns (convenção de ação — int):
            0 -> Se o UF fornecido é válido;
            1 -> Input inválido (não é do tipo string ou não pertence aos estados válidos);
            2 -> Erro ao abrir o JSON contendo os estados válidos.

        Assertiva de entrada:
            O parâmetro "uf" deve ser uma string válida, ou seja, não nula.

        Assertiva de saída:
            Em caso de êxito (0), o parâmetro UF deve constar na lista de estados válidos
            Deve retornar um inteiro indicando o status da execução.
    '''
    if not isinstance(uf, str):
        return 1

    uf_formatada = uf.strip().upper()
    if len(uf_formatada) != 2 or not uf_formatada.isalpha():
        return 1

    try:
        with open('data/estados.json', 'r', encoding='utf-8') as arquivo:
            estados = json.load(arquivo)
    except Exception:
        return 2

    return 0 if uf_formatada in estados else 1


def valida_elevacao(metros: int) -> int:
    '''
        Objetivo: Validar um inteiro para que seja positivo.

        @params:
            "metros" -> Um int.

        @returns (convenção de ação — int):
            0 -> Se a elevação é válida;
            1 -> Input inválido (é negativo);
            2 -> Input não é do tipo int.

        Assertiva de entrada:
            O parâmetro "metros" deve ser um inteiro válido.

        Assertiva de saída:
            Em caso de êxito (0), o parâmetro metros deve ser positivo;
            Deve retornar um inteiro indicando o status da execução.
    '''
    if not isinstance(metros, int):
        return 2

    return 0 if metros >= 0 else 1


def valida_raster(raster: Any) -> int:
    '''
        Objetivo: Validar um raster, ou seja, uma matriz bi-dimensional.

        @params:
            "raster" -> Uma matriz numpy n-dimensional.

        @returns (convenção de ação — int):
            0 -> O raster fornecido é bi-dimensional;
            1 -> Input inválido (não é uma matriz numpy n-dimensional);
            2 -> Matriz não é bi-dimensional

        Assertiva de entrada:
            O parâmetro "raster" deve ser uma matriz numpy n-dimensional válida.

        Assertiva de saída:
            Em caso de êxito (0), o parâmetro raster deve ser uma matriz bi-dimensional;
            Deve retornar um inteiro indicando o status da execução.
    '''
    if raster is None:
        return 1

    if not hasattr(raster, 'shape'):
        return 1

    if len(getattr(raster, 'shape')) != 2:
        return 2

    return 0


def valida_matrizes_tamanho(matriz1: Any, matriz2: Any) -> int:
    '''
        Objetivo: Validar que 2 matrizes tenham a mesma dimensão.

        @params:
            "matriz1" e "matriz2" -> Matriz numpy n-dimensional.

        @returns (convenção de ação — int):
            0 -> O raster fornecido é bi-dimensional;
            1 -> As matrizes não possuem o mesmo tamanho
            2 -> Input inválido (não é uma matriz numpy n-dimensional);

        Assertiva de entrada:
            Os parâmetros "matriz1" e "matriz2" devem ser uma matriz numpy n-dimensional válida.

        Assertiva de saída:
            Em caso de êxito (0), ambas matrizes devem ter a mesma dimensão e tamanho;
            Deve retornar um inteiro indicando o status da execução.
    '''
    if matriz1 is None or matriz2 is None:
        return 2

    if not hasattr(matriz1, 'shape') or not hasattr(matriz2, 'shape'):
        return 2

    return 0 if getattr(matriz1, 'shape') == getattr(matriz2, 'shape') else 1

