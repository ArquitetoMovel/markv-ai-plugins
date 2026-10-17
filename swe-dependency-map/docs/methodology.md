# Metodologia e limites de cobertura

## Apoio conceitual

O material fornecido, `Architectural_Coupling_Science.pdf`, foi consultado visualmente em suas 15 páginas. As páginas 3 a 6 distinguem direção e impacto do acoplamento; a página 7 apresenta I; as páginas 8 a 11 relacionam abstração, sequência principal e Zona de Dor. O PDF não é redistribuído.

A Zona de Dor combina baixa abstração e baixa instabilidade: um componente concreto com consumidores pode afetar muitos componentes quando muda. A sequência principal satisfaz A + I = 1; a distância normalizada é D = |A + I - 1|. Consulte a [referência de Robert C. Martin](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf).

Os gráficos do anexo são ilustrativos, não dados de entrada nem uma especificação de cortes numéricos. Os limites 2, 0,2 e 0,8 são políticas ajustáveis deste plugin. Uma interface não comprova inversão de dependência ou isolamento efetivo.

## Unidades e direção

São produzidos **dois grafos independentes**:

| Linguagem | LIB/projeto | Módulo interno |
| --- | --- | --- |
| .NET | Cada `.csproj`, `.fsproj` ou `.vbproj` | Namespace C# dentro do projeto; `<global>` sem namespace |
| Java | Diretório com `pom.xml`, `build.gradle.kts` ou `build.gradle` | Package Java dentro do projeto |
| TypeScript | Diretório com `package.json` | Arquivo `.ts`, `.tsx`, `.mts` ou `.cts`, incluindo `.d.ts` |
| Python | Diretório com `pyproject.toml`, `setup.cfg` ou `setup.py` | Arquivo `.py`; `__init__.py` representa o package |
| Go | Diretório com `go.mod` | Package por diretório dentro do módulo Go |

Fontes sem manifest criam uma LIB sintética por linguagem na raiz. O proprietário é o projeto mais próximo do mesmo ecossistema. Múltiplos proprietários na mesma profundidade geram aviso e fonte omitida, inclusive dois `.csproj` que compartilham um diretório.

Manifests de um mesmo diretório têm prioridade POM > Gradle Kotlin > Gradle Groovy e pyproject > setup.cfg > setup.py. Alternativos são ignorados com aviso. Requirements básicos associados ao projeto são lidos separadamente.

`X → Y` significa que X depende de Y. CA/CE contam vizinhos distintos, não ocorrências, classes ou dependências transitivas. `A → B → C` não cria `A → C`. Relações internas à mesma LIB não contam nesse grafo, mas podem contar no grafo de módulos. Relações dentro do mesmo módulo são descartadas. Evidências diferentes são preservadas sem inflar as métricas.

Fronteiras sintáticas podem diferir dos módulos de negócio. Não há inferência de HTTP/RPC, filas, bancos, serviços, injeção em runtime ou dependências entre linguagens.

## Escopo das métricas

O grafo de LIBs reúne referências declaradas e imports que atravessam LIBs. Uma declaração não comprova uso efetivo. O grafo de módulos usa imports explícitos reconhecidos. As unidades não são intercambiáveis com ferramentas que contam classes acopladas.

Dependências externas declaradas usam pacote/distribuição/coordenada no grafo de LIBs. Imports externos usam módulo/package/namespace no grafo de módulos. Em Python, `PyYAML` e `yaml` são identidades distintas; em C#/Java, namespaces/packages externos não são adivinhados como NuGet/Maven. Os grafos não devem ser somados.

Por padrão, I usa CE interno. `--include-external` inclui CE externo observado. O escopo é registrado; comparações exigem o mesmo escopo.

Com CA + CE = 0, I é indeterminado. Com Nt = 0, A é indeterminado. Sem I/A, D e zonas são indeterminados. Bibliotecas somente com funções não recebem A = 0. Para dependências externas, CA é apenas o número de consumidores observados nesta raiz; I/A/D/zonas permanecem indeterminados.

Os limites usam valores completos, antes do arredondamento Markdown para quatro casas. JSON preserva ponto flutuante do Python. Zona de Dor padrão exige CA >= 2, I <= 0,2, A <= 0,2; possível abstração desperdiçada exige I >= 0,8 e A >= 0,8. Todos os cortes são inclusivos e configuráveis.

## Gráficos e relatórios

Toda execução produz JSON, Markdown, HTML e dois SVGs. O Markdown referencia `coupling-libraries.svg` e `coupling-modules.svg` na mesma pasta; o HTML incorpora os SVGs e a análise completa em um arquivo independente. Não usa JavaScript, CDNs, fontes externas ou rede. Dados da solução são escapados ao gerar HTML/SVG.

Os gráficos mantêm LIBs e módulos separados, com **X = I** e **Y = A**, escala de 0 a 1 em ambos os eixos. A diagonal tracejada liga (0,1) a (1,0): **A + I = 1**. Não há deslocamento artificial dos pontos.

