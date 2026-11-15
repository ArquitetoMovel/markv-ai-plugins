// Teste real sem chamadas a provedores: instala o tarball fora do checkout.
import { mkdtemp, mkdir, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { spawn, execFileSync } from 'node:child_process';
import { OpenCode } from '@opencode/client';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const source = fileURLToPath(new URL('../', import.meta.url));
const root = await mkdtemp(join(tmpdir(), 'sdd pacote '));
let server;
try {
  const pack = JSON.parse(execFileSync('npm', ['pack', '--ignore-scripts', '--json', '--pack-destination', root], { cwd: source, encoding: 'utf8' }));
  const consumer = join(root, 'consumer'); await mkdir(consumer);
  execFileSync('npm', ['install', '--prefix', consumer, '--ignore-scripts', '--no-audit', join(root, Object.values(pack)[0].filename)], { stdio: 'pipe' });
  const installed = join(consumer, 'node_modules/opencode-sdd-builder');
  const project = join(root, 'workspace neutro'); await mkdir(project);
  execFileSync(process.execPath, [join(installed, 'dist/cli.js'), 'install', '--project', project]);
  const env = { ...process.env, XDG_CONFIG_HOME: join(root, 'config'), XDG_DATA_HOME: join(root, 'data'), XDG_STATE_HOME: join(root, 'state'), XDG_CACHE_HOME: join(root, 'cache') };
  server = spawn('opencode', ['serve', '--port', '0', '--hostname', '127.0.0.1'], { cwd: project, env });
  let output = ''; server.stdout.on('data', b => output += b); server.stderr.on('data', () => {});
  const pause = () => new Promise(r => setTimeout(r, 100));
  for (let i = 0; i < 200 && !output.includes('server password '); i++) { if (server.exitCode !== null) throw new Error('Servidor encerrou antes de iniciar.'); await pause(); }
  const url = output.match(/server listening on (\S+)/)?.[1];
  const password = output.match(/server password (\S+)/)?.[1];
  assert.ok(url && password, 'Servidor deve iniciar em até 20 segundos');
  const client = OpenCode.make({ baseUrl: url, headers: { Authorization: 'Basic ' + Buffer.from('opencode:' + password).toString('base64'), 'x-opencode-directory': project } });
  let skills;
  for (let i = 0; i < 200; i++) { skills = await client.skill.list(); if (skills.data.some(x => x.id === 'sdd-opencode')) break; await pause(); }
  assert.equal(skills.data.filter(x => x.id.startsWith('sdd-')).length, 7);
  const agents = await client.agent.list();
  assert.equal(agents.data.filter(x => x.id.startsWith('sdd-')).length, 13);
  const commands = await client.command.list();
  assert.equal(commands.data.filter(x => ['sdd', 'sdd-prd', 'sdd-spec', 'sdd-feature', 'sdd-solution'].includes(x.name)).length, 5);
  const plugins = await client.plugin.list();
  assert.equal(plugins.data.find(x => x.id === 'opencode-sdd-builder').state.status, 'active');
  const parent = await client.session.create({ agent: 'sdd-builder' });
  const child = await client.session.create({ parentID: parent.id, agent: 'sdd-python-specialist' });
  assert.equal(child.parentID, parent.id);
  assert.equal((await client.session.context({ sessionID: child.id })).length, 0);
  await client.session.remove({ sessionID: parent.id });
  console.log('OpenCode 2.2.6: tarball externo, plugin ativo, 13 agentes, 7 skills, 5 comandos e sessão filha vazia verificados.');
} finally {
  if (server && server.exitCode === null) { server.kill('SIGTERM'); await new Promise(r => server.once('exit', r)); }
  await rm(root, { recursive: true, force: true });
}
