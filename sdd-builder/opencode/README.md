# SDD Builder para OpenCode

Adaptação do `sdd-builder` 1.5.0 para **OpenCode 2.2.6**, com 13 agentes, seis skills
canônicas, uma skill de adaptação e cinco comandos. Requer Node.js 22+ e Git nos
projetos que receberão implementação. O workspace neutro de uma solução não exige Git.

## Instalação local

No checkout deste repositório:

```bash
cd sdd-builder/opencode
npm ci
npm run build
node dist/cli.js install --project /caminho/do/projeto --dry-run
node dist/cli.js install --project /caminho/do/projeto
```

O caminho absoluto deste pacote fica em `plugins` no `opencode.json(c)` do projeto.
Mantenha o checkout no mesmo local ou execute novamente o instalador após movê-lo.
Os perfis ficam em `.opencode/agents/`; hashes ficam em `.opencode/sdd-builder-install.json`.
O instalador preserva comentários JSONC, configurações alheias e o agente padrão.
Não adota agentes existentes, não sobrescreve modificações pessoais e não instala
globalmente. Com dois arquivos de configuração na raiz, exige consolidação prévia.
Configurações herdadas ou em `.opencode/opencode.json(c)` também podem afetar o host;
confira `opencode debug config` se o plugin não aparecer.

Reabra o OpenCode depois de instalar/atualizar. O carregamento de plugins é assíncrono;
aguarde o registro antes de usar os comandos. Se o projeto fizer parte de uma solução,
instale no workspace comum para que os participantes herdem a configuração, ou instale
em cada projeto. Selecionar um agente especialista exige uma sessão filha.

## Uso

- `/sdd`: diagnóstico e roteamento da jornada.
- `/sdd-prd`: PRD e roadmap.
- `/sdd-spec`: specs, planos e casos de teste.
- `/sdd-feature`: implementação da feature e validação por fase.
- `/sdd-solution`: coordenação multiprojeto com contratos e réplicas.

Os comandos selecionam o coordenador na sessão atual e preservam argumentos/anexos.
A linguagem do plugin é pt-BR; os artefatos do produto seguem o idioma definido pelo
contrato canônico do PRD. Leia o [fluxo completo](../README.md) para os requisitos de cada etapa.

`sdd_models` consulta o catálogo da conta. O usuário escolhe modelos independentes
para programação e testes, como `providerID/modelID` ou `inherit`; não há provedor
fixo nem substituição silenciosa. IDs com variante ainda não são aceitos pelo adaptador.

`sdd_dispatch` recebe agente, diretório absoluto, modelo e pacote mínimo. Para editar,
exige `gitRoot` absoluto validado por Git. Sem ele, a sessão nega edição e shell.
Cada filho tem contexto novo e não delega: o root executa o protocolo de planejamento,
despacho direto e revisão isolada previsto para hosts sem delegação aninhada.

Há três slots globais por usuário/máquina, inclusive entre processos. Unidades mutáveis
no mesmo Git, inclusive worktrees, são serializadas. Conflitos retornam bloqueio para o
coordenador aguardar os trabalhos ativos. Não há fila nem retry automático.
O root também deve aguardar writers antes de editar, commitar ou publicar réplicas.
Locks dos roadmaps e soluções continuam seguindo as skills canônicas.

Cancelamentos interrompem a sessão filha. Se não for possível confirmar seu término,
os locks são preservados. Para recuperar após crash, consulte os `owner.json` em
`$TMPDIR/opencode-sdd-builder-locks/` (ou diretório temporário do sistema), identifique
sessão/pid, confirme que nenhum writer continua ativo e reconcilie arquivos, tarefas e
commits antes de remover **somente** o lock correspondente. Não há expiração automática.
As sessões preservam as evidências; os roadmaps mantêm seus schemas portáveis.

## Atualização e remoção

```bash
npm ci
npm run build
node dist/cli.js install --project /caminho/do/projeto
node dist/cli.js uninstall --project /caminho/do/projeto --dry-run
node dist/cli.js uninstall --project /caminho/do/projeto
```

A remoção preserva arquivos/configurações alheios. Se um perfil gerenciado ou a entrada
do plugin foi modificado, ela interrompe antes de escrever e pede reconciliação manual.

## Pacote npm

O pacote está preparado para publicação; não foi publicado por esta implementação.
Depois de publicado, a instalação será:

```bash
npx --yes opencode-sdd-builder@1.5.0 install --project /caminho/do/projeto --npm
```

`--npm` grava `opencode-sdd-builder@1.5.0`, sem depender do cache temporário do npx.
Para testar antes da publicação, use `npm pack`, instale o tarball em um diretório
externo e execute seu binário sem `--npm`, mantendo essa instalação disponível.

## Desenvolvimento e validação

```bash
npm run check
npm test
npm run test:integration
npm pack
```

O build converte frontmatter dos agentes existentes e copia as skills/referências;
não edite `dist`. Os corpos canônicos são preservados e recebem instruções do host.
O teste integrado requer o binário OpenCode 2.2.6 e acesso ao registro npm. Instala um
tarball fora do checkout e inicia servidor com diretórios XDG temporários, sem usar
credenciais pessoais nem chamar modelos. Confere plugin ativo, agentes, skills,
comandos e sessão filha sem histórico.

Os testes de runtime simulam modelos, permissões, cancelamento e concorrência.
Eles não demonstram a qualidade de uma execução completa PRD → implementação com LLM.
Para homologação funcional, execute os cenários de `../docs/validation-solution.md`
com provedores configurados, incluindo integração ponta a ponta e retomada após falha.
Não se declara compatibilidade V1 nem com outras versões do OpenCode.

O SDK 2.2.6 traz dependências transitivas com alertas moderados no `npm audit`.
A versão do SDK fica fixada para manter o contrato do host; upgrades exigem repetir
os testes integrados. A aplicação não possui build global nem modifica os manifests
Claude Code, Copilot CLI ou Cursor.

Referências: [plugins](https://opencode.ai/docs/build/plugins/),
[API servidor](https://opencode.ai/docs/build/plugins/server/),
[agentes](https://opencode.ai/docs/agents/), [permissões](https://opencode.ai/docs/permissions/).