O corte visual em **0,5** cria quatro quadrantes: concreto estável (região da Zona de Dor), abstrato estável (contratos centrais), concreto instável (detalhes/adaptadores) e abstrato instável (região da Zona de Inutilidade). O valor 0,5 pertence ao lado alto. Este corte apenas organiza a visualização; a identificação de risco continua usando CA e os limites configurados, sem arredondamento. Assim, estar no quadrante da Dor não equivale a atender à política de Dor. Vermelho identifica Dor detectada; âmbar Inutilidade detectada; azul os demais. Se políticas personalizadas se sobrepõem, vermelho tem prioridade visual e os dados preservam ambas as flags.

Cada marcador numerado corresponde aos componentes da tabela. Coordenadas exatamente iguais são agrupadas antes da formatação, em ordem de I/A e ID, com indicação “número · quantidade”. O detalhe do ponto no HTML/SVG lista todos os IDs e seus CA/CE. Links da tabela levam ao marcador. Coordenadas SVG usam seis casas decimais; valores muito próximos podem se sobrepor na escala, mas continuam identificados na tabela.

Nós internos com I ou A indeterminado ficam na tabela como **sem posição**. Nós externos ficam na seção de dependências externas; não recebem coordenadas fictícias. As classes reconhecidas contribuem para A da LIB/módulo; nenhum gráfico individual de dependências por classe é extraído.

## Coletores por linguagem

### .NET

- XML: `ProjectReference`, `PackageReference`, `Reference`, `packages.config`. Referências de projeto usam paths literais relativos ao manifest com barras Unix/Windows. `ReferenceOutputAssembly="false"` é omitido como dependência somente de build.
- Propriedades/curingas e referências fora da raiz não são resolvidos; geram aviso. Condições MSBuild usam união de referências literais, com aviso. Imports de props/targets, arquivos linked, seleção Compile e target frameworks não são avaliados.
- C#: tokens para `using`, aliases, static e namespaces. Nt inclui classes/records/structs/interfaces/enums; Na inclui interfaces e classes/records explicitamente abstratos. `record struct` conta uma vez. Tipos no mesmo namespace, contêiner e aridade genérica são deduplicados, inclusive `partial`.
- Sem binding semântico, usos totalmente qualificados ou expansão dos efeitos de `global using`. Múltiplos namespaces no arquivo são atribuídos ao primeiro com aviso. Strings raw/pré-processamento não são interpretados integralmente.
- F#/VB: grafo de LIBs declaradas disponível; fontes, módulos e abstração dessas linguagens não são extraídos.

