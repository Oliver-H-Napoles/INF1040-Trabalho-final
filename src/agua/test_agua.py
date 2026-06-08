import pytest
import numpy as np

from agua import cria_mascara_agua, expandir_mascara_agua

'''
    -------------------------------------
    --- tests para cria_mascara_agua ---
    -------------------------------------
'''

# Casos que os inputs são válidos
def test_CriaMascara1():
    ans: np.ndarray = np.array(
        [
            [1,0],
            [0,0],
            [0,0]
        ], dtype=float
    )
    assert np.array_equal(cria_mascara_agua(3,2,0), ans) == True
    
def test_CriaMascara2():
    ans: np.ndarray = np.array(
        [
            [0, 1],
            [0, 0],
            [0, 0]
        ], dtype=float
    )
    assert np.array_equal(cria_mascara_agua(3,2,1), ans) == True

def test_CriaMascara3():
    ans: np.ndarray = np.array(
        [
            [0, 0],
            [0, 0],
            [0, 1]
        ], dtype=float
    )
    assert np.array_equal(cria_mascara_agua(3,2,2), ans) == True
        
def test_CriaMascara4():
    ans: np.ndarray = np.array(
        [
            [0, 0],
            [0, 0],
            [1, 0]
        ], dtype=float
    )
    assert np.array_equal(cria_mascara_agua(3,2,3), ans) == True

def test_CriaMascara5():
    ans: np.ndarray = np.array(
        [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 1]
        ], dtype=float
    )
    assert np.array_equal(cria_mascara_agua(4,3,2), ans) == True
    
# Casos em que o tamanho da matriz é invalido
def test_CriaMascara6():
    ans = np.array([4], dtype=float)
    assert np.array_equal(cria_mascara_agua(-1, 0, 0), ans) == True

def test_CriaMascara7():
    ans = np.array([4], dtype=float)
    assert np.array_equal(cria_mascara_agua(0, 0, 0), ans) == True

def test_CriaMascara8():
    ans = np.array([4], dtype=float)
    assert np.array_equal(cria_mascara_agua(10, -2, 0), ans) == True

# Casos em que a fonte d`água não está no intervalo 0:3
def test_CriaMascara9():
    ans = np.array([3], dtype=float)
    assert np.array_equal(cria_mascara_agua(10, 10, 5), ans) == True

def test_CriaMascara10():
    ans = np.array([3], dtype=float)
    assert np.array_equal(cria_mascara_agua(10, 10, -1), ans) == True

def test_CriaMascara11():
    ans = np.array([3], dtype=float)
    assert np.array_equal(cria_mascara_agua(10, 10, 4), ans) == True


'''
    -----------------------------------------
    --- tests para expandir_mascara_agua ---
    -----------------------------------------
'''
# Casos que os inputs são válidos
def test_ExpandirMascara1():
    terreno = np.array(
        [
            [5, 3, 2],
            [10, 2, 0],
            [1, 0, 0]
        ], dtype=float
    )
    ans = 7/9 * 100

    assert expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 3) == pytest.approx(ans)

def test_ExpandirMascara2():
    terreno = np.array(
        [
            [5, 1, 2],
            [1, 4, 10],
            [1, 10, 0]
        ], dtype=float
    )
    ans = 1/9 * 100

    assert expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 3) == pytest.approx(ans)

def test_ExpandirMascara3():
    terreno = np.array(
        [
            [5, 4, 5.3],
            [3, 2.5, 1],
            [2.6, 1.1, 0.9],
            [2.3, 3.2, 0]
        ], dtype=float
    )
    ans = 8/12 * 100

    assert expandir_mascara_agua(terreno, cria_mascara_agua(4,3,2), 3.0) == pytest.approx(ans)

# Casos em que o tamanho das matrizes é diferente
def test_ExpandirMascara4():
    terreno = np.array(
        [
            [5, 1, 2],
            [1, 4, 10],
            [1, 10, 0]
        ], dtype=float
    )

    assert expandir_mascara_agua(terreno, cria_mascara_agua(2,2,2), 3) == pytest.approx(-1.0)

def test_ExpandirMascara5():
    terreno = np.array(
        [
            [5, 1, 2, 3],
            [1, 4, 10, 3],
            [1, 10, 0, 3]
        ], dtype=float
    )

    assert expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 3) == pytest.approx(-1.0)

# Caso em que o nível do mar é nulo
def test_ExpandirMascara6():
    terreno = np.array(
        [
            [5, 1, 2],
            [1, 4, 10],
            [1, 10, 0]
        ], dtype=float
    )

    assert expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 0) == pytest.approx(-2.0)
