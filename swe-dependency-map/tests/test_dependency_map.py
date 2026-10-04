"""Contratos de comportamento: fixtures temporárias; nenhum SDK/build necessário."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/dependency-map/scripts'
sys.path.insert(0, str(SCRIPTS))
from dependency_map import analyze, configuration, main
from metrics import Graph, Node, canonical_json, markdown


def config(**values):
    args = argparse.Namespace(config=None, languages=None, exclude=[], include_tests=False, include_external=False)
    data = configuration(args)
    data.update(values)
    return data


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding='utf-8')
        return file

    def run_scan(self, **kwargs):
        return analyze(self.root, config(**kwargs))

    def node(self, report, level, suffix):
        matches = [n for n in report[level]['nodes'] if n['id'].endswith(suffix)]
        self.assertEqual(len(matches), 1, suffix)
        return matches[0]

    def test_dotnet_counts_distinct_neighbors_and_pain(self):
        for name in ('Core', 'Api', 'Worker'):
            reference = '' if name == 'Core' else '<ProjectReference Include="../Core/Core.csproj" />'
            self.write(f'{name}/{name}.csproj', f'<Project><ItemGroup>{reference}</ItemGroup></Project>')
            text = 'namespace Shared; public class Cache {}' if name == 'Core' else f'using Shared; using Shared; namespace {name}; public class Consumer {{}}'
            self.write(f'{name}/Main.cs', text)
        report = self.run_scan(languages=['dotnet'])
        core = self.node(report, 'libraries', 'Core/Core.csproj')
        self.assertEqual((core['ca'], core['ce'], core['abstractness'], core['pain_zone']), (2, 0, 0, True))
        shared = self.node(report, 'modules', ':Shared')
        self.assertEqual(shared['ca'], 2)
        api = self.node(report, 'libraries', 'Api/Api.csproj')
        self.assertEqual(api['ce'], 1)
        edge = next(e for e in report['libraries']['edges'] if e['source'] == api['id'])
        self.assertEqual(len(edge['evidence']), 2)  # manifest + import, sem inflar CE
        self.assertIn('Zona de Dor:', markdown(report))

    def test_java_maven_packages_types_static_and_dependency_management(self):
        self.write('core/pom.xml', '<project><groupId>demo</groupId><artifactId>core</artifactId></project>')
        self.write('app/pom.xml', '<project><groupId>demo</groupId><artifactId>app</artifactId><dependencyManagement><dependencies><dependency><groupId>unused</groupId><artifactId>bom</artifactId></dependency></dependencies></dependencyManagement><dependencies><dependency><groupId>demo</groupId><artifactId>core</artifactId></dependency></dependencies></project>')
        self.write('core/src/main/java/Contract.java', 'package demo.core; public interface Contract {}')
        self.write('app/src/main/java/Api.java', 'package demo.app; import demo.core.Contract; import static demo.core.Contract.CONSTANT; public class Api {}')
        report = self.run_scan(languages=['java'])
        core = self.node(report, 'libraries', 'core/pom.xml')
        self.assertEqual((core['ca'], core['abstractness']), (1, 1))
        self.assertFalse(any('unused' in n['id'] for n in report['libraries']['nodes']))
        self.assertEqual(len(report['modules']['edges']), 1)

    def test_gradle_kotlin_and_groovy_project_edges(self):
        self.write('settings.gradle.kts', 'include(":core", ":app")')
        self.write('core/build.gradle.kts', 'plugins { java }')
        self.write('app/build.gradle', "dependencies { implementation project(':core'); implementation 'org.slf4j:slf4j-api:2.0' }")
        self.write('core/Contract.java', 'package demo.core; interface Contract {}')
        self.write('app/Consumer.java', 'package demo.app; import demo.core.Contract; class Consumer {}')
        report = self.run_scan(languages=['java'])
        app = self.node(report, 'libraries', 'app/build.gradle')
        self.assertEqual((app['ce_internal'], app['ce_external']), (1, 1))
        self.assertEqual(len(report['modules']['edges']), 1)

    def test_typescript_jsonc_aliases_reexports_extension_substitution_and_cycles(self):
        self.write('package.json', '{"name":"app","dependencies":{"lodash":"1"}}')
        self.write('tsconfig.base.json', '{"compilerOptions":{"paths":{"@/*":["src/*"]}}}')
        self.write('tsconfig.json', '{ // commentaire\n "extends":"./tsconfig.base.json", "compilerOptions":{}, }')
        self.write('src/a.ts', 'import {B} from "@/b"; import "lodash/map"; export interface A {}')
        self.write('src/b.ts', 'export {A} from "./a.js"; export class B {}')
        report = self.run_scan(languages=['typescript'])
        a = self.node(report, 'modules', 'src/a.ts')
        b = self.node(report, 'modules', 'src/b.ts')
        self.assertEqual((a['ce_internal'], b['ce_internal'], a['abstractness']), (1, 1, 1))
        self.assertEqual(report['modules']['cycles'], [[a['id'], b['id']]])
        self.assertEqual(self.node(report, 'libraries', 'package.json')['ce_external'], 1)

    def test_typescript_workspace_packages_and_no_false_imports_in_strings(self):
        self.write('packages/core/package.json', '{"name":"@demo/core","types":"src/index.ts"}')
        self.write('packages/core/src/index.ts', 'export interface Contract {}')
        self.write('packages/app/package.json', '{"name":"app","dependencies":{"@demo/core":"workspace:*"}}')
        self.write('packages/app/src/main.ts', '''import type {Contract} from "@demo/core";
const text = "import evil from 'fake'; class Fake {}";
// import "comment";
export class Consumer {}''')
        report = self.run_scan(languages=['typescript'])
        self.assertEqual(len(report['modules']['edges']), 1)
        self.assertEqual(self.node(report, 'modules', 'src/main.ts')['total_types'], 1)
        self.assertEqual(self.node(report, 'libraries', 'core/package.json')['ca'], 1)

    def test_python_src_relative_imports_aliases_and_no_runtime_execution(self):
        self.write('pyproject.toml', '[project]\nname="demo"\ndependencies=["requests>=2"]\n')
        self.write('src/demo/__init__.py', '')
        self.write('src/demo/contracts.py', 'from abc import ABC as Base, abstractmethod as abstract\nclass Contract(Base):\n @abstract\n def send(self): pass\n')
        self.write('src/demo/app.py', 'from .contracts import Contract\nimport requests\nraise RuntimeError("must not execute")\nclass App: pass\n')
        self.write('src/demo/test_ignore.py', 'import does_not_exist')
        report = self.run_scan(languages=['python'])
        contract = self.node(report, 'modules', 'contracts.py')
        self.assertEqual((contract['ca'], contract['abstractness']), (1, 1))
        app = self.node(report, 'modules', 'app.py')
        self.assertEqual(app['ce_internal'], 1)
        self.assertFalse(any(n['id'].endswith('test_ignore.py') for n in report['modules']['nodes']))
        self.assertEqual(self.node(report, 'libraries', 'pyproject.toml')['ce_external'], 1)

    def test_python_namespace_packages_and_from_submodule(self):
        self.write('src/domain/model.py', 'class Model: pass')
        self.write('src/app/main.py', 'from domain import model\nclass App: pass')
        report = self.run_scan(languages=['python'])
        self.assertEqual(self.node(report, 'modules', 'model.py')['ca'], 1)

    def test_go_multiple_modules_grouped_types_imports_and_comments(self):
        self.write('go.work', 'go 1.22\nuse (./core ./app)')
        self.write('core/go.mod', 'module example.com/core\ngo 1.22')
        self.write('app/go.mod', 'module example.com/app\ngo 1.22\nrequire (\nexample.com/core v1.0.0\nexample.com/ext v1.0.0\n)')
        self.write('core/core.go', 'package core\ntype (\nContract interface { Send() }\nModel struct { X int }\n)')
        self.write('app/app.go', 'package app\nimport (\n c "example.com/core"\n "example.com/ext"\n)\n/* import "fake" */\ntype App struct {}')
        self.write('app/app_test.go', 'package app\nimport "ignored"')
        report = self.run_scan(languages=['go'])
        core = self.node(report, 'libraries', 'core/go.mod')
        self.assertEqual((core['ca'], core['total_types'], core['abstract_types'], core['abstractness']), (1, 2, 1, .5))
        app = self.node(report, 'libraries', 'app/go.mod')
        self.assertEqual((app['ce_internal'], app['ce_external']), (1, 1))
        self.assertEqual(len(report['modules']['edges']), 2)

    def test_unresolved_internal_references_and_external_metrics_unknown(self):
        self.write('package.json', '{"name":"demo"}')
        self.write('a.ts', 'import "./missing"; import "external"; export class A {}')
        report = self.run_scan(languages=['typescript'], include_external=True)
        self.assertTrue(any('não resolvido' in w for w in report['warnings']))
        a = self.node(report, 'modules', 'a.ts')
        self.assertEqual(a['ce'], 1)
        external = [n for n in report['modules']['nodes'] if n['external']][0]
        self.assertIsNone(external['instability'])
        self.assertIsNone(external['pain_zone'])

    def test_isolated_function_only_component_has_unknown_i_and_a(self):
        self.write('functions.py', 'def fn(): return 42')
        report = self.run_scan(languages=['python'])
        node = self.node(report, 'modules', 'functions.py')
        self.assertIsNone(node['instability'])
        self.assertIsNone(node['abstractness'])
        self.assertIsNone(node['pain_zone'])

    def test_cli_byte_reproducibility_excludes_output_and_hash_seed(self):
        self.write('app.py', 'from lib import Library\nclass App: pass')
        self.write('lib.py', 'class Library: pass')
        script = str(SCRIPTS / 'dependency_map.py')
        command = [sys.executable, script, '--root', str(self.root), '--languages', 'python']
        subprocess.run(command, check=True, capture_output=True, env=dict(os.environ, PYTHONHASHSEED='1'))
        files = [self.root / '.dependency-map' / n for n in (
            'dependencies.json', 'report.md', 'report.html', 'coupling-libraries.svg', 'coupling-modules.svg')]
        initial = [p.read_bytes() for p in files]
        subprocess.run(command, check=True, capture_output=True, env=dict(os.environ, PYTHONHASHSEED='99'))
        self.assertEqual(initial, [p.read_bytes() for p in files])
        self.assertNotIn(str(self.root), initial[0].decode())

    def test_exclusions_symlinks_invalid_config_and_exit_codes(self):
        self.write('a.ts', 'import "./b"; class A {}')
        self.write('b.ts', 'import "./a"; class B {}')
        self.write('generated/ignored.ts', 'import "external"; class Ignored {}')
        (self.root / 'link.ts').symlink_to(self.root / 'a.ts')
        report = self.run_scan(languages=['typescript'], exclude=['generated/**'])
        self.assertEqual(len([n for n in report['modules']['nodes'] if not n['external']]), 2)
        self.assertEqual(main(['--root', str(self.root), '--languages', 'typescript', '--fail-on-cycle']), 4)
        self.assertEqual(main(['--root', str(self.root), '--languages', 'ruby']), 2)
        bad = self.write('bad.json', '{"thresholds":{"pain_max_i":2}}')
        self.assertEqual(main(['--root', str(self.root), '--config', str(bad)]), 2)

    def test_duplicate_partial_dotnet_type_is_counted_once(self):
        self.write('Demo.csproj', '<Project/>')
        self.write('a.cs', 'namespace Demo; public partial class A {}')
        self.write('b.cs', 'namespace Demo; public partial class A {} public interface I {}')
        report = self.run_scan(languages=['dotnet'])
        self.assertEqual(self.node(report, 'modules', ':Demo')['total_types'], 2)

    def test_csharp_nested_generic_partial_alias_and_using_statement(self):
        self.write('Demo.csproj', '<Project/>')
        self.write('contracts.cs', 'namespace Contracts; public abstract partial class Outer<T> { public class Inner {} } public partial class Outer {}')
        self.write('consumer.cs', 'using Alias = Contracts.Outer; namespace App; public class App { void F() { using var x = factory; } }')
        report = self.run_scan(languages=['dotnet'])
        contracts = self.node(report, 'modules', ':Contracts')
        self.assertEqual((contracts['total_types'], contracts['abstract_types'], contracts['ca']), (3, 1, 1))
        self.assertFalse(any('factory' in n['id'] for n in report['modules']['nodes']))

    def test_concrete_python_subclass_does_not_inherit_abstract_marker(self):
        self.write('contract.py', 'from abc import ABC, abstractmethod\nclass Contract(ABC):\n @abstractmethod\n def f(self): pass\nclass Implementation(Contract):\n def f(self): return 1\n')
        node = self.node(self.run_scan(languages=['python']), 'modules', 'contract.py')
        self.assertEqual((node['total_types'], node['abstract_types']), (2, 1))

    def test_java_unknown_type_under_internal_package_is_not_false_edge(self):
        self.write('known.java', 'package demo; public class Known {}')
        self.write('consumer.java', 'package app; import demo.external.Unknown; public class App {}')
        report = self.run_scan(languages=['java'])
        self.assertEqual(report['modules']['edges'], [])
        self.assertTrue(any('não resolvido' in w for w in report['warnings']))

    def test_typescript_import_type_default_does_not_declare_type(self):
        self.write('a.ts', 'export interface Contract {}')
        self.write('b.ts', 'import type Contract from "./a"; export type Value = string; export class B {}')
        report = self.run_scan(languages=['typescript'])
        b = self.node(report, 'modules', 'b.ts')
        self.assertEqual((b['total_types'], b['abstract_types']), (2, 0))

    def test_malformed_manifests_and_tsconfig_warn_without_crash(self):
        self.write('package.json', '[]')
        self.write('tsconfig.json', '[]')
        self.write('main.ts', 'import "bare"; export class Main {}')
        report = self.run_scan(languages=['typescript'])
        self.assertTrue(any('manifest inválido' in w for w in report['warnings']))
        self.assertTrue(any('tsconfig deve ser' in w for w in report['warnings']))
        self.assertEqual(len([n for n in report['modules']['nodes'] if not n['external']]), 1)

    def test_cli_pain_exit_still_writes_report(self):
        self.write('shared.py', 'class Shared: pass')
        self.write('app.py', 'from shared import Shared\nclass App: pass')
        self.write('worker.py', 'from shared import Shared\nclass Worker: pass')
        self.assertEqual(main(['--root', str(self.root), '--languages', 'python', '--fail-on-pain']), 3)
        for name in ('report.md', 'report.html', 'coupling-libraries.svg', 'coupling-modules.svg'):
            self.assertTrue((self.root / '.dependency-map' / name).is_file())

    def test_mixed_repository_keeps_language_and_graph_boundaries(self):
        self.write('dotnet/Demo.csproj', '<Project/>')
        self.write('dotnet/demo.cs', 'namespace Demo; interface Contract {}')
        self.write('java/pom.xml', '<project><groupId>demo</groupId><artifactId>java</artifactId></project>')
        self.write('java/Demo.java', 'package demo; interface Contract {}')
        self.write('ts/package.json', '{"name":"demo-ts"}')
        self.write('ts/demo.ts', 'export interface Contract {}')
        self.write('python/pyproject.toml', '[project]\nname="demo-python"')
        self.write('python/demo.py', 'class Demo: pass')
        self.write('go/go.mod', 'module example.com/demo')
        self.write('go/demo.go', 'package demo\ntype Contract interface {}')
        report = self.run_scan()
        self.assertEqual(len(report['libraries']['nodes']), 5)
        self.assertEqual(len(report['modules']['nodes']), 5)
        self.assertEqual({n['language'] for n in report['modules']['nodes']}, {'dotnet', 'java', 'typescript', 'python', 'go'})
        self.assertEqual(report['libraries']['edges'], [])


class Metrics(unittest.TestCase):
    def test_graph_long_cycle_without_recursion_limit(self):
        graph = Graph()
        for i in range(1500):
            key = str(i)
            graph.nodes[key] = Node(key, key, 'python', 'module', '')
        for i in range(1500):
            graph.add(str(i), str((i + 1) % 1500), 'fixture.py', 1, 'import')
        self.assertEqual(len(graph.cycles()[0]), 1500)

    def test_distance_and_scope_are_separate_from_evidence_frequency(self):
        graph = Graph()
        graph.nodes['a'] = Node('a', 'a', 'python', 'module', '', total_types=2, abstract_types=1)
        graph.nodes['b'] = Node('b', 'b', 'python', 'module', '', total_types=1)
        graph.nodes['x'] = Node('x', 'x', 'python', 'import', '', external=True)
        graph.add('a', 'b', 'a.py', 1, 'import')
        graph.add('a', 'b', 'a.py', 2, 'import')
        graph.add('a', 'x', 'a.py', 3, 'import')
        graph.add('b', 'a', 'b.py', 1, 'import')
        thresholds = config()['thresholds']
        node = graph.export(thresholds, False)['nodes'][0]
        self.assertEqual((node['ce'], node['instability'], node['distance']), (1, .5, 0))
        node = graph.export(thresholds, True)['nodes'][0]
        self.assertEqual(node['ce'], 2)
        self.assertAlmostEqual(node['instability'], 2 / 3)
        self.assertEqual(canonical_json({'b': 1, 'a': 2}), canonical_json({'a': 2, 'b': 1}))


if __name__ == '__main__':
    unittest.main()
