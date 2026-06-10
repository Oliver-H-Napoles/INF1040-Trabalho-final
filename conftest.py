"""
Configuração global da suíte de testes (pytest).

1. Força o backend não-interativo "Agg" do matplotlib antes que qualquer módulo
   de visualização seja importado, garantindo que nenhuma janela de gráfico seja
   aberta durante a execução dos testes.

2. Gera um relatório descritivo (estilo "spec"): para cada teste imprime, sob o
   nome do módulo, a descrição do caso (1ª linha da docstring do teste) e o
   resultado obtido (PASSOU / FALHOU / PULADO). Em caso de falha, o valor
   esperado vs. obtido continua sendo exibido pela introspecção padrão do pytest.
"""
import sys

import matplotlib

matplotlib.use("Agg")

import pytest

# Garante que os acentos do relatório descritivo sejam exibidos corretamente,
# independentemente da página de código padrão do console (ex.: cp1252 no Windows).
# No Windows, ajusta a code page do console para UTF-8 (65001) e, em seguida,
# reconfigura o stdout para emitir bytes UTF-8.
if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Rótulo e símbolo exibidos para cada resultado.
_ROTULO = {
    "passed": "PASSOU",
    "failed": "FALHOU",
    "skipped": "PULADO",
}
_SIMBOLO = {
    "passed": "v",
    "failed": "x",
    "skipped": "-",
}

# Descrição de cada teste (1ª linha da docstring), capturada na coleta.
_DESCRICOES: dict = {}
# Controla a impressão do cabeçalho do módulo apenas uma vez por arquivo.
_ULTIMO_ARQUIVO: dict = {"nome": None}


def _descricao_legivel(item) -> str:
    """Descrição do caso: docstring do teste ou, na falta, o nome formatado."""
    funcao = getattr(item, "function", None)
    doc = (getattr(funcao, "__doc__", None) or "").strip()
    if doc:
        return doc.splitlines()[0].strip()
    # Sem docstring: transforma "test_valida_uf_ok_x" em "valida uf ok x".
    nome = item.name
    if nome.startswith("test_"):
        nome = nome[len("test_"):]
    return nome.replace("_", " ")


def pytest_collection_modifyitems(items):
    for item in items:
        _DESCRICOES[item.nodeid] = _descricao_legivel(item)


def pytest_report_teststatus(report, config):
    # Suprime os marcadores padrão (".", "F", "s", "E") em uma linha só, pois o
    # relatório descritivo é impresso por pytest_runtest_logreport. As categorias
    # são preservadas para que o resumo final ("N passed") continue correto.
    outcome = report.outcome
    if report.when == "call":
        return outcome, "", ""
    if report.when == "setup":
        if outcome == "skipped":
            return "skipped", "", ""
        if outcome == "failed":
            return "error", "", ""
    return "", "", ""


def pytest_runtest_logreport(report):
    # Reporta o resultado da fase de execução do teste; também captura falhas
    # ocorridas na preparação (fixtures).
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        arquivo = report.nodeid.split("::")[0]
        if arquivo != _ULTIMO_ARQUIVO["nome"]:
            _ULTIMO_ARQUIVO["nome"] = arquivo
            print(f"\n{arquivo}")

        descricao = _DESCRICOES.get(report.nodeid, report.nodeid)
        simbolo = _SIMBOLO.get(report.outcome, "?")
        rotulo = _ROTULO.get(report.outcome, report.outcome.upper())
        print(f"  [{simbolo}] {rotulo:7s} {descricao}")