As referências seguem os elementos descritos pela [Microsoft](https://learn.microsoft.com/en-us/dotnet/core/tools/dependencies). A leitura é uma fotografia parcial, não o grafo avaliado pelo MSBuild.

### Java

- Maven: grupo/artifact, grupo do parent, dependências diretas e propriedades locais literais. `dependencyManagement` não cria dependência usada. Herança completa e profiles não são avaliados, com aviso. Scope test exige `--include-tests`.
- Gradle: reconhece configurações usuais api/implementation/compileOnly/runtimeOnly/compile/runtime/annotationProcessor, coordenadas de string e project(...). Testes acrescentam configurações test usuais. Interpolação e expressões não literais geram aviso.
- Paths de project `:a:b` são relativos ao settings mais próximo. Não avalia projectDir personalizado, catalogs, includeBuild, plugins ou código Gradle.
- Imports de tipos, wildcard e static resolvem para packages conhecidos. Desambiguação usa proprietário/referências declaradas; se persistir ambiguidade, relação omitida com aviso.
- Nt inclui classes/interfaces/enums/records, incluindo aninhados. Na inclui interfaces e classes/records marcados abstract. Não avalia JPMS, todos os nomes sem import ou binding semântico.

Referências: [POM](https://maven.apache.org/pom.html) e [dependências Gradle](https://docs.gradle.org/current/userguide/declaring_dependencies_basics.html).

### TypeScript

- package.json: dependencies, peerDependencies, optionalDependencies; devDependencies com testes. Imports explícitos continuam observados mesmo que o pacote só esteja em devDependencies.
- Imports de valor/tipo/efeito colateral, reexports, import-equals/require e import dinâmico literal. Argumentos dinâmicos não literais geram aviso.
- Resolução local aproximada: relativo, extensões, index, `.js → .ts/.tsx/.d.ts`, `.mjs → .mts/.d.mts`, `.cjs → .cts/.d.cts`.
- tsconfig JSONC: extends local simples, baseUrl e paths; aliases herdadas preservam sua origem relativa. Não avalia extends de pacote ou múltiplos extends.
- Packages locais por nome: entradas literais types/main, exports exatos e seleção simples types/import/default. Não reproduz todos os modos, wildcard exports, condições ou aliases de bundler.
- Nt inclui interfaces/classes/enums/aliases type; Na inclui interfaces e classes explicitamente abstratas. Aliases contam como não abstratos neste proxy, mesmo quando podem atuar como contratos estruturais. `import type Foo` não declara um tipo.
- `.d.ts` conta como fonte de contratos; para excluí-los use filtros e mantenha o escopo estável entre comparações.

O coletor não substitui os resolvedores descritos na [documentação TypeScript](https://www.typescriptlang.org/docs/handbook/modules/reference).

### Python

- AST sem executar imports. Sintaxe não aceita pelo runtime gera aviso e fonte omitida. Raízes: src/, projeto e python_roots adicionais relativos à solução.
- import/from/relativos; nomes importados criam uma relação adicional só quando um submódulo existe. Namespace packages são resolvidos por submódulos explícitos. Inicialização implícita dos packages pai não é expandida.
- Nt inclui classes; Na reconhece marcadores explícitos ABC, ABCMeta, Protocol e abstractmethod, incluindo aliases importados. Não simula metaclasses ou `__abstractmethods__`; implementação que herda contrato não vira abstrata automaticamente.
- PEP 621, Poetry básico, setup.cfg e requirements.txt, incluindo -r locais. Não executa setup.py, extras, grupos de desenvolvimento ou metadados dinâmicos. Marcadores de ambiente não são avaliados; referências literais são observadas.
- Import externo usa o primeiro segmento. Só acrescenta evidência a uma distribuição declarada quando os nomes normalizados coincidem; não adivinha PIL → Pillow ou yaml → PyYAML.
- Imports dinâmicos, sys.path em runtime e plugins não são resolvidos.

Parser baseado na [API AST pública](https://docs.python.org/3/library/ast.html), usando o runtime local sem instalar dependências da solução.

### Go

- Todos os go.mod elegíveis sob a raiz, independentemente da seleção de go.work. Lê module e require (linha/bloco); a raiz define o universo analisado.
- Imports literais, aliases, efeito colateral e blocos; packages por diretório. Imports externos acrescentam evidência ao require cujo prefixo de módulo é mais específico.
- Nt: tipos nomeados/aliases; Na: declarações interface. Reconhece grupos e parâmetros genéricos usuais. Não infere implementações implícitas ou separa todos os constraints de contratos de runtime.
- Build tags, GOOS/GOARCH, cgo, replace e código gerado não são avaliados: união dos arquivos elegíveis pode incluir variantes mutuamente exclusivas.

Imports e deps transitivas são conceitos distintos na [ferramenta oficial Go](https://pkg.go.dev/cmd/go). O motor não executa go list nem downloads.

## Filtros e reprodutibilidade

Symlinks não são seguidos. Ignora `.git`, `.hg`, `.svn`, `node_modules`, `bin`, `obj`, `target`, `build`, `dist`, `.venv`, `venv`, `__pycache__`, `.gradle`, `.idea`, caches Python, `vendor`, `coverage`, `.dependency-map` e a própria pasta de saída. Os filtros desses diretórios são fixos.

Sem include-tests, omite diretórios test/tests/__tests__/__mocks__, `*_test.go`, `test_*.py`, `*.test.ts/tsx/mts/cts`, `*.spec.ts/tsx/mts/cts`. Convenções C#/Java como Api.Tests ou *Test.java exigem globs explícitos. Include-tests retira filtros de teste e acrescenta seções reconhecidas, não todas as configurações possíveis de build.

Globs operam sobre paths relativos POSIX com fnmatch, sensível a maiúsculas. `*` pode atravessar `/`; `**` não é um operador especial. `generated/**` filtra árvore na raiz, `**/generated/**` árvore aninhada. `**/*.g.cs` filtra arquivos aninhados; acrescente `*.g.cs` para arquivos na raiz.

Nós, relações, evidências, ciclos, avisos e listas são ordenados; artefatos não contêm relógio, paths absolutos ou dados do ambiente. Fixe plugin/runtime, configuração e árvore elegível para comparação byte a byte. O teste de integração varia PYTHONHASHSEED e repete a CLI com a saída presente na árvore.

## Diagnóstico e cobertura

O Markdown e o HTML gerados pelo script já contêm análise do acoplamento. O agente pode acrescentar interpretação contextual sem recalcular métricas. São priorizados Zona de Dor, maiores CA/CE, possível abstração desperdiçada, ciclos e direção de estabilidade.

Ciclos são componentes fortemente conexos com mais de um nó; não enumeram todos os caminhos possíveis. A travessia é iterativa, inclusive acima do limite de recursão Python. I(origem) < I(destino) sugere revisar dependências estáveis, sem comprovar erro de design.

JSON sempre contém `coverage: partial_static`. Erros de leitura, manifests inválidos e resolução limitada podem reduzir cobertura e subestimar CA/CE. Import tem linha lexical/AST; referências de manifest sem posição específica usam linha 1 para identificar o documento de origem. O relatório não garante completude semântica.
