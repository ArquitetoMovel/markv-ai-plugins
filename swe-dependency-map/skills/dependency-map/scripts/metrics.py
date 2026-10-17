"""Grafo e métricas determinísticas. Apenas biblioteca padrão do Python."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from visuals import point_numbers


@dataclass
class Node:
    id: str
    name: str
    language: str
    kind: str
    path: str
    library: str | None = None
    external: bool = False
    total_types: int = 0
    abstract_types: int = 0
    files: set[str] = field(default_factory=set)


class Graph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str], set[tuple[str, int, str]]] = {}

    def add(self, source: str, target: str, path: str, line: int, reason: str):
        if source != target:
            self.edges.setdefault((source, target), set()).add((path, line, reason))

    def cycles(self) -> list[list[str]]:
        """Componentes fortemente conexos, sem recursão ou limite de profundidade."""
        ids = sorted(k for k, n in self.nodes.items() if not n.external)
        out = {k: [] for k in ids}
        rev = {k: [] for k in ids}
        for a, b in sorted(self.edges):
            if a in out and b in out:
                out[a].append(b)
                rev[b].append(a)
        seen, order = set(), []
        for start in ids:
            if start in seen:
                continue
            seen.add(start)
            stack = [(start, iter(out[start]))]
            while stack:
                vertex, children = stack[-1]
                child = next(children, None)
                if child is None:
                    order.append(vertex)
                    stack.pop()
                elif child not in seen:
                    seen.add(child)
                    stack.append((child, iter(out[child])))
        seen, groups = set(), []
        for start in reversed(order):
            if start in seen:
                continue
            seen.add(start)
            group, stack = [], [start]
            while stack:
                vertex = stack.pop()
                group.append(vertex)
                for child in rev[vertex]:
                    if child not in seen:
                        seen.add(child)
                        stack.append(child)
            if len(group) > 1:
                groups.append(sorted(group))
        return sorted(groups)

    def export(self, thresholds: dict, include_external: bool) -> dict:
        incoming = {k: set() for k in self.nodes}
        outgoing = {k: set() for k in self.nodes}
        for a, b in self.edges:
            incoming[b].add(a)
            outgoing[a].add(b)
        rows = []
        for key, n in sorted(self.nodes.items()):
            internal_out = sorted(k for k in outgoing[key] if not self.nodes[k].external)
            external_out = sorted(k for k in outgoing[key] if self.nodes[k].external)
            ca = len(incoming[key])
            ce = len(internal_out) + (len(external_out) if include_external else 0)
            instability = ce / (ca + ce) if ca + ce and not n.external else None
            abstraction = n.abstract_types / n.total_types if n.total_types and not n.external else None
            distance = abs(abstraction + instability - 1) if abstraction is not None and instability is not None else None
            pain = None if distance is None else (
                ca >= thresholds['pain_min_ca']
                and instability <= thresholds['pain_max_i']
                and abstraction <= thresholds['pain_max_a'])
            useless = None if distance is None else (
                instability >= thresholds['useless_min_i']
                and abstraction >= thresholds['useless_min_a'])
            rows.append(dict(
                id=key, name=n.name, language=n.language, kind=n.kind, path=n.path,
                library=n.library, external=n.external, files=sorted(n.files),
                ca=ca, ce=ce, ce_internal=len(internal_out), ce_external=len(external_out),
                instability=instability, abstractness=abstraction, distance=distance,
                pain_zone=pain, uselessness_zone=useless,
                total_types=n.total_types, abstract_types=n.abstract_types,
                afferent=sorted(incoming[key]), efferent_internal=internal_out,
                efferent_external=external_out,
                metric_status='observed_consumers_only' if n.external else 'static_observation',
            ))
        edges = [dict(source=a, target=b, evidence=[
            dict(path=p, line=line, reason=reason) for p, line, reason in sorted(ev)])
            for (a, b), ev in sorted(self.edges.items())]
        by_id = {n['id']: n for n in rows}
        violations = []
        for a, b in sorted(self.edges):
            i, j = by_id[a]['instability'], by_id[b]['instability']
            if i is not None and j is not None and i < j:
                violations.append(dict(source=a, target=b, source_i=i, target_i=j))
        return dict(nodes=rows, edges=edges, cycles=self.cycles(), stability_violations=violations)


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def markdown(report: dict) -> str:
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ').replace('`', "'")

    def number(value):
        return 'indeterminado' if value is None else f'{value:.4f}'

    def zone(value):
        return 'indeterminada' if value is None else ('sim' if value else 'não')

    lines = ['# Análise do acoplamento', '',
             'Relatório gerado por análise estática determinística. Relação `origem → destino` significa que a origem depende do destino.', '',
             '## Escopo e método', '',
             f"- Linguagens: {', '.join(report['config']['languages'])}.",
             f"- CE usado em I: {'interno + externo observado' if report['config']['include_external'] else 'somente interno'}.",
             '- CA e CE contam vizinhos distintos, não ocorrências, tipos ou dependências transitivas.',
             '- I = CE / (CA + CE); A = tipos abstratos / tipos totais; D = |A + I - 1| (distância normalizada).',
             '- I de componente isolado, A sem tipos e métricas sem código de bibliotecas externas são indeterminados.',
             '- A é uma aproximação sintática específica de cada linguagem; não mede a qualidade dos contratos.',
             '- Os valores refletem o escopo observado. Referências não resolvidas podem subestimar CA/CE.', '',
             '### Limites configurados', '', '```json', canonical_json(report['config']['thresholds']).rstrip(), '```', '',
             'Os limites das zonas são políticas configuráveis deste plugin, não cortes definidos pelo material de apoio.', '']
    for level, label in [('libraries', 'LIBs e projetos'), ('modules', 'Módulos internos')]:
        graph = report[level]
        nodes = [n for n in graph['nodes'] if not n['external']]
        point_ids = point_numbers(graph)
        lines += [f'## {label}', '',
                  f"{len(nodes)} componentes internos; {len(graph['edges'])} relações observadas; {len(graph['cycles'])} ciclos (grupos fortemente conexos).", '',
                  f'![Quadrantes de acoplamento: {label}](coupling-{level}.svg)', '',
                  'Eixo X: instabilidade I, calculada por CA/CE. Eixo Y: abstração A, calculada pelos tipos reconhecidos. Linha tracejada: A + I = 1.', '',
                  'Os quatro quadrantes usam corte visual em 0,5: concreto estável (região da Zona de Dor), abstrato estável (contratos centrais), concreto instável (detalhes/adaptadores) e abstrato instável (região da Zona de Inutilidade). Valores iguais a 0,5 pertencem ao lado alto de cada eixo. O quadrante não substitui os limites configurados: pontos vermelhos atendem à Zona de Dor; pontos âmbar atendem à Zona de Inutilidade; os demais são azuis.', '',
                  'O número identifica o ponto na tabela; “número · quantidade” reúne componentes nas mesmas coordenadas, sem deslocá-los. Passe o cursor sobre o ponto no HTML para consultar seus componentes. I ou A indeterminado: sem posição no gráfico. Classes contribuem para A do componente; não há grafo de dependências individuais por classe.', '',
                  '| Ponto | Componente | CA | CE interno | CE externo | I | A | D | Zona de Dor |',
                  '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
        for n in nodes:
            point = f"[{point_ids[n['id']]}](coupling-{level}.svg#chart-{level}-point-{point_ids[n['id']]})" if n['id'] in point_ids else 'sem posição'
            lines.append(f"| {point} | {cell(n['id'])} | {n['ca']} | {n['ce_internal']} | {n['ce_external']} | {number(n['instability'])} | {number(n['abstractness'])} | {number(n['distance'])} | {zone(n['pain_zone'])} |")
        lines += ['', '### Diagnóstico e prioridades', '']
        pain = sorted((n for n in nodes if n['pain_zone']), key=lambda n: (-n['ca'], n['id']))
        if pain:
            for n in pain:
                lines.append(f"- **Zona de Dor: {cell(n['id'])}**. CA={n['ca']}, I={number(n['instability'])}, A={number(n['abstractness'])}. Avaliar contratos e pontos de variação antes de alterar este componente; revisar seus consumidores.")
        else:
            lines.append('- Nenhum componente com dados suficientes atende aos limites configurados da Zona de Dor.')
        for n in sorted(nodes, key=lambda n: (-n['ca'], n['id']))[:5]:
            if n['ca']:
                lines.append(f"- **Impacto de mudança: {cell(n['id'])}** tem {n['ca']} consumidores diretos. CA alto indica criticidade; sozinho não comprova defeito.")
        for n in sorted(nodes, key=lambda n: (-n['ce_internal'], n['id']))[:5]:
            if n['ce_internal']:
                lines.append(f"- **Exposição: {cell(n['id'])}** depende de {n['ce_internal']} componentes internos. Revisar responsabilidades e volatilidade dos destinos; CE alto sozinho não comprova fragilidade.")
        for n in nodes:
            if n['uselessness_zone']:
                lines.append(f"- **Abstração possivelmente desperdiçada: {cell(n['id'])}**. Confirmar se os contratos isolam detalhes e possuem consumidores úteis.")
        missing = [n['id'] for n in nodes if n['pain_zone'] is None]
        if missing:
            lines.append('- Zona indeterminada por falta de I ou A: ' + ', '.join(cell(x) for x in missing) + '.')
        lines += ['', '### Ciclos', '']
        lines += ['- Grupo mutuamente dependente: ' + ', '.join(cell(x) for x in group) + '. Avaliar separação de contratos e responsabilidades.' for group in graph['cycles']] or ['- Nenhum ciclo observado.']
        lines += ['', '### Dependências contrárias à estabilidade', '']
        lines += [f"- {cell(v['source'])} → {cell(v['target'])}: I={number(v['source_i'])} → I={number(v['target_i'])}. Revisar a direção da dependência no contexto da arquitetura." for v in graph['stability_violations']] or ['- Nenhuma relação com I(origem) < I(destino) observada.']
        lines += ['', '### Relações e evidências', '']
        for edge in graph['edges']:
            lines.append(f"- {cell(edge['source'])} → {cell(edge['target'])}")
            for ev in edge['evidence']:
                lines.append(f"  - `{cell(ev['path'])}:{ev['line']}`: {cell(ev['reason'])}.")
        if not graph['edges']:
            lines.append('- Nenhuma relação observada.')
        external = [n for n in graph['nodes'] if n['external']]
        lines += ['', '### Dependências externas observadas', '']
        lines += [f"- {cell(n['id'])}: {n['ca']} {'consumidor interno observado' if n['ca'] == 1 else 'consumidores internos observados'}; I/A/D/Zona de Dor indeterminados sem código externo." for n in external] or ['- Nenhuma dependência externa observada.']
        lines.append('')
    lines += ['', '## Cobertura e limitações', '']
    lines += ['- ' + cell(w) for w in report['warnings']] or ['- Nenhum aviso adicional nesta execução.']
    lines += ['', '## Referências metodológicas', '',
              '- Architectural_Coupling_Science.pdf: material de apoio fornecido, especialmente páginas 3 a 11. Não redistribuído pelo plugin.',
              '- [Robert C. Martin: Design Principles and Design Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf).',
              '- Consulte `docs/methodology.md` do plugin para regras por linguagem e limites do reconhecimento estático.', '']
    return '\n'.join(lines)
