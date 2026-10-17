# swe-dependency-map-plugin

Mapeia dependências entre **LIBs/projetos e módulos** em soluções **.NET, Java, TypeScript, Python e Go**. Calcula CA, CE, instabilidade, abstração, distância da sequência principal e candidatos à Zona de Dor, e gera um **relatório de análise do acoplamento** com evidências.

Compatível com Claude Code, GitHub Copilot CLI e Cursor. Scripts Python compartilhados fazem os cálculos offline e determinísticos; a IA interpreta os resultados.

## Instalação

```bash
# Claude Code
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install swe-dependency-map-plugin@markv-ai-plugins

# GitHub Copilot CLI
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install swe-dependency-map-plugin
```

Cursor: importe `ArquitetoMovel/markv-ai-plugins` em **Dashboard → Settings → Plugins → Team Marketplaces → Import** e selecione o plugin.

Pré-requisito: **Python 3.11+**. Sem pacotes pip, SDKs das linguagens, restore, build ou execução do código analisado.

## Fluxo de uso

Peça ao agente `dependency-analyzer` ou invoque a skill `swe-dependency-map-plugin:dependency-map`:

```text
Analise o acoplamento da solução nesta pasta com swe-dependency-map.
Calcule dependências aferentes/eferentes de LIBs e módulos,
identifique a Zona de Dor e gere o relatório com evidências.
```

O agente localiza a skill instalada, executa os scripts e entrega os arquivos gerados com uma síntese dos componentes críticos e dos limites de cobertura. A skill contém o conhecimento canônico, fórmulas e regras de interpretação.

## Execução direta

Na raiz de um checkout deste marketplace:

```bash
python3 swe-dependency-map/skills/dependency-map/scripts/dependency_map.py \
  --root /caminho/da/solucao
```

Quando instalado, use o path absoluto de `skills/dependency-map/scripts/dependency_map.py` dentro do plugin. Não precisa copiar o motor para a solução.

Saída padrão:

```text
/caminho/da/solucao/.dependency-map/
├── dependencies.json
├── report.md
├── report.html
├── coupling-libraries.svg
└── coupling-modules.svg
```

- **dependencies.json:** grafos, métricas, consumidores/destinos, ciclos, configuração, evidências e avisos.
- **report.md:** análise em pt-BR com gráficos de quatro quadrantes, tabelas, Zona de Dor, criticidade aferente, exposição eferente, ciclos, direção de estabilidade, recomendações de revisão, evidências e limitações. Mantenha os SVGs junto ao Markdown para exibir os gráficos.
- **report.html:** a mesma análise com gráficos SVG incorporados, navegação por seção, pontos com detalhes ao passar o cursor e links da tabela para o gráfico. Arquivo independente, offline, responsivo e imprimível, sem JavaScript ou recursos externos.
- **coupling-libraries.svg / coupling-modules.svg:** gráficos vetoriais separados para LIBs e módulos, reutilizáveis em documentos.

Veja os exemplos em [Markdown](docs/example-report.md) e [HTML](docs/example-report.html), com seus [dados JSON](docs/example-dependencies.json), gerados de uma solução sintética .NET. Não representam uma solução real. Abra o HTML no navegador para consultar os gráficos e os pontos.

Opções:

```bash
python3 swe-dependency-map/skills/dependency-map/scripts/dependency_map.py \
  --root /caminho/monorepo \
  --languages dotnet,java,typescript,python,go \
  --output /caminho/reports/dependencies \
  --config swe-dependency-map/docs/config.example.json \
  --exclude 'generated/**' \
  --exclude '**/*.g.cs'
```

- `--include-tests`: fontes e dependências de teste reconhecidas.
- `--include-external`: inclui CE externo observado em I; por padrão I usa CE interno.
- `--exclude`: glob relativo à raiz, repetível. `python_roots` em JSON acrescenta raízes de import Python relativas à solução.
- `--fail-on-pain`: código 3 para Zona de Dor; `--fail-on-cycle`: código 4 para ciclos. Se ambos ocorrerem, 3 prevalece. Relatórios são escritos antes de retornar esses códigos.
- Código 0: execução concluída; 2: configuração/I/O inválidos. Avisos de análise parcial permanecem nos relatórios.

## Métricas

