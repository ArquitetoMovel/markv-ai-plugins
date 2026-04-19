# Definição da criação de agentes personalizados para o plugin

## Introdução

O plugin *dotnet-unity-tests-plugin* deverá contar com alguns agentes customizados para auxiliar no processo de revisão, criação e manutenção dos testes unitários votados para plataforma **dotnet**.
A seguir, temos os detalhes dos agentes customizados que deverão ser criados.

### dotnet-tester-reviewer

O agente *dotnet-tester-reviewer*, deverá ter sólidos conhecimentos em frameworks de testes e mocks.
O papel do agente *dotnet-tester-reviewer* é fazer um deep dive na solução **.NET** com objetivo de identificar os seguintes pontos da solução e projetos relacionados.

- Levantar e documentar a versão do **dotnet** referente aos projetos da solução Ex: **net8+** ou **net472**.
- Inspecionar projetos de testes existentes e percentual de cobertura da solução.
- Fazer uso da SKILL adequada de acordo com a versão do **dotnet** presente nos projetos da solução indicando *MSTest* para **net472** e *xUnit* para **net8+**.
- Deverá gerar uma especificação e um plano de execução para:
        - Planejar a criação de novos casos de testes para um projeto de testes existente.
        - Planejar a modernização de projetos *MSTest v2* para **MSTest V3**.
        - Planejar a criação de projeto de testes para soluções **dotnet** sem projetos de testes unitários.
        - Sugerir exclusão de cobertura para componentes de infraestrutura e inicialização das aplicações.

### dotnet-tester-creator

O agente *dotnet-tester-creator*, deverá ter sólidos conhecimentos em *dotnet*, *csharp*, *xUnit*, *MSTest* e boas praticas de desenvolvimento de testes unitários.
Procura sempre variar os testes com *InlineData*, *DataRow* com objetivo de evitar mutantes.
Poderá fazer uso de skills para entender como criar os projetos e casos de testes de forma adequada de acordo com a versão do **dotnet** e framework de testes.
O papel do agente *dotnet-tester-creator* é ler a especificação e plano gerado pelo *dotnet-tester-reviewer* e seguir com as implementações.

- Deverá utilizar ferramentas de terminal para garantir que o projeto compila e os testes rodam como `dotnet build` e `dotnet test`.
- Deverá garantir uma cobertura minima de 80%.

### dotnet-tester-planner

O agente *dotnet-tester-planner* é responsável por **decompor** o `test-plan.md` gerado pelo *dotnet-tester-reviewer* em múltiplos arquivos `<NomeProjeto>.plan.md`, um por unidade paralelizável.

- Lê a seção 3 (Plano de Ação por Projeto) e a seção 4 (Ordem de Execução Recomendada) do plano mestre.
- Deriva metadados de dependência a partir da coluna "Pode Paralelizar Com" e da prioridade.
- Gera frontmatter YAML em cada `*.plan.md` com os campos `session`, `projeto`, `tipo`, `framework`, `skill`, `prioridade`, `depende-de`, `pode-paralelizar-com`.
- **Nunca** escreve código de teste nem executa comandos `dotnet`.
- Todos os `*.plan.md` são gravados dentro do `session-dir` informado no prompt.

### dotnet-tester-coordinator

O agente *dotnet-tester-coordinator* é o ponto de entrada do plugin. Ele orquestra o pipeline completo em quatro fases:

1. **Setup de sessão**: localiza o `.sln`, gera `session-id` (timestamp UTC no formato `YYYYMMDD-HHmmss`) e cria `<solution-root>/.dotnet-unity-tests/<session-id>/`.
2. **Reviewer**: invoca *dotnet-tester-reviewer* para produzir `test-plan.md` dentro do `session-dir`.
3. **Planner**: invoca *dotnet-tester-planner* para particionar o plano em `*.plan.md` individuais.
4. **Creators em ondas**: dispara instâncias de *dotnet-tester-creator* **em paralelo** por onda, respeitando o grafo de dependências derivado do frontmatter de cada `*.plan.md`. Cada creator grava um `<NomeProjeto>.result.md` no `session-dir`.

Ao final, o coordinator consolida todos os `*.result.md` em `<session-dir>/summary.md` e reporta ao usuário: projetos concluídos, cobertura global, falhas.

Todos os artefatos da sessão ficam isolados em `.dotnet-unity-tests/<session-id>/`, permitindo múltiplas execuções coexistirem na mesma solução.
