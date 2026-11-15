import type { Plugin } from '@opencode/plugin';
import { mkdir, realpath, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, relative, isAbsolute } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { assets } from './resources.js';
type Context = Parameters<Plugin.Plugin['setup']>[0];
const locks = join(tmpdir(), 'opencode-sdd-builder-locks');
export async function acquire(name: string, owner: string) {
  await mkdir(locks, { recursive: true });
  const path = join(locks, createHash('sha256').update(name).digest('hex'));
  try { await mkdir(path); } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'EEXIST') throw new Error(`Recurso SDD ocupado: ${name}. Reconcilie a sessão antes de tentar novamente.`);
    throw error;
  }
  try { await writeFile(join(path, 'owner.json'), JSON.stringify({ owner, pid: process.pid, resource: name })); }
  catch (error) { await rm(path, { recursive: true }); throw error; }
  return () => rm(path, { recursive: true });
}
export async function registerDispatch(ctx: Context) {
  const agents: { name: string; worker: boolean }[] = JSON.parse(await readFile(join(assets, 'agents.json'), 'utf8'));
  await ctx.tool.transform(editor => {
    editor.add({ name: 'sdd_models', description: 'Consultar catálogo real e modelo padrão para escolhas SDD por papel.', input: { type: 'object', properties: {}, additionalProperties: false }, execute: async () => ({ content: JSON.stringify({ models: await ctx.model.list(), default: await ctx.model.default() }) }) });
    editor.add({ name: 'sdd_dispatch', description: 'Executar pacote SDD em sessão isolada; no máximo 3 janelas globais e um writer por Git.', input: {
      type: 'object', properties: { agent: { type: 'string' }, directory: { type: 'string' }, model: { type: 'string' }, gitRoot: { type: 'string' }, packet: { type: 'string' } }, required: ['agent', 'directory', 'model', 'packet'], additionalProperties: false,
    }, execute: async (raw, context) => {
      const input = raw as { agent: string; directory: string; model: string; gitRoot?: string; packet: string };
      if (!agents.some(x => x.name === input.agent)) throw new Error('Agente SDD desconhecido.');
      const parent = await ctx.session.get({ sessionID: context.sessionID });
      if (parent.metadata?.sddWorker) throw new Error('Sessões filhas SDD não podem delegar. Retorne o plano ao root.');
      if (!isAbsolute(input.directory) || (input.gitRoot && !isAbsolute(input.gitRoot))) throw new Error('directory e gitRoot devem ser absolutos.');
      const directory = await realpath(input.directory);
      let model = parent.model;
      if (input.model !== 'inherit') {
        const models = (await ctx.model.list()).data;
        const selected = models.find(m => `${m.providerID}/${m.id}` === input.model);
        if (!selected) throw new Error('Modelo não disponível. Solicite nova escolha ao usuário.');
        model = { providerID: selected.providerID, id: selected.id };
      }
      if (!model) { const selected = (await ctx.model.default()).data; if (selected) model = { providerID: selected.providerID, id: selected.id }; }
      if (!model) throw new Error('Modelo herdado indisponível. Solicite escolha ao usuário.');
      await ctx.permission.assert({ sessionID: context.sessionID, agent: context.agent, action: 'sdd_dispatch', resources: [input.agent] });
      const boundary = relative(await realpath(parent.location.directory), directory);
      if (boundary.startsWith('..') || isAbsolute(boundary)) await ctx.permission.assert({ sessionID: context.sessionID, agent: context.agent, action: 'external_directory', resources: [`${directory}/*`] });
      let releaseSlot: undefined | (() => Promise<void>);
      for (let i = 0; i < 3; i++) {
        try { releaseSlot = await acquire(`slot:${i}`, context.sessionID); break; }
        catch (e) { if (!(e instanceof Error && e.message.startsWith('Recurso SDD ocupado'))) throw e; }
      }
      if (!releaseSlot) throw new Error('Três janelas SDD ocupadas. Aguarde as unidades ativas.');
      let releaseGit: undefined | (() => Promise<void>);
      let child: Awaited<ReturnType<Context['session']['create']>> | undefined;
      let safeToRelease = true;
      const interrupt = () => { if (child) void ctx.session.interrupt({ sessionID: child.id, resume: false }).catch(() => {}); };
      try {
        if (input.gitRoot) {
          const gitRoot = await realpath(input.gitRoot);
          const detected = await realpath(execFileSync('git', ['-C', directory, 'rev-parse', '--show-toplevel'], { encoding: 'utf8' }).trim());
          if (gitRoot !== detected) throw new Error('gitRoot não corresponde ao projeto alvo.');
          // --git-common-dir também serializa worktrees do mesmo repositório.
          const common = execFileSync('git', ['-C', directory, 'rev-parse', '--path-format=absolute', '--git-common-dir'], { encoding: 'utf8' }).trim();
          releaseGit = await acquire(`git:${await realpath(common)}`, context.sessionID);
        }
        context.signal.throwIfAborted();
        child = await ctx.session.create({ parentID: context.sessionID, title: `SDD ${input.agent}`, agent: input.agent, model, location: { directory }, metadata: { sddWorker: true, requestedModel: input.model }, permissions: [
          { action: 'subagent', resource: '*', effect: 'deny' },
          { action: 'sdd_dispatch', resource: '*', effect: 'deny' },
          ...(!input.gitRoot ? [{ action: 'edit', resource: '*', effect: 'deny' as const }, { action: 'shell', resource: '*', effect: 'deny' as const }] : []),
        ] });
        context.signal.addEventListener('abort', interrupt, { once: true });
        context.signal.throwIfAborted();
        await ctx.session.prompt({ sessionID: child.id, text: input.packet });
        safeToRelease = false;
        await ctx.session.wait({ sessionID: child.id });
        safeToRelease = true;
        context.signal.throwIfAborted();
        const result = await ctx.session.get({ sessionID: child.id });
        return { content: JSON.stringify({ sessionID: child.id, outcome: result.outcome, requestedModel: input.model, resolvedModel: model, effectiveModel: result.model, messages: await ctx.session.context({ sessionID: child.id }) }) };
      } catch (error) {
        if (child) {
          try { await ctx.session.interrupt({ sessionID: child.id, resume: false }); await ctx.session.wait({ sessionID: child.id }); safeToRelease = true; }
          catch { safeToRelease = false; }
        }
        throw new Error(`Falha SDD${child ? ` na sessão ${child.id}` : ''}: ${String(error)}${safeToRelease ? '' : '. Locks preservados; reconciliação manual obrigatória.'}`);
      } finally {
        context.signal.removeEventListener('abort', interrupt);
        if (safeToRelease) { await releaseGit?.(); await releaseSlot(); }
      }
    } });
  });
}
