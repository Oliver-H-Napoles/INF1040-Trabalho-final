"""
Configuração global da suíte de testes (pytest).

Força o backend não-interativo "Agg" do matplotlib antes que qualquer módulo de
visualização seja importado, garantindo que nenhuma janela de gráfico seja
aberta durante a execução dos testes.
"""
import matplotlib

matplotlib.use("Agg")
