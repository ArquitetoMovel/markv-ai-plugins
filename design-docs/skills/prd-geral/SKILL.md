---
name: prd-geral
description: >
  Use esta skill quando o usuário pedir para criar um PRD Geral, um documento
  de alto nível sobre o produto como um todo (visão, objetivos, escopo,
  estratégia, stakeholders). Ativa para "PRD geral", "PRD do produto",
  "documento de visão do produto", "requisitos gerais do produto".
---

# prd-geral — PRD de Produto (visão de alto nível)

## Objetivo da skill

Conduzir uma entrevista estruturada com o usuário para gerar um **PRD Geral**, um documento de alto nível que descreve a visão, os objetivos e o escopo do produto como um todo. O PRD Geral é usado para alinhar as partes interessadas e orientar o desenvolvimento do produto.

## Princípios de entrevista

Aplique rigorosamente estes princípios durante toda a coleta:

- Faça uma pergunta por vez e aguarde a resposta.
- Não faça perguntas duplas.
- Use linguagem simples e direta em português.
- Não use travessões do tipo "—" em nenhuma saída.
- Se o usuário não souber responder, ofereça de duas a três opções plausíveis marcadas como hipótese.
- Ao final de cada bloco lógico, faça um resumo curto de três a seis linhas com o que entendeu e peça confirmação antes de seguir.
- Se houver inconsistência entre respostas, avise e peça correção antes de continuar.
- Não invente detalhes que o usuário não deu. Inferências derivadas do repositório devem ser marcadas como hipótese.

## Perguntas-guia

Você deve capturar respostas claras para cada uma destas perguntas, uma por vez:

1. Por que esse produto existe?
2. O que queremos alcançar com esse produto?
3. O que esse projeto vai entregar e o que não vai?
4. Para quem estamos construindo isso?
5. Qual é o problema que esse produto resolve e por que ele importa?
6. Como pretendemos alcançar os objetivos?
7. O que o produto deve ser capaz de fazer em linhas gerais?
8. Como saberemos se o produto deu certo?
9. O que pode dar errado e como vamos lidar com isso?
10. Qual é o roadmap desse projeto?
11. Quem está envolvido e qual é o papel de cada um?
12. Como esse produto se conecta à estratégia da empresa?

## Enriquecimento a partir do repositório

Caso a skill esteja sendo executada dentro de um repositório Git do próprio produto, você pode usar as seguintes fontes para enriquecer o PRD, sempre confirmando com o usuário antes de incorporar a informação ao documento:

- **Histórico de commits** via `git log` para entender marcos e direção recente do produto.
- **Issues e pull requests** do repositório para identificar problemas recorrentes, prioridades e stakeholders ativos.
- **Arquivos-fonte e READMEs** para extrair descrição técnica, integrações existentes e capacidades já implementadas.

Qualquer informação derivada dessas fontes que não tenha sido validada pelo usuário deve aparecer no PRD marcada como hipótese.

## Checagens antes de finalizar

Antes de gerar o PRD final, confirme que:

- Existe uma visão clara do "porquê" do produto.
- Os objetivos estão associados a indicadores de sucesso.
- Está claro o que está dentro e fora do escopo.
- Há pelo menos um risco mapeado com mitigação associada.
- Os stakeholders principais foram identificados.
- O roadmap tem, no mínimo, a ordenação das próximas fases.

## Formato de saída do PRD Geral

Gere o PRD em Markdown seguindo exatamente esta estrutura. Substitua os placeholders entre colchetes pelas respostas coletadas. Não acrescente seções não previstas. Não omita seções obrigatórias.

```markdown
# Documento de Requisitos de Produto (PRD) - [Nome do Produto]

- Data de criação: [Data]
- Autor: [Nome do Autor]

## Visão e proposito
[Resposta à pergunta "Por que esse produto existe?"]

## Contexto e oportunidades
[Resposta à pergunta "O que queremos alcançar com esse produto?"]

## Público e personas
[Resposta à pergunta "Para quem estamos construindo isso?"]

## Objetivos e métricas
[Resposta à pergunta "Como saberemos se o produto deu certo?"]

## Escopo
[Resposta à pergunta "O que esse projeto vai entregar e o que não vai?"]

## Requisitos de alto nível (capacidade macro que o produto deve oferecer)
[Resposta à pergunta "O que o produto deve ser capaz de fazer em linhas gerais?"]

## Estratégia e fases
[Resposta à pergunta "Como pretendemos alcançar os objetivos?"]

## Riscos e mitigação
[Resposta à pergunta "O que pode dar errado e como vamos lidar com isso?"]

## KPIs
[Resposta à pergunta "Qual é o roadmap desse projeto ?"]

## Stakeholders
[Resposta à pergunta "Quem está envolvido e qual é o papel de cada um?"]
```

## Mensagem inicial sugerida

Ao abrir a entrevista para o PRD Geral, envie uma mensagem como esta:

> Perfeito. Vamos montar um PRD Geral do produto. Vou fazer algumas perguntas uma por vez para entender a visão, o público, os objetivos, o escopo, a estratégia, os riscos, o roadmap e os stakeholders. Para começar, por que esse produto existe?
