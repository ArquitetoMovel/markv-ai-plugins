"""Coletores estáticos offline; não executam builds, manifests ou código analisado."""
from __future__ import annotations

import ast
import configparser
import fnmatch
import json
import os
import re
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from metrics import Graph, Node

LANGUAGES = ('dotnet', 'java', 'typescript', 'python', 'go')
EXTENSIONS = {'.cs': 'dotnet', '.java': 'java', '.ts': 'typescript', '.tsx': 'typescript',
              '.mts': 'typescript', '.cts': 'typescript', '.py': 'python', '.go': 'go'}
IGNORED = {'.git', '.hg', '.svn', 'node_modules', 'bin', 'obj', 'target', 'build', 'dist',
           '.venv', 'venv', '__pycache__', '.gradle', '.idea', '.mypy_cache', '.pytest_cache',
           'vendor', 'coverage', '.dependency-map'}
TEST_DIRS = {'test', 'tests', '__tests__', '__mocks__'}


@dataclass(frozen=True)
class Token:
    value: str
    line: int
    kind: str


# Strings são tokens distintos: texto de comentário ou string nunca vira import ou tipo.
LEXER = re.compile(r'(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)|'
                   r'(?P<string>@"(?:""|[^"\\]|\\.)*"|"(?:\\.|[^"\\])*"|'
                   r"'(?:\\.|[^'\\])*'|`[^`]*`)|"
                   r'(?P<word>[A-Za-z_$\u0080-\uffff][\w$]*)|(?P<space>\s+)|(?P<symbol>.)')


def tokens(text: str) -> list[Token]:
    result, line = [], 1
    for m in LEXER.finditer(text):
        kind, value = m.lastgroup, m.group()
        if kind not in ('comment', 'space'):
            if kind == 'string':
                value = value[2:-1].replace('""', '"') if value.startswith('@"') else value[1:-1]
            result.append(Token(value, line, kind))
        line += m.group().count('\n')
    return result


def dotted(items: list[Token]) -> str:
    return ''.join(t.value for t in items)


def jsonc(text: str):
    """Remove comentários e vírgulas finais preservando strings JSON."""
    pattern = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/')
    text = pattern.sub(lambda m: m.group() if m.group().startswith('"') else ' ', text)
    # Só remova vírgulas fora de strings.
    return json.loads(re.sub(r'("(?:\\.|[^"\\])*")|,(\s*[}\]])',
                             lambda m: m.group(1) if m.group(1) else m.group(2), text))


def normalize_distribution(name: str) -> str:
    return re.sub(r'[-_.]+', '-', name).lower()


