# Simulador de Elevação do Nível do Mar

Este projeto consiste no desenvolvimento de uma **Engine de Física de Água** com o objetivo de **simular cenários realistas de inundação em terrenos complexos**. A aplicação utiliza estados brasileiros com fronteira oceânica como estudo de caso, processando dados topográficos de alta resolução para modelar como a água se propaga pela paisagem sob diferentes níveis de elevação do mar.

Ao final da execução, o simulador fornece **insights visuais** de regiões propensas a inundações e **dados quantitativos** sobre a relação entre o nível da água e a área total alagada.

## 🚀 Funcionalidades (Requisitos Funcionais)

*   **Definição e Validação de Área:** Permite a escolha da área de análise através da sigla da Unidade Federativa (UF), validando se o estado é brasileiro e possui fronteira litorânea.
*   **Configuração de Elevação:** O usuário define o valor do aumento do nível do mar em metros.
*   **Isolamento Geográfico:** Isola geograficamente a UF de análise utilizando os dados de fronteira para remover da simulação UFs vizinhas ou áreas oceânicas.
*   **Simulação Realista com Barreiras:** Executa a propagação da inundação a partir do litoral para o interior, garantindo a proteção por barreiras geográficas ao alagar apenas áreas com elevação menor ou igual ao nível do mar e com conexão contínua com o oceano.
*   **Cálculo de Impacto:** Estima o dano calculando a área total afetada em quilômetros quadrados.
*   **Visualização Gráfica:** Gera a sobreposição do mapa do terreno com o destaque visual das áreas afetadas pela inundação.

## 🛠 Tecnologias e Restrições de Arquitetura

O desenvolvimento seguiu as seguintes restrições técnicas:
*   **Linguagem:** Desenvolvido em **Python**, de forma imperativa (sem o uso de Orientação a Objetos).
*   **Banco de Dados:** Não utiliza nenhum modelo de banco de dados.
*   **Processamento de Dados Espaciais:** Leitura de dados territoriais no formato **.tiff** e dados de fronteira no formato **.shp**.
*   **Gráficos:** Visualização da área de análise modelada em um mapa de calor (*heatmap*).

## 🧩 Arquitetura de Módulos e Equipe

A aplicação foi estruturada seguindo o princípio da decomposição em **cinco módulos paralelos**:

*   **Módulo Principal** *(Desenvolvido por Rafaela Santos de Faria)*: Responsável por interagir com o usuário no terminal, executando funções como `obter_uf()` e `obter_elevacao()`.
*   **Módulo Água** *(Desenvolvido por João Pedro Capechi Telhado)*: Concentra a inteligência algorítmica para criar as máscaras de água e calcular a porcentagem de expansão do alagamento.
*   **Módulo Terreno** *(Desenvolvido por Maria Clara Padilha Pires)*: Encarregado da manipulação de arquivos geográficos, como carregar dados topográficos, ler polígonos de fronteira e aplicar a máscara de isolamento no terreno.
*   **Módulo Visualização** *(Desenvolvido por Gabriel Campos Correa de Araujo)*: Manipula as matrizes resultantes para projetar as camadas, gerando os objetos do *heatmap* e plotando os mapas de inundação.
*   **Módulo Validação** *(Desenvolvido por Oliver Hoerde Napoles)*: Módulo utilitário focado na verificação de regras de negócio e integridade estrutural. Possui funções para validar a entrada de UFs e elevações, além de checar a integridade de rasters, polígonos e tamanhos de matrizes.

## ✅ Convenção de Saídas (Erro/Êxito)

Para padronizar a sinalização de erro e êxito em **todos os módulos**, o projeto adota uma convenção única, dividida por tipo de função:

*   **Funções de ação / validação** (não produzem um dado de domínio — apenas validam ou executam um efeito): retornam um **código de status inteiro**.
    *   `0` → êxito;
    *   `≥ 1` → erro (cada função documenta seus códigos; `1` é o erro genérico quando não há subtipos).
    *   Exemplos: `valida_uf`, `valida_elevacao`, `projetar_camadas`, `plot_layers`, `carrega_dados`, `main`.
*   **Funções produtoras** (retornam um artefato — matriz, polígono, figura, tupla ou valor calculado): retornam o **objeto/valor** em caso de êxito e **`None`** em caso de falha esperada. **Não levantam exceção** para erros previsíveis (arquivo inexistente, formato inválido, parâmetro fora do domínio).
    *   Exemplos: `carregar_estado`, `cria_mascara_agua`, `expandir_mascara_agua`, `gerar_heatmap`, `obter_caminhos_arquivos`.

## 🧪 Testes

Os testes usam **pytest** e seguem uma convenção única de nomenclatura: cada módulo possui um arquivo `test_<modulo>.py` com funções `test_*`, cobrindo todos os casos de uso (êxito e erro) de cada função do módulo. Todo o I/O pesado (leitura de rasters/shapefiles, JSON e renderização do matplotlib) é **mockado**, de modo que a suíte não depende dos arquivos reais em `data/` nem do diretório de execução, e nenhum gráfico é aberto.

```bash
# Rodar toda a suíte de uma vez
pytest

# Rodar os testes de um módulo específico (em leva)
pytest src/agua
pytest src/terreno
pytest src/validacao
pytest src/visualizacao
pytest src/test_principal.py
```

A configuração fica em `pytest.ini` (raiz do projeto), que define `pythonpath = src` — assim os testes podem ser executados de qualquer diretório, sem ajustes manuais de `PYTHONPATH`.