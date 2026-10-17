"""Validação do contrato de distribuição nos três hosts e quatro marketplaces."""
import json
from pathlib import Path
import unittest

PLUGIN = Path(__file__).resolve().parents[1]


class Packaging(unittest.TestCase):
    def test_manifests_and_marketplace_entry_are_consistent(self):
        manifests = [json.loads((PLUGIN / p).read_text()) for p in (
            '.claude-plugin/plugin.json', '.cursor-plugin/plugin.json', 'plugin.json')]
        for field in ('name', 'version', 'description', 'keywords', 'author'):
            self.assertTrue(all(m[field] == manifests[0][field] for m in manifests))
        for host in manifests[:2]:
            self.assertNotIn('agents', host)
            self.assertNotIn('skills', host)
        self.assertEqual(manifests[2]['agents'], 'copilot-agents/')
        self.assertEqual(manifests[2]['skills'], ['skills/'])
        entries = []
        for p in ('marketplace.json', '.claude-plugin/marketplace.json', '.cursor-plugin/marketplace.json', '.github/plugin/marketplace.json'):
            data = json.loads((PLUGIN.parent / p).read_text())
            self.assertEqual(data['name'], 'arquiteto-movel-plugins' if p.startswith('.github/') else 'markv-ai-plugins')
            found = [x for x in data['plugins'] if x['name'] == manifests[0]['name']]
            self.assertEqual(len(found), 1)
            entries.append(found[0])
        self.assertTrue(all(e == entries[0] for e in entries))
        for field in ('name', 'version', 'description', 'keywords'):
            self.assertEqual(entries[0][field], manifests[0][field])

    def test_agent_bodies_and_skill_resources(self):
        claude = (PLUGIN / 'agents/dependency-analyzer.md').read_text()
        copilot = (PLUGIN / 'copilot-agents/dependency-analyzer.agent.md').read_text()
        self.assertEqual(claude.split('---', 2)[2], copilot.split('---', 2)[2])
        self.assertIn('swe-dependency-map-plugin:dependency-map', claude.split('---', 2)[1])
        self.assertNotIn('model:', copilot.split('---', 2)[1])
        self.assertNotIn('skills:', copilot.split('---', 2)[1])
        skill = PLUGIN / 'skills/dependency-map/SKILL.md'
        text = skill.read_text()
        self.assertIn('name: dependency-map', text.split('---', 2)[1])
        self.assertIn('description:', text.split('---', 2)[1])
        for path in ('scripts/dependency_map.py', 'scripts/collectors.py', 'scripts/metrics.py', 'scripts/visuals.py', 'scripts/html_report.py', '../../docs/methodology.md', '../../docs/config.example.json'):
            self.assertTrue((skill.parent / path).is_file(), path)
        for readme in (PLUGIN / 'README.md', PLUGIN.parent / 'README.md'):
            self.assertIn('swe-dependency-map-plugin', readme.read_text())


if __name__ == '__main__':
    unittest.main()
