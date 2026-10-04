"""Validação de coordenadas, agrupamento, cobertura e HTML offline seguro."""
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/dependency-map/scripts'))
from html_report import html_report
from metrics import markdown
from visuals import chart, point_numbers


def fixture():
    return json.loads((Path(__file__).resolve().parents[1] / 'docs/example-dependencies.json').read_text())


class ParseHTML(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags, self.links, self.ids, self.text = [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs = dict(attrs)
        self.assert_no_events(attrs)
        if 'href' in attrs:
            self.links.append(attrs['href'])
        if 'id' in attrs:
            self.ids.append(attrs['id'])

    def assert_no_events(self, attrs):
        if any(key.startswith('on') for key in attrs):
            raise AssertionError('atributo executável no HTML')
        if any(key in attrs for key in ('src', 'xlink:href')):
            raise AssertionError('recurso externo no HTML')

    def handle_data(self, data):
        self.text.append(data)


class Reports(unittest.TestCase):
    def test_coordinates_quadrants_and_main_sequence(self):
        report = fixture()
        nodes = report['modules']['nodes']
        base = deepcopy(next(n for n in nodes if not n['external']))
        nodes[:] = []
        for i, (instability, abstraction) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1), (.5, .5))):
            node = dict(base, id=f'node-{i}', instability=instability, abstractness=abstraction)
            nodes.append(node)
        svg = ET.fromstring(chart(report, 'modules'))
        ns = {'s': 'http://www.w3.org/2000/svg'}
        actual = {(float(c.attrib['cx']), float(c.attrib['cy'])) for c in svg.findall('.//s:circle', ns)}
        self.assertEqual(actual, {(100, 578), (100, 78), (600, 578), (600, 78), (350, 328)})
        text = ''.join(svg.itertext())
        for term in ('Zona de Dor', 'Zona de inutilidade', 'Abstrato estável', 'Concreto instável', 'A + I = 1'):
            self.assertIn(term, text)
        self.assertIn('M 100 578 L 600 78', chart(report, 'modules'))

    def test_coincident_nodes_preserve_positions_and_are_all_identified(self):
        report = fixture()
        first = deepcopy(next(n for n in report['modules']['nodes'] if not n['external']))
        second = dict(first, id='another-node', ca=9, pain_zone=True)
        report['modules']['nodes'] = [first, second]
        svg = ET.fromstring(chart(report, 'modules'))
        ns = {'s': 'http://www.w3.org/2000/svg'}
        self.assertEqual(len(svg.findall('.//s:circle', ns)), 1)
        self.assertEqual(point_numbers(report['modules']), {first['id']: 1, second['id']: 1})
        self.assertIn(first['id'], ''.join(svg.itertext()))
        self.assertIn('another-node', ''.join(svg.itertext()))
        self.assertIn('1 · 2', ''.join(svg.itertext()))
        self.assertEqual(svg.find('.//s:circle', ns).attrib['fill'], '#ac2335')
        report['modules']['nodes'].reverse()
        self.assertEqual(ET.tostring(svg), ET.tostring(ET.fromstring(chart(report, 'modules'))))

    def test_unknown_and_external_nodes_are_not_plotted_or_given_zero(self):
        report = fixture()
        nodes = report['modules']['nodes']
        nodes[:] = [dict(nodes[0], instability=None, id='unknown'), dict(nodes[0], external=True, id='external')]
        svg = ET.fromstring(chart(report, 'modules'))
        self.assertFalse(svg.findall('.//{http://www.w3.org/2000/svg}circle'))
        self.assertIn('Sem componentes com I e A determinados', ''.join(svg.itertext()))
        self.assertIn('| sem posição | unknown |', markdown(report))
        self.assertNotIn('external', point_numbers(report['modules']))

    def test_close_metrics_are_not_grouped_after_display_rounding(self):
        report = fixture()
        base = report['modules']['nodes'][0]
        report['modules']['nodes'] = [dict(base, id='a', instability=.200001, abstractness=.1),
                                     dict(base, id='b', instability=.200002, abstractness=.1)]
        self.assertEqual(point_numbers(report['modules']), {'a': 1, 'b': 2})
        svg = ET.fromstring(chart(report, 'modules'))
        circles = svg.findall('.//{http://www.w3.org/2000/svg}circle')
        self.assertEqual(len(circles), 2)
        self.assertNotEqual(circles[0].attrib['cx'], circles[1].attrib['cx'])

    def test_html_contains_complete_analysis_embedded_graphs_and_valid_links(self):
        report = fixture()
        text = html_report(report)
        parsed = ParseHTML(text)
        self.assertEqual(parsed.tags.count('svg'), 2)
        self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
        for link in parsed.links:
            if link.startswith('#'):
                self.assertIn(link[1:], parsed.ids)
        self.assertNotIn('script', parsed.tags)
        self.assertNotIn('img', parsed.tags)
        content = ''.join(parsed.text)
        for term in ('Diagnóstico e prioridades', 'Ciclos', 'Relações e evidências', 'Cobertura e limitações', 'Referências metodológicas'):
            self.assertIn(term, content)
        for level in ('libraries', 'modules'):
            for node in report[level]['nodes']:
                self.assertIn(node['id'], content)
        self.assertIn('<ul><li><code>', text)  # evidências aninhadas
        self.assertIn('default-src', text)
        self.assertEqual(text, html_report(report))

    def test_source_names_and_evidence_cannot_inject_html_or_svg(self):
        report = fixture()
        payload = '<script>alert("x")</script><img src="https://example.invalid" onerror="alert(1)"> & | teste'
        for level in ('libraries', 'modules'):
            report[level]['nodes'][0]['id'] = payload
            report[level]['nodes'][0]['name'] = payload
            if report[level]['edges']:
                report[level]['edges'][0]['evidence'][0]['reason'] = payload
        parsed = ParseHTML(html_report(report))
        self.assertNotIn('script', parsed.tags)
        self.assertNotIn('img', parsed.tags)
        self.assertIn(payload, ''.join(parsed.text))
        for level in ('libraries', 'modules'):
            ET.fromstring(chart(report, level))


if __name__ == '__main__':
    unittest.main()
