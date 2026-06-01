import unittest
from agua.agua import cria_mascara_agua, expandir_mascara_agua

class TesteCriaMascaraAgua(unittest.TestCase):
    '''
        Casos que os inputs são válidos
    '''
    def test_ValidMatrix_0(self):
        self.assertEqual(cria_mascara_agua(3,2,0), [[1,0],[0,0],[0,0]])
    def test_ValidMatrix_1(self):
        self.assertEqual(cria_mascara_agua(3,2,1), [[0,1],[0,0],[0,0]])
    def test_ValidMatrix_2(self):
        self.assertEqual(cria_mascara_agua(3,2,2), [[0,0],[0,0],[0,1]])
    def test_ValidMatrix_3(self):
        self.assertEqual(cria_mascara_agua(3,2,3), [[0,0],[0,0],[1,0]])
    
    '''
        Casos em que o tamanho da matriz é invalido
    '''
    def test_InvalidMatrix_0(self):
        self.assertEqual(cria_mascara_agua(-1, 0, 0), [4])
    def test_InvalidMatrix_1(self):
        self.assertEqual(cria_mascara_agua(0, 0, 0), [4])
    def test_InvalidMatrix_2(self):
        self.assertEqual(cria_mascara_agua(10, -2, 0), [4])
    
    '''
        Casos em que a fonte d`água não está no intervalo 0:3
    '''
    def test_InvalidWaterFountain_0(self):
        self.assertEqual(cria_mascara_agua(10, 10, 5), [3])
    def test_InvalidWaterFountain_1(self):
        self.assertEqual(cria_mascara_agua(10, 10, -1), [3])
    def test_InvalidWaterFountain_2(self):
        self.assertEqual(cria_mascara_agua(10, 10, 4), [3])

def main():
    unittest.main()

if __name__ == "__main__":
    main()