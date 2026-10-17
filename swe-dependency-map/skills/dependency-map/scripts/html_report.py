"""HTML offline: renderiza apenas o subconjunto Markdown emitido pelo motor."""
from __future__ import annotations

from html import escape
import re

from metrics import markdown
from visuals import chart_assets


def inline(value: str) -> str:
    # Nunca interprete HTML vindo de nomes, caminhos ou evidências da solução.
    target = r'(?:https://[^\s)]+|coupling-(?:libraries|modules)\.svg#chart-(?:libraries|modules)-point-\d+)'
    pattern = rf'(`[^`]+`|\*\*[^*]+\*\*|\[[^\]\n]+\]\({target}\))'
    result = []
    for part in re.split(pattern, value):
        if part.startswith('`') and part.endswith('`'):
            result.append('<code>' + escape(part[1:-1]) + '</code>')
        elif part.startswith('**') and part.endswith('**'):
            result.append('<strong>' + escape(part[2:-2]) + '</strong>')
        else:
            link = re.fullmatch(rf'\[([^\]\n]+)\]\(({target})\)', part)
            if link:
                href = '#' + link[2].split('#', 1)[1] if link[2].startswith('coupling-') else link[2]
                result.append(f'<a href="{escape(href, quote=True)}">{escape(link[1])}</a>')
            else:
                result.append(escape(part))
    return ''.join(result)


def render(body: str, assets: dict[str, str]) -> str:
    lines, out, index = body.splitlines(), [], 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line:
            continue
        image = re.fullmatch(r'!\[[^\]]+\]\((coupling-(?:libraries|modules)\.svg)\)', line)
        if image:
            out.append('<figure>' + assets[image[1]] + '</figure>')
        elif line.startswith('```'):
            code = []
            while index < len(lines) and not lines[index].startswith('```'):
                code.append(lines[index])
                index += 1
            index += 1
            out.append('<pre><code>' + escape('\n'.join(code)) + '</code></pre>')
        elif line.startswith('| '):
            rows = [line]
            while index < len(lines) and lines[index].startswith('| '):
                rows.append(lines[index])
                index += 1
            table = ['<div class="table-scroll"><table>']
            for i, row in enumerate(rows):
                if i == 1:  # Separador de cabeçalho emitido por metrics.markdown.
                    continue
                cells = re.split(r'(?<!\\)\|', row)[1:-1]
                tag = 'th' if i == 0 else 'td'
                if i == 0:
                    table.append('<thead>')
                elif i == 2:
                    table.append('<tbody>')
                table.append('<tr>' + ''.join(f'<{tag}>' + inline(c.strip().replace('\\|', '|')) + f'</{tag}>' for c in cells) + '</tr>')
                if i == 0:
                    table.append('</thead>')
            if len(rows) > 2:
                table.append('</tbody>')
            table.append('</table></div>')
            out.extend(table)
        elif line.startswith('- '):
            out.append('<ul>')
            while True:
                out.append('<li>' + inline(line[2:]))
                children = []
                while index < len(lines) and lines[index].startswith('  - '):
                    children.append('<li>' + inline(lines[index][4:]) + '</li>')
                    index += 1
                if children:
                    out.append('<ul>' + ''.join(children) + '</ul>')
                out.append('</li>')
                if index >= len(lines) or not lines[index].startswith('- '):
                    break
                line = lines[index]
                index += 1
            out.append('</ul>')
        elif line.startswith('#'):
            heading = re.fullmatch(r'(#{1,3}) (.*)', line)
            if heading:
                tag = 'h' + str(len(heading[1]))
                anchors = {'LIBs e projetos': 'libraries', 'Módulos internos': 'modules', 'Cobertura e limitações': 'coverage'}
                anchor = f' id="{anchors[heading[2]]}"' if heading[2] in anchors else ''
                out.append(f'<{tag}{anchor}>' + inline(heading[2]) + f'</{tag}>')
            else:
                out.append('<p>' + inline(line) + '</p>')
        else:
            out.append('<p>' + inline(line) + '</p>')
    return '\n'.join(out)


STYLE = '''
:root { color-scheme: light; font-family: system-ui, sans-serif; color: #172b4d; background: #eef2f7; }
body { margin: 0; line-height: 1.6; }
main { max-width: 1120px; margin: 24px auto; padding: 28px 36px; background: white; border-radius: 16px; }
nav { display: flex; flex-wrap: wrap; gap: 20px; padding: 16px 0; border-bottom: 1px solid #d9e1ec; }
a { color: #245496; } h1 { line-height: 1.2; } h2 { margin-top: 44px; } h3 { margin-top: 28px; }
p, li, td { overflow-wrap: anywhere; } figure { max-width: 800px; margin: 24px auto; }
svg { display: block; width: 100%; height: auto; } .chart-point { cursor: help; }
.chart-point:focus, .chart-point:target { outline: none; } .chart-point:focus circle, .chart-point:target circle { stroke: #0c1524; stroke-width: 4; }
.table-scroll { overflow-x: auto; } table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { padding: 10px 12px; border-bottom: 1px solid #d9e1ec; text-align: left; vertical-align: top; }
th { background: #eef2f7; } tr:nth-child(even) { background: #f8fafc; }
code { background: #eef2f7; border-radius: 4px; padding: 2px 4px; } pre { overflow: auto; padding: 16px; background: #eef2f7; }
pre code { padding: 0; } @media (max-width: 640px) { main { margin: 0; padding: 20px 14px; border-radius: 0; } }
@media print { :root { background: white; } main { max-width: none; margin: 0; padding: 0; } nav { display: none; } figure, tr { break-inside: avoid; } }
'''


def html_report(report: dict) -> str:
    content = render(markdown(report), chart_assets(report))
    return '\n'.join([
        '<!DOCTYPE html>', '<html lang="pt-BR">', '<head>', '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
        '<title>Análise do acoplamento · swe-dependency-map</title>',
        '<style>' + STYLE + '</style>', '</head>', '<body>', '<main>',
        '<nav aria-label="Seções do relatório"><a href="#libraries">LIBs e projetos</a><a href="#modules">Módulos internos</a><a href="#coverage">Cobertura e limitações</a></nav>',
        content, '</main>', '</body>', '</html>', ''])