class Scanner:
    def __init__(self, root: Path, config: dict, output: Path | None = None):
        self.root = root.resolve()
        self.config = config
        self.output = output.resolve() if output else None
        self.libraries, self.modules = Graph(), Graph()
        self.warnings: set[str] = set()
        self.projects: dict[str, dict] = {}
        self.files: list[Path] = []
        self.sources: dict[Path, dict] = {}
        self.index: dict[tuple[str, str], list[str]] = {}
        self.type_names: set[tuple[str, str]] = set()
        self.pending: list[tuple[str, str, str, int, str]] = []
        self.tsconfigs: dict[Path, dict] = {}

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix() or '.'

    def warn(self, path: Path | str, message: str):
        self.warnings.add(f'{self.rel(path) if isinstance(path, Path) else path}: {message}')

    def read(self, path: Path) -> str:
        try:
            return path.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as e:
            self.warn(path, f'arquivo não lido ({type(e).__name__}); cobertura incompleta')
            return ''

    def walk(self):
        for base, dirs, names in os.walk(self.root, followlinks=False):
            directory = Path(base)
            def allowed(path):
                if path.is_symlink() or path == self.output:
                    return False
                rel = self.rel(path)
                return not any(fnmatch.fnmatchcase(rel, p) or fnmatch.fnmatchcase(rel + '/', p)
                               for p in self.config['exclude'])
            dirs[:] = sorted(d for d in dirs if d not in IGNORED
                             and (self.config['include_tests'] or d.lower() not in TEST_DIRS)
                             and allowed(directory / d))
            for name in sorted(names):
                path = directory / name
                if not allowed(path):
                    continue
                if not self.config['include_tests'] and (
                    name.endswith('_test.go') or name.startswith('test_') and name.endswith('.py')
                    or re.search(r'\.(?:test|spec)\.[cm]?tsx?$', name)
                ):
                    continue
                self.files.append(path)

    def project(self, language: str, manifest: Path | None, base: Path, name: str, **details) -> str:
        location = self.rel(manifest) if manifest else self.rel(base) + '/<sources>'
        key = f'{language}:library:{location}'
        self.libraries.nodes[key] = Node(key, name, language, 'library', location)
        self.projects[key] = dict(language=language, manifest=manifest, base=base, name=name, **details)
        return key

    def external(self, graph: Graph, language: str, name: str, kind: str = 'import') -> str:
        key = f'{language}:external:{kind}:{name}'
        graph.nodes.setdefault(key, Node(key, name, language, kind, '', external=True))
        return key

    def declared(self, source: str, name: str, path: Path, line: int = 1, kind: str = 'package'):
        self.pending.append((source, kind, name, line, self.rel(path)))

    def discover(self):
        languages = self.config['languages']
        for path in self.files:
            language = None
            if path.suffix in ('.csproj', '.fsproj', '.vbproj'):
                language = 'dotnet'
            elif path.name in ('pom.xml', 'build.gradle', 'build.gradle.kts'):
                language = 'java'
            elif path.name == 'package.json':
                language = 'typescript'
            elif path.name in ('pyproject.toml', 'setup.cfg', 'setup.py'):
                language = 'python'
            elif path.name == 'go.mod':
                language = 'go'
            if language not in languages:
                continue
            # Um projeto pode ter mais de um manifest do mesmo ecossistema.
            if language in ('python', 'java'):
                priority = ('pyproject.toml', 'setup.cfg', 'setup.py') if language == 'python' else ('pom.xml', 'build.gradle.kts', 'build.gradle')
                if any(path.with_name(n) in self.files for n in priority[:priority.index(path.name)]):
                    self.warn(path, 'manifest alternativo ignorado; o manifest de maior prioridade define a LIB')
                    continue
            try:
                getattr(self, f'discover_{language}')(path)
            except (ET.ParseError, json.JSONDecodeError, tomllib.TOMLDecodeError, configparser.Error, ValueError, TypeError, AttributeError) as e:
                self.warn(path, f'manifest inválido ({type(e).__name__}); dependências declaradas não extraídas')
        for language in languages:
            sources = [p for p in self.files if EXTENSIONS.get(p.suffix) == language]
            if any(not self.owners(p, language) for p in sources):
                self.project(language, None, self.root, f'{language}: fontes sem manifest')
                self.warn(language, 'fontes sem manifest agrupadas em LIB sintética; fronteiras podem precisar de revisão')
        self.resolve_declared()

    def owners(self, path: Path, language: str) -> list[str]:
        candidates = [(len(p['base'].parts), key) for key, p in self.projects.items()
                      if p['language'] == language and path.is_relative_to(p['base'])]
        depth = max((d for d, _ in candidates), default=-1)
        return sorted(k for d, k in candidates if d == depth)

    def xml(self, path):
        root = ET.fromstring(self.read(path))
        for element in root.iter():
            element.tag = element.tag.split('}')[-1]
        return root

    def discover_dotnet(self, path):
        root = self.xml(path)
        key = self.project('dotnet', path, path.parent, path.stem)
        if path.suffix != '.csproj':
            self.warn(path, 'grafo de LIBs disponível; módulos e abstração de fontes F#/VB não extraídos')
        for element in root.iter():
            if element.tag in ('ProjectReference', 'PackageReference', 'Reference'):
                name = element.attrib.get('Include', '')
                if not name:
                    continue
                if '$(' in name or '*' in name:
                    self.warn(path, f'referência MSBuild não literal ignorada: {name}')
                    continue
                if element.tag == 'ProjectReference':
                    if element.attrib.get('ReferenceOutputAssembly', '').lower() == 'false':
                        continue
                    destination = (path.parent / name.replace('\\', '/')).resolve()
                    if not destination.is_relative_to(self.root):
                        self.warn(path, f'ProjectReference fora do escopo: {name}')
                    else:
                        self.declared(key, self.rel(destination), path, kind='project_path')
                else:
                    self.declared(key, name.lower(), path, kind='assembly' if element.tag == 'Reference' else 'package')
            if element.attrib.get('Condition'):
                self.warn(path, 'condições MSBuild não avaliadas; relatório usa a união das referências literais')
            if element.tag in ('Import', 'Compile'):
                self.warn(path, 'imports MSBuild e seleção explícita de Compile não avaliados; fontes descobertas por diretório')
        legacy = path.parent / 'packages.config'
        if legacy in self.files:
            for package in self.xml(legacy).iter('package'):
                if package.attrib.get('id'):
                    self.declared(key, package.attrib['id'].lower(), legacy)

    def discover_java(self, path):
        if path.name == 'pom.xml':
            root = self.xml(path)
            group = root.findtext('groupId') or root.findtext('parent/groupId') or ''
            artifact = root.findtext('artifactId') or path.parent.name
            props = {x.tag: x.text or '' for x in root.findall('properties/*')}
            props.update({'project.groupId': group, 'pom.groupId': group, 'project.artifactId': artifact})
            def expand(value):
                for _ in range(8):
                    changed = re.sub(r'\$\{([^}]+)\}', lambda m: props.get(m.group(1), m.group()), value)
                    if value == changed:
                        break
                    value = changed
                return value
            coord = expand(group) + ':' + expand(artifact)
            key = self.project('java', path, path.parent, coord, coordinate=coord)
            for dep in root.findall('dependencies/dependency'):
                if dep.findtext('scope') == 'test' and not self.config['include_tests']:
                    continue
                name = expand((dep.findtext('groupId') or '') + ':' + (dep.findtext('artifactId') or ''))
                if '${' in name or name.startswith(':') or name.endswith(':'):
                    self.warn(path, f'coordenada Maven não resolvida: {name}')
                else:
                    self.declared(key, name, path)
            if root.find('parent') is not None or root.find('profiles') is not None:
                self.warn(path, 'herança e perfis Maven não avaliados; somente dependências diretas literais/propriedades locais')
        else:
            key = self.project('java', path, path.parent, self.rel(path.parent), gradle=True)
            items = tokens(self.read(path))
            configs = {'api', 'implementation', 'compileOnly', 'runtimeOnly', 'compile', 'runtime', 'annotationProcessor'}
            if self.config['include_tests']:
                configs.update({'testImplementation', 'testCompileOnly', 'testRuntimeOnly', 'testCompile'})
            for i, t in enumerate(items):
                if t.value not in configs or t.kind != 'word':
                    continue
                j = i + 1
                if j < len(items) and items[j].value == '(':
                    j += 1
                if j < len(items) and items[j].value == 'project':
                    j += 1
                    while j < len(items) and items[j].value in ('(', 'path', ':', '='):
                        j += 1
                    if j < len(items) and items[j].kind == 'string' and '$' not in items[j].value:
                        self.declared(key, items[j].value, path, t.line, 'gradle_project')
                    else:
                        self.warn(path, f'project Gradle não literal na linha {t.line}')
                elif j < len(items) and items[j].kind == 'string' and ':' in items[j].value:
                    if '$' in items[j].value:
                        self.warn(path, f'coordenada Gradle interpolada na linha {t.line}')
                    else:
                        self.declared(key, ':'.join(items[j].value.split(':')[:2]), path, t.line)
                else:
                    self.warn(path, f'dependência Gradle não literal na linha {t.line}')
            self.warn(path, 'Gradle não executado; catálogos, plugins, variáveis, includeBuild e projectDir personalizados não avaliados')

    def discover_typescript(self, path):
        data = json.loads(self.read(path))
        key = self.project('typescript', path, path.parent, data.get('name') or self.rel(path.parent), package=data)
        fields = ['dependencies', 'peerDependencies', 'optionalDependencies']
        if self.config['include_tests']:
            fields.append('devDependencies')
        for section in fields:
            for name in sorted(data.get(section, {})):
                self.declared(key, name, path)
        if data.get('devDependencies') and not self.config['include_tests']:
            self.warn(path, 'devDependencies omitidas do grafo declarado; imports explícitos continuam observados')

    def discover_python(self, path):
        name, deps = path.parent.name, []
        if path.name == 'pyproject.toml':
            data = tomllib.loads(self.read(path))
            project = data.get('project', {})
            name = project.get('name', name)
            deps.extend(project.get('dependencies', []))
            poetry = data.get('tool', {}).get('poetry', {})
            name = poetry.get('name', name)
            deps.extend(k for k in poetry.get('dependencies', {}) if k != 'python')
            if project.get('dynamic'):
                self.warn(path, 'metadados Python dinâmicos não avaliados')
            if project.get('optional-dependencies'):
                self.warn(path, 'extras Python não ativados; somente dependências básicas')
        elif path.name == 'setup.cfg':
            data = configparser.ConfigParser(interpolation=None)
            data.read_string(self.read(path))
            name = data.get('metadata', 'name', fallback=name)
            deps.extend(data.get('options', 'install_requires', fallback='').splitlines())
        else:
            self.warn(path, 'setup.py não executado; dependências dinâmicas não extraídas')
        key = self.project('python', path, path.parent, name)
        for dep in deps:
            self.python_requirement(key, dep, path)
        requirements = path.parent / 'requirements.txt'
        if requirements in self.files:
            self.requirements(key, requirements, set())

    def python_requirement(self, key, dep, path, line=1):
        if ';' in dep:
            self.warn(path, 'marcadores de ambiente Python não avaliados; referências literais observadas')
        m = re.match(r'\s*([A-Za-z0-9][A-Za-z0-9._-]*)', dep)
        if m and not dep.lstrip().startswith(('#', '-')):
            self.declared(key, normalize_distribution(m.group(1)), path, line)
        elif dep.strip() and not dep.lstrip().startswith('#'):
            self.warn(path, f'requisito não literal ignorado na linha {line}')

    def requirements(self, key, path, seen):
        if path in seen:
            return
        seen.add(path)
        for line, dep in enumerate(self.read(path).splitlines(), 1):
            match = re.match(r'\s*(?:-r\s+|--requirement[=\s]+)(\S+)', dep)
            if match:
                target = (path.parent / match.group(1)).resolve()
                if target in self.files:
                    self.requirements(key, target, seen)
                else:
                    self.warn(path, f'arquivo de requisitos não disponível: {match.group(1)}')
            else:
                self.python_requirement(key, dep, path, line)

    def discover_go(self, path):
        text = re.sub(r'//[^\n]*', '', self.read(path))
        m = re.search(r'^\s*module\s+(\S+)', text, re.M)
        if not m:
            raise ValueError('module ausente')
        name = m.group(1).strip('"')
        key = self.project('go', path, path.parent, name, module=name)
        block = False
        for line, value in enumerate(text.splitlines(), 1):
            value = value.strip()
            if re.match(r'require\s*\(', value):
                block = True
                continue
            if value == ')':
                block = False
                continue
            m = re.match(r'(?:require\s+)?([\w./~-]+)\s+v\S+', value) if block or value.startswith('require ') else None
            if m:
                self.declared(key, m.group(1), path, line)
        if re.search(r'^\s*replace\s', text, re.M):
            self.warn(path, 'replace Go não avaliado; resolução por caminhos de module descobertos no escopo')

    def resolve_declared(self):
        for source, kind, name, line, path in sorted(self.pending):
            language = self.projects[source]['language']
            candidates = []
            if kind == 'project_path':
                candidates = [k for k, p in self.projects.items() if p['manifest'] and self.rel(p['manifest']) == name]
            elif kind == 'gradle_project':
                # Caminho padrão relativo ao settings.gradle mais próximo, sem executar o script.
                base = self.projects[source]['base']
                while base != self.root and not any((base / n) in self.files for n in ('settings.gradle', 'settings.gradle.kts')):
                    base = base.parent
                dest = base.joinpath(*name.lstrip(':').split(':'))
                candidates = [k for k, p in self.projects.items() if p['language'] == 'java' and p['base'] == dest]
            else:
                for key, p in self.projects.items():
                    project_name = normalize_distribution(p['name']) if language == 'python' else p.get('coordinate', p.get('module', p['name']))
                    if p['language'] == language and project_name == name:
                        candidates.append(key)
            if len(candidates) == 1:
                target = candidates[0]
            elif kind in ('project_path', 'gradle_project') or len(candidates) > 1:
                self.warn(path, f'referência interna não resolvida ou ambígua: {name}')
                continue
            else:
                target = self.external(self.libraries, language, name, kind)
            self.libraries.add(source, target, path, line, f'declared:{kind}:{name}')
        # Requisitos soltos também são fontes de dependências da LIB sintética Python.
        for key, project in self.projects.items():
            if project['language'] == 'python' and project['manifest'] is None:
                req = project['base'] / 'requirements.txt'
                if req in self.files:
                    previous = len(self.pending)
                    self.requirements(key, req, set())
                    for source, kind, name, line, path in self.pending[previous:]:
                        target = self.external(self.libraries, 'python', name, kind)
                        self.libraries.add(source, target, path, line, f'declared:{kind}:{name}')

    def add_index(self, language, name, key):
        self.index.setdefault((language, name), []).append(key)

    def prepare_sources(self):
        dotnet_declarations = {}
        for path in self.files:
            language = EXTENSIONS.get(path.suffix)
            if language not in self.config['languages']:
                continue
            owners = self.owners(path, language)
            if len(owners) != 1:
                self.warn(path, 'projeto proprietário ambíguo; fonte omitida do grafo')
                continue
            owner = owners[0]
            project = self.projects[owner]
            text = self.read(path)
            info = dict(language=language, owner=owner, text=text, path=path, imports=[])
            if language == 'python':
                self.prepare_python(info, project)
            else:
                info['tokens'] = tokens(text)
                self.prepare_lexical(info, project)
            if 'module' not in info:
                continue
            self.sources[path] = info
            node = self.modules.nodes[info['module']]
            node.files.add(self.rel(path))
            lib = self.libraries.nodes[owner]
            lib.files.add(self.rel(path))
            node.total_types += info.get('total_types', 0)
            node.abstract_types += info.get('abstract_types', 0)
            lib.total_types += info.get('total_types', 0)
            lib.abstract_types += info.get('abstract_types', 0)
            if language == 'dotnet':
                declarations = dotnet_declarations.setdefault(node.id, {})
                for name, abstract in info.get('declarations', {}).items():
                    declarations[name] = declarations.get(name, False) or abstract
        # C# partial e variantes condicionais do mesmo tipo não inflam A.
        for key, declarations in dotnet_declarations.items():
            node = self.modules.nodes[key]
            node.total_types = len(declarations)
            node.abstract_types = sum(declarations.values())
        for key, lib in self.libraries.nodes.items():
            if lib.language == 'dotnet' and not lib.external:
                children = [n for n in self.modules.nodes.values() if n.library == key]
                lib.total_types = sum(n.total_types for n in children)
                lib.abstract_types = sum(n.abstract_types for n in children)

    def new_module(self, info, name, key):
        path = info['path']
        self.modules.nodes.setdefault(key, Node(key, name, info['language'], 'module', self.rel(path.parent), info['owner']))
        info['module'] = key
        info['module_name'] = name
        self.add_index(info['language'], name, key)

    def prepare_python(self, info, project):
        path = info['path']
        try:
            tree = ast.parse(info['text'], filename=self.rel(path))
        except SyntaxError as e:
            self.warn(path, f'Python inválido na linha {e.lineno}; fonte omitida')
            return
        roots = [self.root / p for p in self.config['python_roots']]
        roots += [project['base'] / 'src', project['base']]
        roots = [p for p in roots if path.is_relative_to(p)]
        base = max(roots, key=lambda p: len(p.parts))
        parts = list(path.relative_to(base).with_suffix('').parts)
        is_init = parts[-1] == '__init__'
        if is_init:
            parts.pop()
        name = '.'.join(parts) or project['name'].replace('-', '_')
        self.new_module(info, name, f'python:module:{self.rel(path)}')
        info['is_init'] = is_init
        info['tree'] = tree
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        abc_names, protocol_names, abstract_decorators = {'abc.ABC', 'abc.ABCMeta'}, {'typing.Protocol', 'typing_extensions.Protocol'}, {'abc.abstractmethod'}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                for alias in n.names:
                    qualified = f'{n.module}.{alias.name}'
                    if qualified in {'abc.ABC', 'abc.ABCMeta'}:
                        abc_names.add(alias.asname or alias.name)
                    if qualified in {'typing.Protocol', 'typing_extensions.Protocol'}:
                        protocol_names.add(alias.asname or alias.name)
                    if qualified == 'abc.abstractmethod':
                        abstract_decorators.add(alias.asname or alias.name)
            elif isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == 'abc':
                        prefix = alias.asname or 'abc'
                        abc_names.update({prefix + '.ABC', prefix + '.ABCMeta'})
                        abstract_decorators.add(prefix + '.abstractmethod')
                    if alias.name in ('typing', 'typing_extensions'):
                        protocol_names.add((alias.asname or alias.name) + '.Protocol')
        def expression(n):
            if isinstance(n, ast.Subscript):
                n = n.value
            return ast.unparse(n)
        # Só marcadores explícitos: uma implementação que herda Contract não é
        # necessariamente abstrata. Não execute nem simule __abstractmethods__.
        abstract_classes = set()
        for n in classes:
            base_abstract = any(expression(b) in abc_names | protocol_names for b in n.bases)
            meta_abstract = any(k.arg == 'metaclass' and expression(k.value) in abc_names for k in n.keywords)
            decorated = any(isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                            any(expression(d) in abstract_decorators for d in f.decorator_list) for f in n.body)
            if base_abstract or meta_abstract or decorated:
                abstract_classes.add(n)
        info['total_types'] = len(classes)
        info['abstract_types'] = len(abstract_classes)
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                info['imports'].extend((a.name, n.lineno, 'import', []) for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                info['imports'].append(('.' * n.level + (n.module or ''), n.lineno, 'from', [a.name for a in n.names]))
            elif isinstance(n, ast.Call) and expression(n.func) in ('__import__', 'importlib.import_module'):
                self.warn(path, f'import dinâmico Python não resolvido na linha {n.lineno}')

    def prepare_lexical(self, info, project):
        items, language, path = info['tokens'], info['language'], info['path']
        namespaces = []
        for i, t in enumerate(items):
            if t.kind == 'word' and t.value == ('namespace' if language == 'dotnet' else 'package') and language in ('dotnet', 'java'):
                j = i + 1
                while j < len(items) and (items[j].kind == 'word' or items[j].value == '.'):
                    j += 1
                if j > i + 1:
                    namespaces.append(dotted(items[i + 1:j]))
        if language in ('dotnet', 'java'):
            name = namespaces[0] if namespaces else '<global>'
            if len(set(namespaces)) > 1:
                self.warn(path, 'múltiplos namespaces por arquivo; tipos/imports atribuídos ao primeiro namespace')
            key = f"{language}:module:{self.libraries.nodes[info['owner']].path}:{name}"
        elif language == 'typescript':
            name, key = self.rel(path), f'typescript:module:{self.rel(path)}'
        else:
            suffix = path.parent.relative_to(project['base']).as_posix()
            name = project.get('module', project['name']) + ('/' + suffix if suffix != '.' else '')
            key = f"go:module:{self.libraries.nodes[info['owner']].path}:{suffix}"
        self.new_module(info, name, key)
        total, abstract = 0, 0
        if language == 'go':
            i = 0
            while i < len(items):
                if items[i].kind != 'word' or items[i].value != 'type':
                    i += 1
                    continue
                j = i + 1
                grouped = j < len(items) and items[j].value == '('
                if grouped:
                    j += 1
                while j < len(items) and items[j].kind == 'word':
                    total += 1
                    k = j + 1
                    if k < len(items) and items[k].value == '[':
                        k = self.after_balanced(items, k, '[', ']')
                    if k < len(items) and items[k].value == '=':
                        k += 1
                    if k < len(items) and items[k].value == 'interface':
                        abstract += 1
                    if not grouped:
                        break
                    depth = 0
                    start_line = items[j].line
                    j += 1
                    while j < len(items):
                        v = items[j].value
                        if depth == 0 and (v == ';' or v == ')' or items[j].line > start_line):
                            break
                        if v in ('{', '[', '('):
                            depth += 1
                        elif v in ('}', ']', ')'):
                            depth -= 1
                        j += 1
                    if j < len(items) and items[j].value == ';':
                        j += 1
                i = max(i + 1, j)
        else:
            declarations, spans = {}, []
            type_words = {'class', 'interface', 'enum', 'record', 'struct'} if language == 'dotnet' else {'class', 'interface', 'enum', 'record'} if language == 'java' else {'class', 'interface', 'enum', 'type'}
            for i, t in enumerate(items[:-1]):
                if t.kind != 'word' or t.value not in type_words or items[i + 1].kind != 'word':
                    continue
                if language == 'dotnet' and t.value in ('class', 'struct') and i and items[i - 1].value == 'record':
                    continue
                name_index = i + 2 if t.value == 'record' and items[i + 1].value in ('class', 'struct') else i + 1
                if name_index >= len(items) or items[name_index].kind != 'word':
                    continue
                after_name = name_index + 1
                arity = 0
                if after_name < len(items) and items[after_name].value == '<':
                    after_generic = self.after_balanced(items, after_name, '<', '>')
                    depth = 0
                    arity = 1
                    for token in items[after_name:after_generic]:
                        if token.value == '<':
                            depth += 1
                        elif token.value == '>':
                            depth -= 1
                        elif token.value == ',' and depth == 1:
                            arity += 1
                    after_name = after_generic
                if language == 'typescript' and t.value == 'type' and (after_name >= len(items) or items[after_name].value != '='):
                    # import type Foo é dependência, não declaração de tipo.
                    continue
                total += 1
                modifiers = []
                previous = i - 1
                while previous >= 0 and items[previous].kind == 'word' and items[previous].value in {
                    'abstract', 'partial', 'public', 'protected', 'private', 'internal', 'static', 'sealed',
                    'export', 'default', 'declare', 'final', 'strictfp', 'readonly', 'ref'}:
                    modifiers.append(items[previous].value)
                    previous -= 1
                is_abstract = t.value == 'interface' or t.value in ('class', 'record') and 'abstract' in modifiers
                abstract += bool(is_abstract)
                if language == 'dotnet':
                    type_name = items[name_index].value + f'`{arity}'
                    parents = [signature for start, end, signature in spans if start < i < end]
                    identity = '.'.join(parents + [type_name])
                    declarations[identity] = declarations.get(identity, False) or bool(is_abstract)
                    symbol = info['module_name'] + '.' + re.sub(r'`\d+', '', identity)
                    self.add_index(language, symbol, key)
                    self.type_names.add((language, symbol))
                    brace = after_name
                    while brace < len(items) and items[brace].value not in ('{', ';', '}'):
                        brace += 1
                    if brace < len(items) and items[brace].value == '{':
                        spans.append((brace, self.after_balanced(items, brace, '{', '}'), type_name))
                if language == 'java':
                    symbol = info['module_name'] + '.' + items[name_index].value
                    self.add_index(language, symbol, key)
                    self.type_names.add((language, symbol))
            if language == 'dotnet':
                info['declarations'] = declarations
        info['total_types'], info['abstract_types'] = total, abstract
        i = 0
        while i < len(items):
            t = items[i]
            if t.kind != 'word':
                i += 1
                continue
            if language in ('dotnet', 'java') and t.value == ('using' if language == 'dotnet' else 'import'):
                j = i + 1
                while j < len(items) and items[j].value in ('static',):
                    j += 1
                end = j
                while end < len(items) and items[end].value not in (';', '{', '}'):
                    end += 1
                seq = items[j:end]
                if any(x.value == '=' for x in seq):
                    assignment = next(n for n, x in enumerate(seq) if x.value == '=')
                    # using var x = ... e using Type x = ... são statements.
                    seq = seq[assignment + 1:] if assignment == 1 else []
                if seq and all(x.kind == 'word' or x.value in ('.', '*', ':') for x in seq):
                    info['imports'].append((dotted(seq).removeprefix('global::'), t.line, 'import', []))
                i = end
            elif language == 'go' and t.value == 'import':
                j = i + 1
                grouped = j < len(items) and items[j].value == '('
                if grouped:
                    j += 1
                    end = self.after_balanced(items, j - 1, '(', ')') - 1
                else:
                    end = min(len(items), j + 2)
                for token in items[j:end]:
                    if token.kind == 'string':
                        info['imports'].append((token.value, token.line, 'import', []))
                        if not grouped:
                            break
                i = end
            elif language == 'typescript' and t.value in ('import', 'export', 'require'):
                j = i + 1
                if j < len(items) and items[j].value == '(':
                    if j + 1 < len(items) and items[j + 1].kind == 'string':
                        info['imports'].append((items[j + 1].value, t.line, t.value, []))
                    elif t.value in ('import', 'require'):
                        self.warn(path, f'import dinâmico TypeScript não literal na linha {t.line}')
                elif t.value == 'import' and j < len(items) and items[j].kind == 'string':
                    info['imports'].append((items[j].value, t.line, 'import', []))
                else:
                    # Percorre apenas a declaração atual, inclusive import { ... } multiline.
                    while j < len(items) and items[j].value != ';':
                        if j > i + 1 and items[j].kind == 'word' and items[j].value in ('import', 'export', 'const', 'function', 'class'):
                            break
                        if items[j].kind == 'word' and items[j].value == 'from' and j + 1 < len(items) and items[j + 1].kind == 'string':
                            info['imports'].append((items[j + 1].value, t.line, t.value, []))
                            break
                        if items[j].value == 'require' and j + 2 < len(items) and items[j + 1].value == '(' and items[j + 2].kind == 'string':
                            info['imports'].append((items[j + 2].value, t.line, 'require', []))
                            break
                        j += 1
            i += 1
        if language == 'dotnet' and any(x in info['text'] for x in ('#if', '"""')):
            self.warn(path, 'pré-processamento/strings raw C# não interpretados integralmente; revisar cobertura lexical')

    @staticmethod
    def after_balanced(items, start, opening, closing):
        depth = 0
        for i in range(start, len(items)):
            if items[i].kind == 'string':
                continue
            if items[i].value == opening:
                depth += 1
            elif items[i].value == closing:
                depth -= 1
                if depth == 0:
                    return i + 1
        return len(items)

    def choose(self, info, name):
        candidates = sorted(set(self.index.get((info['language'], name), [])))
        own = [k for k in candidates if self.modules.nodes[k].library == info['owner']]
        reachable = [k for k in candidates if (info['owner'], self.modules.nodes[k].library) in self.libraries.edges]
        candidates = own or reachable or candidates
        if len(candidates) > 1:
            self.warn(info['path'], f'import ambíguo: {name}; relação omitida')
            return None, True
        return (candidates[0] if candidates else None), False

    def resolve_python(self, info, spec, style, names):
        if spec.startswith('.'):
            level = len(spec) - len(spec.lstrip('.'))
            parts = info['module_name'].split('.')
            package = parts if info['is_init'] else parts[:-1]
            if level > len(package):
                return [], True
            base = package[:len(package) - level + 1]
            name = '.'.join(base + ([spec[level:]] if spec[level:] else []))
        else:
            name = spec
        found, ambiguous = [], False
        target, bad = self.choose(info, name)
        if target:
            found.append(target)
        ambiguous |= bad
        if style == 'from':
            for child in names:
                if child == '*':
                    continue
                target, bad = self.choose(info, name + '.' + child)
                ambiguous |= bad
                if target:
                    found.append(target)
        # Namespace packages não têm __init__.py; from pkg import value é indeterminado
        # se pkg é interno e nenhum submódulo explícito foi encontrado.
        internal_prefix = any(lang == 'python' and (n == name or n.startswith(name + '.')) for lang, n in self.index)
        return sorted(set(found)), ambiguous or (not found and internal_prefix) or spec.startswith('.') and not found

    def tsconfig(self, path, seen=None):
        if path in self.tsconfigs:
            return self.tsconfigs[path]
        seen = set() if seen is None else seen
        if path in seen:
            self.warn(path, 'ciclo em extends do tsconfig; configuração omitida')
            return {}
        seen.add(path)
        try:
            data = jsonc(self.read(path))
        except (ValueError, TypeError):
            self.warn(path, 'tsconfig inválido; aliases não resolvidos')
            return {}
        if not isinstance(data, dict):
            self.warn(path, 'tsconfig deve ser um objeto; aliases não resolvidos')
            return {}
        result = {}
        parent = data.get('extends')
        if isinstance(parent, str):
            if parent.startswith('.'):
                candidate = (path.parent / parent).resolve()
                if candidate.suffix != '.json':
                    candidate = candidate.with_suffix('.json')
                if candidate in self.files:
                    result.update(self.tsconfig(candidate, seen))
                else:
                    self.warn(path, f'extends não disponível: {parent}')
            else:
                self.warn(path, f'extends de pacote não avaliado: {parent}')
        elif parent:
            self.warn(path, 'extends múltiplo não avaliado')
        options = data.get('compilerOptions', {})
        if not isinstance(options, dict) or not isinstance(options.get('paths', {}), dict):
            self.warn(path, 'compilerOptions/paths inválidos; aliases omitidas')
            return result
        if any(not isinstance(k, str) or not isinstance(v, list) or any(not isinstance(s, str) for s in v)
               for k, v in options.get('paths', {}).items()):
            self.warn(path, 'paths deve mapear strings para listas de strings; aliases omitidas')
            return result
        if 'baseUrl' in options:
            if not isinstance(options['baseUrl'], str):
                self.warn(path, 'baseUrl inválido; configuração omitida')
                return result
            result['base_url'] = (path.parent / options['baseUrl']).resolve()
        if 'paths' in options:
            result['paths'] = options['paths']
            result['paths_base'] = result.get('base_url', path.parent)
        self.tsconfigs[path] = result
        return result

    def ts_file(self, path):
        candidates = [path]
        substitutions = {'.js': ('.ts', '.tsx', '.d.ts'), '.mjs': ('.mts', '.d.mts'), '.cjs': ('.cts', '.d.cts')}
        if path.suffix in substitutions:
            candidates = [path.with_suffix(ext) for ext in substitutions[path.suffix]] + candidates
        if not path.suffix:
            candidates += [Path(str(path) + ext) for ext in ('.ts', '.tsx', '.mts', '.cts', '.d.ts')]
            candidates += [path / ('index' + ext) for ext in ('.ts', '.tsx', '.mts', '.cts', '.d.ts')]
        for p in candidates:
            source = self.sources.get(p.resolve())
            if source and source['language'] == 'typescript':
                return source['module']
        return None

    def resolve_ts(self, info, spec):
        path = info['path']
        if spec.startswith('.'):
            target = self.ts_file(path.parent / spec)
            return target, target is None
        configs = [p for p in self.files if p.name == 'tsconfig.json' and path.is_relative_to(p.parent)]
        options = self.tsconfig(max(configs, key=lambda p: len(p.parts))) if configs else {}
        aliases = options.get('paths', {})
        for pattern in sorted(aliases, key=lambda s: (-len(s.split('*')[0]), s)):
            wildcard = None
            if '*' in pattern:
                prefix, suffix = pattern.split('*', 1)
                if spec.startswith(prefix) and spec.endswith(suffix) and len(spec) >= len(prefix) + len(suffix):
                    wildcard = spec[len(prefix):len(spec) - len(suffix) if suffix else None]
            elif pattern == spec:
                wildcard = ''
            if wildcard is not None:
                for value in aliases[pattern]:
                    target = self.ts_file(options['paths_base'] / value.replace('*', wildcard))
                    if target:
                        return target, False
                return None, True
        if 'base_url' in options:
            target = self.ts_file(options['base_url'] / spec)
            if target:
                return target, False
        packages = [(key, p) for key, p in self.projects.items() if p['language'] == 'typescript' and
                    (spec == p['name'] or spec.startswith(p['name'] + '/'))]
        packages.sort(key=lambda pair: (-len(pair[1]['name']), pair[0]))
        if packages:
            best_length = len(packages[0][1]['name'])
            packages = [pair for pair in packages if len(pair[1]['name']) == best_length]
            own = [pair for pair in packages if pair[0] == info['owner']]
            packages = own or packages
            if len(packages) > 1:
                self.warn(path, f'package TypeScript ambíguo: {spec}')
                return None, True
            key, p = packages[0]
            suffix = spec[len(p['name']):].lstrip('/')
            data = p.get('package', {})
            exports = data.get('exports')
            entry = exports if isinstance(exports, str) and not suffix else exports.get('./' + suffix if suffix else '.') if isinstance(exports, dict) else None
            if isinstance(entry, dict):
                entry = entry.get('types') or entry.get('import') or entry.get('default')
            entry = entry if isinstance(entry, str) else suffix or data.get('types') or data.get('main') or 'index'
            target = self.ts_file(p['base'] / entry)
            if not target and not suffix:
                target = self.ts_file(p['base'] / 'src/index')
            return target, target is None
        return None, spec.startswith(('#', '/'))

    def source_edge(self, info, target, spec, line):
        path = self.rel(info['path'])
        self.modules.add(info['module'], target, path, line, f'import:{spec}')
        target_lib = self.modules.nodes[target].library
        if target_lib:
            self.libraries.add(info['owner'], target_lib, path, line, f'import:{spec}')

    def collect_imports(self):
        for path, info in sorted(self.sources.items()):
            language = info['language']
            for spec, line, style, names in info['imports']:
                found, unresolved = [], False
                if language == 'python':
                    found, unresolved = self.resolve_python(info, spec, style, names)
                elif language == 'typescript':
                    target, unresolved = self.resolve_ts(info, spec)
                    if target:
                        found = [target]
                elif language in ('dotnet', 'java'):
                    name = spec.removesuffix('.*')
                    target, unresolved = self.choose(info, name)
                    if not target and language == 'java' and not unresolved:
                        # Imports de tipos e imports estáticos, inclusive classes internas.
                        while '.' in name and not target and not unresolved:
                            name = name.rsplit('.', 1)[0]
                            if (language, name) in self.type_names:
                                target, unresolved = self.choose(info, name)
                        if not target and any(lang == 'java' and (spec.startswith(n + '.') or spec == n)
                                              for lang, n in self.index if (lang, n) not in self.type_names):
                            unresolved = True
                    if target:
                        found = [target]
                else:
                    target, unresolved = self.choose(info, spec)
                    if target:
                        found = [target]
                    elif any(p['language'] == 'go' and (spec == p['name'] or spec.startswith(p['name'] + '/')) for p in self.projects.values()):
                        unresolved = True
                if unresolved:
                    self.warn(path, f'import não resolvido na linha {line}: {spec}; relação interna pode estar ausente')
                for target in found:
                    self.source_edge(info, target, spec, line)
                if not found and not unresolved:
                    external_name = spec
                    if language == 'python':
                        external_name = spec.split('.')[0]
                    elif language == 'typescript' and not spec.startswith('node:'):
                        external_name = '/'.join(spec.split('/')[:2]) if spec.startswith('@') else spec.split('/')[0]
                    target = self.external(self.modules, language, external_name)
                    self.modules.add(info['module'], target, self.rel(path), line, f'import:{spec}')
                    # Relaciona import externo a pacote declarado só quando o nome é inequívoco.
                    candidates = []
                    for a, b in self.libraries.edges:
                        if a != info['owner'] or not self.libraries.nodes[b].external:
                            continue
                        package = self.libraries.nodes[b].name
                        matches = language == 'typescript' and external_name == package
                        matches |= language == 'python' and normalize_distribution(external_name) == package
                        matches |= language == 'go' and (spec == package or spec.startswith(package + '/'))
                        if matches:
                            candidates.append(b)
                    if candidates:
                        # Go seleciona a dependência cujo prefixo de módulo é mais específico.
                        destination = sorted(candidates, key=lambda k: (-len(self.libraries.nodes[k].name), k))[0]
                        self.libraries.add(info['owner'], destination, self.rel(path), line, f'import:{spec}')
                    elif language == 'typescript':
                        # Pacote importado mas ausente de dependencies (inclui devDependencies).
                        destination = self.external(self.libraries, language, external_name, 'package')
                        self.libraries.add(info['owner'], destination, self.rel(path), line, f'import:{spec}')

    def run(self):
        self.walk()
        self.discover()
        self.prepare_sources()
        self.collect_imports()
        for language in self.config['languages']:
            if not any(p['language'] == language for p in self.projects.values()):
                continue
            limitations = {
                'dotnet': 'coletor C# lexical de using e csproj; nomes totalmente qualificados, binding de símbolos, arquivos linked, VB/F# e avaliação MSBuild não cobertos',
                'java': 'imports Java e dependências declaradas; binding semântico, referências sem import, herança completa de builds e módulos JPMS não cobertos',
                'typescript': 'imports/reexports/require literais e resolução local aproximada; não substitui o resolvedor TypeScript, bundler ou conditional exports',
                'python': 'AST de imports explícitos; caminhos sys.path em runtime, plugins e resolução de distribuições versus nomes importados não inferidos',
                'go': 'imports e go.mod estáticos; build tags/cgo não avaliados, união de arquivos elegíveis sem seleção por GOOS/GOARCH',
            }
            self.warn(language, limitations[language])
        if not any(not n.external for n in self.modules.nodes.values()):
            self.warn('escopo', 'nenhum módulo de fonte elegível encontrado')
        return self
