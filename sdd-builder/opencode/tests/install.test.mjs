import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, readdir, rm, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { install } from '../dist/install.js';
import { resources, assets } from '../dist/resources.js';
async function fixture(t) { const root = await mkdtemp(join(tmpdir(), 'sdd projeto ')); t.after(() => rm(root, { recursive: true, force: true })); return root; }
test('instalação JSONC, repetição, atualização e remoção preservam configuração alheia', async t => {
  const root = await fixture(t);
  await writeFile(join(root, 'opencode.jsonc'), '{\n // configuração pessoal\n "plugins": ["outro"], "default_agent": "build",\n}\n');
  await install(root);
  assert.equal((await readdir(join(root, '.opencode/agents'))).length, 13);
  const config = await readFile(join(root, 'opencode.jsonc'), 'utf8');
  assert.match(config, /configuração pessoal/);
  assert.match(config, /"outro"/);
  assert.deepEqual(await install(root), []);
  await install(root, { packageSource: 'opencode-sdd-builder@1.5.0' });
  await install(root, { remove: true });
  assert.equal((await readdir(join(root, '.opencode/agents'))).length, 0);
  const result = await readFile(join(root, 'opencode.jsonc'), 'utf8');
  assert.match(result, /configuração pessoal/);
  assert.match(result, /"outro"/);
  assert.doesNotMatch(result, /opencode-sdd-builder/);
});
test('dry-run não cria arquivos nem Git', async t => {
  const root = await fixture(t);
  assert.equal((await install(root, { dryRun: true })).length, 15);
  assert.deepEqual(await readdir(root), []);
});
test('conflito em agente modificado aborta atualização e remoção sem escrita', async t => {
  const root = await fixture(t); await install(root);
  const config = await readFile(join(root, 'opencode.jsonc'), 'utf8');
  await writeFile(join(root, '.opencode/agents/sdd-builder.md'), 'personalizado');
  await assert.rejects(install(root), /modificado/);
  await assert.rejects(install(root, { remove: true }), /modificado/);
  assert.equal(await readFile(join(root, 'opencode.jsonc'), 'utf8'), config);
});
test('agente existente não é adotado nem sobrescrito', async t => {
  const root = await fixture(t); await mkdir(join(root, '.opencode/agents'), { recursive: true });
  await writeFile(join(root, '.opencode/agents/sdd-builder.md'), 'meu');
  await assert.rejects(install(root), /não gerenciado/);
  assert.equal(await readFile(join(root, '.opencode/agents/sdd-builder.md'), 'utf8'), 'meu');
});
test('configuração inválida ou dupla bloqueia antes de escrever', async t => {
  const root = await fixture(t); await writeFile(join(root, 'opencode.json'), '{');
  await assert.rejects(install(root), /inválida/);
  await writeFile(join(root, 'opencode.jsonc'), '{}');
  await assert.rejects(install(root), /Consolide/);
});
test('pacote contém seis skills, adaptador e referências canônicas', async () => {
  assert.equal((await resources()).length, 7);
  const contract = await readFile(join(assets, 'skills/solution-builder/references/contracts.md'), 'utf8');
  assert.ok(contract.length > 100);
});
test('agentes gerados mantêm corpos canônicos e só workers negam despacho', async () => {
  const { parse } = await import('yaml');
  const { fileURLToPath } = await import('node:url');
  for (const file of await readdir(join(assets, 'agents'))) {
    const output = await readFile(join(assets, 'agents', file), 'utf8');
    const source = await readFile(fileURLToPath(new URL('../../agents/' + file, import.meta.url)), 'utf8');
    const body = source.split(/\n---\n/).slice(1).join('\n---\n');
    assert.ok(output.includes(body), file);
    const meta = parse(output.match(/^---\n([\s\S]*?)\n---/)[1]);
    assert.equal(meta.model, undefined);
    assert.equal(meta.mode === 'subagent', file.includes('specialist'));
  }
});
