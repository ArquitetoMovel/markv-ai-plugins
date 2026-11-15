import { test } from 'node:test';
import assert from 'node:assert/strict';
import { registerDispatch, acquire } from '../dist/runtime.js';
import { randomUUID } from 'node:crypto';
function harness(overrides = {}) {
  const tools = new Map(), calls = [];
  const ctx = {
    tool: { transform: async f => f({ add: t => tools.set(t.name, t) }) },
    model: { list: async () => ({ data: [{ providerID: 'p', id: 'm' }] }), default: async () => ({ data: { providerID: 'p', id: 'm' } }) },
    permission: { assert: async x => calls.push(['permission', x]) },
    session: { get: async ({ sessionID }) => ({ id: sessionID, model: { providerID: 'p', id: 'm' }, outcome: 'succeeded', location: { directory: process.cwd() } }), create: async x => { calls.push(['create', x]); return { id: 'child' }; }, prompt: async x => calls.push(['prompt', x]), wait: async () => {}, context: async () => ['evidências'], interrupt: async x => calls.push(['interrupt', x]), ...overrides },
  };
  return { ctx, tools, calls };
}
const input = { agent: 'sdd-python-specialist', directory: process.cwd(), model: 'p/m', packet: 'somente esta unidade' };
const context = () => ({ sessionID: 'parent', agent: 'sdd-builder', signal: new AbortController().signal });
test('sessão isolada recebe pacote mínimo e modelo explícito, sem copiar histórico', async () => {
  const h = harness(); await registerDispatch(h.ctx);
  const result = JSON.parse((await h.tools.get('sdd_dispatch').execute(input, context())).content);
  assert.equal(result.outcome, 'succeeded'); assert.equal(result.requestedModel, 'p/m');
  const created = h.calls.find(c => c[0] === 'create')[1];
  assert.equal(created.parentID, 'parent'); assert.deepEqual(created.model, { providerID: 'p', id: 'm' });
  assert.equal(created.permissions.find(x => x.action === 'edit').effect, 'deny');
  assert.equal(h.calls.find(c => c[0] === 'prompt')[1].text, input.packet);
});
test('modelo inexistente não cria sessão e não aplica fallback', async () => {
  const h = harness(); await registerDispatch(h.ctx);
  await assert.rejects(h.tools.get('sdd_dispatch').execute({ ...input, model: 'inexistente' }, context()), /não disponível/);
  assert.ok(!h.calls.some(c => c[0] === 'create'));
});
test('filho não pode abrir nova delegação', async () => {
  const h = harness({ get: async () => ({ metadata: { sddWorker: true } }) }); await registerDispatch(h.ctx);
  await assert.rejects(h.tools.get('sdd_dispatch').execute(input, context()), /não podem delegar/);
});
test('locks excluem concorrência e podem ser readquiridos após conclusão', async () => {
  const key = randomUUID(); const release = await acquire(key, 'primeiro');
  await assert.rejects(acquire(key, 'segundo'), /ocupado/);
  await release(); await (await acquire(key, 'segundo'))();
});
test('limite global impede quarto worker e libera slots ao concluir', async () => {
  const releases = await Promise.all([0, 1, 2].map(i => acquire(`slot:${i}`, 'teste')));
  try {
    const h = harness(); await registerDispatch(h.ctx);
    await assert.rejects(h.tools.get('sdd_dispatch').execute(input, context()), /Três janelas/);
  } finally { await Promise.all(releases.map(r => r())); }
});
test('cancelamento interrompe a sessão filha', async () => {
  const controller = new AbortController();
  const h = harness({ prompt: async () => controller.abort(), wait: async () => {} }); await registerDispatch(h.ctx);
  await assert.rejects(h.tools.get('sdd_dispatch').execute(input, { ...context(), signal: controller.signal }), /Falha SDD/);
  assert.ok(h.calls.some(c => c[0] === 'interrupt'));
});
test('falha de worker preserva outcome e nunca declara conclusão da feature', async () => {
  const h = harness({ get: async ({ sessionID }) => ({ id: sessionID, location: { directory: process.cwd() }, model: { providerID: 'p', id: 'm' }, outcome: sessionID === 'child' ? 'failed' : undefined }) });
  await registerDispatch(h.ctx);
  const result = JSON.parse((await h.tools.get('sdd_dispatch').execute({ ...input, model: 'inherit' }, context())).content);
  assert.equal(result.outcome, 'failed'); assert.equal(result.requestedModel, 'inherit');
});
test('mesmo Git serializa diretórios distintos e libera a concessão', async t => {
  const { mkdtemp, mkdir, rm, realpath } = await import('node:fs/promises');
  const { tmpdir } = await import('node:os'); const { join } = await import('node:path');
  const { execFileSync } = await import('node:child_process');
  const root = await realpath(await mkdtemp(join(tmpdir(), 'sdd git ')));
  t.after(() => rm(root, { recursive: true, force: true }));
  execFileSync('git', ['init', '--quiet', root]); await mkdir(join(root, 'projeto'));
  let unblock; const waiting = new Promise(r => unblock = r);
  let started; const ready = new Promise(r => started = r);
  const h = harness({ wait: async () => { started(); await waiting; } }); await registerDispatch(h.ctx);
  const call = h.tools.get('sdd_dispatch').execute({ ...input, directory: root, gitRoot: root }, context());
  await ready;
  try { await assert.rejects(h.tools.get('sdd_dispatch').execute({ ...input, directory: join(root, 'projeto'), gitRoot: root }, context()), /ocupado/); }
  finally { unblock(); await call; }
  const next = harness(); await registerDispatch(next.ctx);
  await next.tools.get('sdd_dispatch').execute({ ...input, directory: root, gitRoot: root }, context());
});
