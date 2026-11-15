import { readFile, readdir, mkdir, rm, cp, writeFile, chmod } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { parse, stringify } from 'yaml';
const root = fileURLToPath(new URL('../', import.meta.url));
await rm(resolve(root, 'dist'), { recursive: true, force: true });
execFileSync(resolve(root, 'node_modules/.bin/tsc'), [], { cwd: root, stdio: 'inherit' });
await mkdir(resolve(root, 'dist/assets/agents'), { recursive: true });
await cp(resolve(root, '../skills'), resolve(root, 'dist/assets/skills'), { recursive: true });
const agents = [];
for (const file of (await readdir(resolve(root, '../agents'))).filter(x => x.endsWith('.md')).sort()) {
  const source = await readFile(resolve(root, '../agents', file), 'utf8');
  const [, front, body] = source.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/) ?? [];
  if (!front) throw new Error(`Frontmatter inválido: ${file}`);
  const meta = parse(front);
  const worker = meta.name.endsWith('-specialist');
  const permissions = [
    { action: 'subagent', resource: '*', effect: 'deny' },
    ...(worker ? [{ action: 'sdd_dispatch', resource: '*', effect: 'deny' }] : []),
  ];
  const header = { description: meta.description, mode: worker ? 'subagent' : meta.name === 'sdd-builder' ? 'primary' : 'all', permissions };
  const skills = meta.skills.map(x => x.split(':')[1]);
  const output = `---\n${stringify(header)}---\n${body}\n\n## Adaptação OpenCode\n\nLeia primeiro as skills ${skills.map(x => '`sdd-' + x + '`').join(', ')} e a skill \`sdd-opencode\`. Elas preservam os contratos canônicos. Referências \`sdd-builder-plugin:<skill>\` correspondem a \`sdd-<skill>\` neste host. As ferramentas citadas no texto usam os equivalentes nativos do OpenCode; \`Task\` corresponde a \`sdd_dispatch\`.\n`;
  await writeFile(resolve(root, 'dist/assets/agents', file), output);
  agents.push({ name: meta.name, skills, worker });
}
await writeFile(resolve(root, 'dist/assets/agents.json'), JSON.stringify(agents, null, 2));
await cp(resolve(root, 'adapter.md'), resolve(root, 'dist/assets/adapter.md'));
await chmod(resolve(root, 'dist/cli.js'), 0o755);
