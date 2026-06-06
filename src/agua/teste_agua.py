import unittest
import numpy as np

from agua import cria_mascara_agua, expandir_mascara_agua

class TesteCriaMascaraAgua(unittest.TestCase):
    # ---------- cria_mascara_agua ----------
    '''
        Casos que os inputs são válidos
    '''
    def test_ValidMatrix_0(self):
        ans: np.ndarray = np.array(
            [
                [1,0],
                [0,0],
                [0,0]
            ], dtype=float
        )
        self.assertTrue(np.array_equal(cria_mascara_agua(3,2,0), ans))
    
    def test_ValidMatrix_1(self):
        ans: np.ndarray = np.array(
            [
                [0, 1],
                [0, 0],
                [0, 0]
            ], dtype=float
        )
        self.assertTrue(np.array_equal(cria_mascara_agua(3,2,1), ans))

    def test_ValidMatrix_2(self):
        ans: np.ndarray = np.array(
            [
                [0, 0],
                [0, 0],
                [0, 1]
            ], dtype=float
        )
        self.assertTrue(np.array_equal(cria_mascara_agua(3,2,2), ans))
        
    def test_ValidMatrix_3(self):
        ans: np.ndarray = np.array(
            [
                [0, 0],
                [0, 0],
                [1, 0]
            ], dtype=float
        )
        self.assertTrue(np.array_equal(cria_mascara_agua(3,2,3), ans))
        
    
    '''
        Casos em que o tamanho da matriz é invalido
    '''
    def test_InvalidMatrix_0(self):
        ans = np.array([4], dtype=float)
        self.assertTrue(np.array_equal(cria_mascara_agua(-1, 0, 0), ans))
    def test_InvalidMatrix_1(self):
        ans = np.array([4], dtype=float)
        self.assertTrue(np.array_equal(cria_mascara_agua(0, 0, 0), ans))
    def test_InvalidMatrix_2(self):
        ans = np.array([4], dtype=float)
        self.assertTrue(np.array_equal(cria_mascara_agua(10, -2, 0), ans))
    
    '''
        Casos em que a fonte d`água não está no intervalo 0:3
    '''
    def test_InvalidWaterFountain_0(self):
        ans = np.array([3], dtype=float)
        self.assertTrue(np.array_equal(cria_mascara_agua(10, 10, 5), ans))
    def test_InvalidWaterFountain_1(self):
        ans = np.array([3], dtype=float)
        self.assertTrue(np.array_equal(cria_mascara_agua(10, 10, -1), ans))
    def test_InvalidWaterFountain_2(self):
        ans = np.array([3], dtype=float)
        self.assertTrue(np.array_equal(cria_mascara_agua(10, 10, 4), ans))

    
    # ---------- expandir_mascara_agua ----------
    '''
        Casos que os inputs são válidos
    '''
    def test_ValidInputs1(self):
        terreno = np.array(
            [
                [5, 3, 2],
                [10, 2, 0],
                [1, 0, 0]
            ], dtype=float
        )

        self.assertEqual(expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 3), 7/9 * 100)
    def test_ValidInputs2(self):
        terreno = np.array(
            [
                [5, 1, 2],
                [1, 4, 10],
                [1, 10, 0]
            ], dtype=float
        )

        self.assertEqual(expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 3), 1/9 * 100)
    
    '''
        Casos em que o tamanho das matrizes é diferente
    '''
    def test_DiferentSizeMat1(self):
        terreno = np.array(
            [
                [5, 1, 2],
                [1, 4, 10],
                [1, 10, 0]
            ], dtype=float
        )

        self.assertEqual(expandir_mascara_agua(terreno, cria_mascara_agua(2,2,2), 3), -1.0)
    def test_DiferentSizeMat2(self):
        terreno = np.array(
            [
                [5, 1, 2, 3],
                [1, 4, 10, 3],
                [1, 10, 0, 3]
            ], dtype=float
        )

        self.assertEqual(expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 3), -1.0)

    '''
        Caso em que o nível do mar é nulo
    '''
    def test_NivelNulo1(self):
        terreno = np.array(
            [
                [5, 1, 2],
                [1, 4, 10],
                [1, 10, 0]
            ], dtype=float
        )

        self.assertEqual(expandir_mascara_agua(terreno, cria_mascara_agua(3,3,2), 0), -2.0)


def main():
    unittest.main()


if __name__ == "__main__":
    main()