| Métrica | Significado |
| --- | --- |
| CA | Componentes distintos que dependem deste componente |
| CE interno | Componentes internos distintos dos quais depende |
| CE externo | Dependências externas distintas observadas neste grafo |
| I | CE / (CA + CE), com escopo de CE registrado |
| A | Tipos abstratos reconhecidos / tipos totais reconhecidos |
| D | \|A + I - 1\|, distância normalizada da sequência principal |
| Zona de Dor | CA suficiente, I baixo e A baixo segundo limites configurados |

Uma relação conta uma vez; vários imports acrescentam evidências sem inflar CA/CE. LIBs e módulos têm grafos separados e unidades próprias por linguagem.

Zona de Dor inicial: **CA >= 2, I <= 0,2 e A <= 0,2**. São políticas configuráveis do plugin, não cortes prescritos pelo anexo. Valores altos ou uma zona detectada não comprovam isoladamente defeito arquitetural.

Componente isolado tem I indeterminado. Sem tipos, A é indeterminado. Sem I/A, D e zonas são indeterminados. Bibliotecas externas sem fontes mostram consumidores observados sem cálculo de sua Zona de Dor.

## Gráfico de quatro quadrantes

Cada componente interno com métricas suficientes aparece nas coordenadas **X = I** e **Y = A**, em escala de 0 a 1. I reflete as dependências CA/CE; A reflete a proporção de tipos abstratos. A diagonal tracejada representa **A + I = 1**.

| Quadrante (corte visual em 0,5) | Região |
| --- | --- |
| A baixo, I baixo | Concreto estável — região da Zona de Dor |
| A alto, I baixo | Abstrato estável — contratos centrais |
| A baixo, I alto | Concreto instável — detalhes e adaptadores |
| A alto, I alto | Abstrato instável — região da Zona de Inutilidade |

O corte em 0,5 organiza a visualização; a detecção de Dor/Inutilidade usa os limites configurados e valores completos. Pontos vermelhos atendem à política de Dor; pontos âmbar à de Inutilidade; demais pontos são azuis. I/A = 0,5 pertence ao lado alto. A região de um quadrante não comprova defeito.

Os números dos pontos correspondem à tabela. Componentes com coordenadas idênticas compartilham um marcador “número · quantidade”, que lista todos os componentes no detalhe do ponto. As posições não sofrem deslocamento artificial. Componentes sem I/A ficam na tabela como **sem posição**; externos aparecem em sua seção. Classes contribuem para A da LIB/módulo; o coletor não calcula CA/CE individual por classe.

## Cobertura

| Stack | Entrada e fronteiras |
| --- | --- |
| .NET | Referências de csproj/fsproj/vbproj; namespaces, imports e tipos C# |
| Java | Maven/Gradle literais; packages, imports e tipos Java |
| TypeScript | package.json, aliases locais tsconfig; imports/reexports/require e tipos por arquivo |
| Python | pyproject/setup.cfg/requirements; AST de imports/classes e packages |
| Go | go.mod, imports, tipos nomeados e interfaces por diretório |

Extração estática parcial: não avalia builds condicionais, todos os resolvedores de compilador, reflection, runtime ou comunicações entre serviços. A é um proxy sintático específico da linguagem. Consulte a [metodologia](docs/methodology.md) para regras, filtros e limitações. O PDF fornecido foi consultado, sem redistribuição.

## Estrutura

```text
swe-dependency-map/
├── .claude-plugin/plugin.json
├── .cursor-plugin/plugin.json
├── plugin.json
├── agents/dependency-analyzer.md
├── copilot-agents/dependency-analyzer.agent.md
├── skills/dependency-map/
│   ├── SKILL.md
│   └── scripts/
│       ├── dependency_map.py
│       ├── collectors.py
│       ├── metrics.py
│       ├── visuals.py
│       └── html_report.py
├── docs/
│   ├── methodology.md
│   ├── config.example.json
│   ├── example-report.md
│   ├── example-report.html
│   ├── example-dependencies.json
│   ├── coupling-libraries.svg
│   └── coupling-modules.svg
├── tests/
│   ├── test_dependency_map.py
│   ├── test_packaging.py
│   └── test_reports.py
└── README.md
```

## Verificação

```bash
python3 -m unittest discover -s swe-dependency-map/tests -v
```

Testes usam soluções temporárias, sem builds/downloads. Cobrem as cinco linguagens, grafos, ciclos, aliases, partial C#, filtros, indeterminados, códigos de saída, coordenadas dos quadrantes, pontos coincidentes, escape de dados no HTML/SVG e igualdade byte a byte de JSON, Markdown, HTML e SVGs.

Autor: Alexandre Danelon. Licença MIT, conforme o marketplace.
