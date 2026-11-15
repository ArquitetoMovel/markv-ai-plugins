import { readFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { parse } from 'yaml';
export const assets = fileURLToPath(new URL('./assets/', import.meta.url));
export async function resources() {
  const skills = [];
  for (const dir of await readdir(join(assets, 'skills'))) {
    const path = join(assets, 'skills', dir, 'SKILL.md');
    const text = await readFile(path, 'utf8');
    const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
    if (!match) throw new Error(`Skill inválida: ${path}`);
    const meta = parse(match[1]);
    skills.push({ id: `sdd-${dir}`, name: `sdd-${dir}`, description: meta.description, path, content: match[2] });
  }
  skills.push({ id: 'sdd-opencode', name: 'sdd-opencode', description: 'Execução SDD no OpenCode: modelos, sessões e permissões', path: join(assets, 'adapter.md'), content: await readFile(join(assets, 'adapter.md'), 'utf8') });
  return skills;
}
