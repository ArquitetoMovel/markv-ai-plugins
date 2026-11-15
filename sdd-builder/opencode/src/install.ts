import { readFile, writeFile, readdir, mkdir, rename, rm, lstat, realpath } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { parse, modify, applyEdits, type ParseError } from 'jsonc-parser';
import { assets } from './resources.js';
const digest = (s: string) => createHash('sha256').update(s).digest('hex');
async function read(path: string) { try { return await readFile(path, 'utf8'); } catch (e) { if ((e as NodeJS.ErrnoException).code === 'ENOENT') return undefined; throw e; } }
type State = { version: 1; config: string; plugin: string; files: Record<string, string> };
export async function install(project: string, options: { remove?: boolean; dryRun?: boolean; packageSource?: string } = {}) {
  const root = await realpath(project);
  const base = join(root, '.opencode');
  for (const path of [base, join(base, 'agents')]) {
    try { if ((await lstat(path)).isSymbolicLink()) throw new Error(`Diretório gerenciado não pode ser link: ${path}`); }
    catch (e) { if ((e as NodeJS.ErrnoException).code !== 'ENOENT') throw e; }
  }
  const statePath = join(base, 'sdd-builder-install.json');
  const previousText = await read(statePath);
  const previous: State | undefined = previousText ? JSON.parse(previousText) : undefined;
  if (previous && (previous.version !== 1 || !['opencode.json', 'opencode.jsonc'].includes(previous.config) || Object.keys(previous.files).some(f => !/^sdd-[a-z-]+\.md$/.test(f)))) throw new Error('Registro de instalação inválido.');
  const json = await read(join(root, 'opencode.json'));
  const jsonc = await read(join(root, 'opencode.jsonc'));
  if (json !== undefined && jsonc !== undefined) throw new Error('Há opencode.json e opencode.jsonc. Consolide antes de instalar.');
  const config = previous?.config ?? (json !== undefined ? 'opencode.json' : 'opencode.jsonc');
  const configPath = join(root, config);
  const original = await read(configPath) ?? '{}\n';
  const errors: ParseError[] = [];
  const parsed = parse(original, errors, { allowTrailingComma: true });
  if (errors.length || !parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Configuração OpenCode inválida.');
  if (parsed.plugins !== undefined && !Array.isArray(parsed.plugins)) throw new Error('plugins deve ser uma lista.');
  const plugins: unknown[] = parsed.plugins ?? [];
  const source = options.packageSource ?? resolve(assets, '../..');
  const managed = previous?.plugin;
  const pluginName = (p: unknown) => typeof p === 'string' ? p : p && typeof p === 'object' && 'package' in p ? p.package : undefined;
  if (!previous && plugins.some(p => String(pluginName(p)).includes('opencode-sdd-builder') || pluginName(p) === source)) throw new Error('Entrada SDD existente sem registro gerenciado. Reconcilie manualmente.');
  const changes = new Map<string, string | undefined>();
  const hashes: Record<string, string> = {};
  for (const [file, hash] of Object.entries(previous?.files ?? {})) {
    const current = await read(join(base, 'agents', file));
    if (current !== undefined && digest(current) !== hash) throw new Error(`Arquivo modificado pelo usuário: ${file}`);
  }
  if (options.remove) {
    if (!previous) return ['Nenhuma instalação gerenciada.'];
    for (const file of Object.keys(previous.files)) changes.set(join(base, 'agents', file), undefined);
  } else {
    for (const file of await readdir(join(assets, 'agents'))) {
      const path = join(base, 'agents', file);
      const content = await readFile(join(assets, 'agents', file), 'utf8');
      const current = await read(path);
      if (!previous?.files[file] && current !== undefined) throw new Error(`Agente existente não gerenciado: ${file}`);
      changes.set(path, content);
      hashes[file] = digest(content);
    }
    for (const file of Object.keys(previous?.files ?? {})) if (!hashes[file]) changes.set(join(base, 'agents', file), undefined);
  }
  const indices = plugins.flatMap((p, i) => pluginName(p) === managed ? [i] : []);
  if (previous && (indices.length !== 1 || plugins[indices[0]] !== managed)) throw new Error('Entrada gerenciada do plugin foi alterada. Reconcilie antes de continuar.');
  let configText = original;
  const formattingOptions = { insertSpaces: true, tabSize: 2, eol: '\n' };
  if (previous) configText = applyEdits(configText, modify(configText, ['plugins', indices[0]], options.remove ? undefined : source, { formattingOptions }));
  else if (!options.remove) configText = applyEdits(configText, modify(configText, parsed.plugins ? ['plugins', plugins.length] : ['plugins'], parsed.plugins ? source : [source], { formattingOptions }));
  if (configText !== original) changes.set(configPath, configText);
  changes.set(statePath, options.remove ? undefined : JSON.stringify({ version: 1, config, plugin: source, files: hashes } satisfies State, null, 2) + '\n');
  const actions: string[] = [];
  for (const [path, content] of changes) if (await read(path) !== content) actions.push(`${content === undefined ? 'Remover' : 'Gravar'} ${path}`);
  if (options.dryRun || actions.length === 0) return actions;
  await mkdir(base, { recursive: true });
  const lock = join(base, 'sdd-builder-install.lock');
  await mkdir(lock); // instalação concorrente deve falhar, nunca sobrescrever.
  const backups = new Map<string, string | undefined>();
  async function atomic(path: string, content: string | undefined) {
    if (content === undefined) { await rm(path, { force: true }); return; }
    await mkdir(resolve(path, '..'), { recursive: true });
    const temp = `${path}.${randomUUID()}.tmp`;
    try { await writeFile(temp, content, { flag: 'wx' }); await rename(temp, path); }
    finally { await rm(temp, { force: true }); }
  }
  try {
    // Valida novamente após adquirir o lock, antes da primeira escrita.
    if ((await read(statePath)) !== previousText || (await read(configPath) ?? '{}\n') !== original) throw new Error('Configuração mudou durante instalação. Tente novamente.');
    for (const [path, content] of changes) {
      const before = await read(path);
      backups.set(path, before);
      if (before !== content) await atomic(path, content);
    }
  } catch (error) {
    for (const [path, before] of [...backups].reverse()) await atomic(path, before);
    throw error;
  } finally { await rm(lock, { recursive: true }); }
  return actions;
}
