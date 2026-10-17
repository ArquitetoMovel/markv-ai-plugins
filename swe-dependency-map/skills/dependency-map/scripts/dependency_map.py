#!/usr/bin/env python3
"""CLI do swe-dependency-map. Requer Python 3.11+, sem pacotes adicionais."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from collectors import LANGUAGES, Scanner
from metrics import canonical_json, markdown
from html_report import html_report
from visuals import chart_assets

VERSION = '1.0.0'
DEFAULT_THRESHOLDS = dict(pain_min_ca=2, pain_max_i=0.2, pain_max_a=0.2,
                          useless_min_i=0.8, useless_min_a=0.8)


def configuration(args) -> dict:
    data = {}
    if args.config:
        data = json.loads(Path(args.config).read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('a configuração deve ser um objeto JSON')
    allowed = {'languages', 'exclude', 'include_tests', 'include_external', 'python_roots', 'thresholds'}
    unknown = set(data) - allowed
    if unknown:
        raise ValueError('campos de configuração desconhecidos: ' + ', '.join(sorted(unknown)))
    languages = args.languages.split(',') if args.languages else data.get('languages', list(LANGUAGES))
    if not isinstance(languages, list) or not languages or any(x not in LANGUAGES for x in languages):
        raise ValueError('languages deve conter: ' + ', '.join(LANGUAGES))
    for field in ('exclude', 'python_roots'):
        value = data.get(field, [])
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            raise ValueError(f'{field} deve ser uma lista de strings')
    for field in ('include_tests', 'include_external'):
        if field in data and not isinstance(data[field], bool):
            raise ValueError(f'{field} deve ser booleano')
    for value in data.get('python_roots', []):
        if Path(value).is_absolute() or '..' in Path(value).parts:
            raise ValueError('python_roots deve conter caminhos relativos dentro da raiz')
    thresholds = dict(DEFAULT_THRESHOLDS)
    provided = data.get('thresholds', {})
    if not isinstance(provided, dict) or set(provided) - set(thresholds):
        raise ValueError('thresholds contém campos desconhecidos ou não é um objeto')
    thresholds.update(provided)
    for key, value in thresholds.items():
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            raise ValueError(f'limite inválido: {key}')
        if key == 'pain_min_ca':
            if not isinstance(value, int) or value < 1:
                raise ValueError('pain_min_ca deve ser inteiro >= 1')
        elif not 0 <= value <= 1:
            raise ValueError(f'{key} deve estar entre 0 e 1')
    return dict(languages=sorted(set(languages)), exclude=sorted(set(data.get('exclude', []) + args.exclude)),
                python_roots=sorted(set(data.get('python_roots', []))), thresholds=thresholds,
                include_tests=args.include_tests or data.get('include_tests', False),
                include_external=args.include_external or data.get('include_external', False))


def analyze(root: Path, config: dict, output: Path | None = None) -> dict:
    scan = Scanner(root, config, output).run()
    return dict(schema_version='1.0', analyzer_version=VERSION, config=config,
                coverage='partial_static', warnings=sorted(scan.warnings),
                libraries=scan.libraries.export(config['thresholds'], config['include_external']),
                modules=scan.modules.export(config['thresholds'], config['include_external']))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Calcula acoplamento de LIBs e módulos por análise estática offline.')
    parser.add_argument('--root', default='.', help='raiz da solução ou monorepo')
    parser.add_argument('--output', help='diretório de saída; padrão: <root>/.dependency-map')
    parser.add_argument('--config', help='arquivo de configuração JSON')
    parser.add_argument('--languages', help='linguagens separadas por vírgula: ' + ','.join(LANGUAGES))
    parser.add_argument('--exclude', action='append', default=[], help='glob relativo à raiz; pode repetir')
    parser.add_argument('--include-tests', action='store_true', help='inclui fontes/test dependencies reconhecidas')
    parser.add_argument('--include-external', action='store_true', help='inclui CE externo observado na fórmula de I')
    parser.add_argument('--fail-on-pain', action='store_true', help='código 3 se detectar Zona de Dor')
    parser.add_argument('--fail-on-cycle', action='store_true', help='código 4 se detectar ciclos')
    parser.add_argument('--version', action='version', version=VERSION)
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve()
        if not root.is_dir():
            raise ValueError('a raiz deve ser um diretório existente')
        output = Path(args.output).resolve() if args.output else root / '.dependency-map'
        if output == root:
            raise ValueError('a saída deve ser diferente da raiz da solução')
        config = configuration(args)
        report = analyze(root, config, output)
        output.mkdir(parents=True, exist_ok=True)
        # Serialização ordenada, sem relógio, caminhos absolutos ou dados do ambiente.
        (output / 'dependencies.json').write_text(canonical_json(report), encoding='utf-8', newline='\n')
        (output / 'report.md').write_text(markdown(report), encoding='utf-8', newline='\n')
        (output / 'report.html').write_text(html_report(report), encoding='utf-8', newline='\n')
        for name, content in chart_assets(report).items():
            (output / name).write_text(content, encoding='utf-8', newline='\n')
        print(f"JSON: {output / 'dependencies.json'}")
        print(f"Relatório: {output / 'report.md'}")
        print(f"HTML: {output / 'report.html'}")
        if args.fail_on_pain and any(n['pain_zone'] for level in ('libraries', 'modules') for n in report[level]['nodes']):
            return 3
        if args.fail_on_cycle and any(report[level]['cycles'] for level in ('libraries', 'modules')):
            return 4
        return 0
    except (OSError, ValueError, TypeError, KeyError) as e:
        print(f'Erro: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
