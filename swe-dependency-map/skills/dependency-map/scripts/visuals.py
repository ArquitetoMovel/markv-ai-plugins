"""SVGs determinísticos de A × I. Coordenadas preservam as métricas observadas."""
from __future__ import annotations

from html import escape

LEVELS = (('libraries', 'LIBs e projetos'), ('modules', 'Módulos internos'))


def points(graph: dict) -> list[list[dict]]:
    groups = {}
    for node in sorted(graph['nodes'], key=lambda n: n['id']):
        if node['external'] or node['instability'] is None or node['abstractness'] is None:
            continue
        groups.setdefault((node['instability'], node['abstractness']), []).append(node)
    return [groups[key] for key in sorted(groups)]


def point_numbers(graph: dict) -> dict[str, int]:
    return {n['id']: i for i, group in enumerate(points(graph), 1) for n in group}


def chart(report: dict, level: str) -> str:
    label = dict(LEVELS)[level]
    groups = points(report[level])
    total = sum(len(group) for group in groups)
    # Margens acomodam pontos em I/A = 0 ou 1. Mesma escala nos dois eixos.
    left, top, side = 100, 78, 500
    right, bottom, middle = left + side, top + side, side / 2
    prefix = f'chart-{level}'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 680" role="img" aria-labelledby="{prefix}-title {prefix}-desc">',
           f'<title id="{prefix}-title">{escape(label)}: abstração × instabilidade</title>',
           f'<desc id="{prefix}-desc">{total} componentes em {len(groups)} pontos. Eixo X: I de zero a um; eixo Y: A de zero a um. Pontos coincidentes são agrupados; a tabela identifica cada componente.</desc>',
           '<rect width="720" height="680" fill="#ffffff"/>',
           '<g font-family="system-ui, sans-serif" fill="#172b4d">',
           f'<text x="100" y="34" font-size="21" font-weight="700">{escape(label)} · A × I</text>']
    zones = [(left, top, '#e4f3f0', 'Abstrato estável', 'Contratos centrais'),
             (left + middle, top, '#fff1d7', 'Abstrato instável', 'Zona de inutilidade'),
             (left, top + middle, '#fde7e7', 'Concreto estável', 'Zona de Dor'),
             (left + middle, top + middle, '#e8effc', 'Concreto instável', 'Detalhes e adaptadores')]
    for x, y, color, title, subtitle in zones:
        out += [f'<rect x="{x:g}" y="{y:g}" width="250" height="250" fill="{color}"/>',
                f'<text x="{x + 18:g}" y="{y + 40:g}" font-size="16" font-weight="600">{title}</text>',
                f'<text x="{x + 18:g}" y="{y + 62:g}" font-size="13">{subtitle}</text>']
    for value in (0, .25, .5, .75, 1):
        x, y = left + side * value, bottom - side * value
        out += [f'<path d="M {x:g} {top} V {bottom} M {left} {y:g} H {right}" fill="none" stroke="#a5b3c5" stroke-opacity="0.5"/>',
                f'<text x="{x:g}" y="{bottom + 25}" text-anchor="middle" font-size="12">{value:g}</text>',
                f'<text x="{left - 16}" y="{y + 4:g}" text-anchor="end" font-size="12">{value:g}</text>']
    out += [f'<rect x="{left}" y="{top}" width="{side}" height="{side}" fill="none" stroke="#536580"/>',
            f'<path d="M {left} {bottom} L {right} {top}" fill="none" stroke="#536580" stroke-width="2" stroke-dasharray="7 5"/>',
            '<text x="350" y="632" text-anchor="middle" font-size="15">Instabilidade (I) →</text>',
            '<text transform="translate(34 328) rotate(-90)" text-anchor="middle" font-size="15">Abstração (A) →</text>']
    for i, group in enumerate(groups, 1):
        node = group[0]
        x = left + side * node['instability']
        y = bottom - side * node['abstractness']
        pain = any(n['pain_zone'] for n in group)
        useless = any(n['uselessness_zone'] for n in group)
        color = '#ac2335' if pain else '#946000' if useless else '#234e88'
        detail = [f"Ponto {i}: I={node['instability']:.4f}, A={node['abstractness']:.4f}"]
        for n in group:
            status = 'Zona de Dor detectada' if n['pain_zone'] else 'Zona de inutilidade detectada' if n['uselessness_zone'] else 'não atende aos limites das zonas de risco'
            detail.append(f"{n['id']} · CA={n['ca']}, CE={n['ce']} · {status}")
        tooltip = escape('\n'.join(detail), quote=True)
        # Números deslocam apenas o rótulo, nunca a posição real do ponto.
        anchor = 'end' if x > left + side * .85 else 'start'
        lx = x - 13 if anchor == 'end' else x + 13
        ly = y + 24 if y < top + 20 else y - 13
        text = f'{i}' + (f' · {len(group)}' if len(group) > 1 else '')
        out += [f'<g id="{prefix}-point-{i}" class="chart-point" tabindex="0" aria-label="{tooltip}">',
                f'<title>{tooltip}</title>',
                f'<circle cx="{x:.6f}" cy="{y:.6f}" r="8" fill="{color}" stroke="#ffffff" stroke-width="2"/>',
                f'<text x="{lx:.6f}" y="{ly:.6f}" text-anchor="{anchor}" font-size="13" font-weight="700" fill="{color}" stroke="#ffffff" stroke-width="3" paint-order="stroke">{text}</text>',
                '</g>']
    if not groups:
        out.append('<text x="350" y="324" text-anchor="middle" font-size="16" font-weight="700">Sem componentes com I e A determinados</text>')
    out += ['<text x="100" y="662" font-size="12">Linha tracejada: A + I = 1 · Quadrantes: corte visual em 0,5</text>', '</g>', '</svg>', '']
    return '\n'.join(out)


def chart_assets(report: dict) -> dict[str, str]:
    return {f'coupling-{level}.svg': chart(report, level) for level, _ in LEVELS}
