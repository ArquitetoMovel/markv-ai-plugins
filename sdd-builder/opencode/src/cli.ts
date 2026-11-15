#!/usr/bin/env node
import { install } from './install.js';
const args = process.argv.slice(2);
try {
  const command = args.shift();
  if (!['install', 'uninstall'].includes(command ?? '')) throw new Error('Uso: opencode-sdd-builder install|uninstall --project <diretório> [--dry-run] [--npm]');
  let project = process.cwd(), dryRun = false, npm = false;
  while (args.length) {
    const arg = args.shift();
    if (arg === '--project' && args[0] && !args[0].startsWith('--')) project = args.shift()!;
    else if (arg === '--dry-run') dryRun = true;
    else if (arg === '--npm') npm = true;
    else throw new Error(`Argumento inválido: ${arg}`);
  }
  const changes = await install(project, { remove: command === 'uninstall', dryRun, packageSource: npm ? 'opencode-sdd-builder@1.5.0' : undefined });
  console.log(changes.join('\n') || 'Instalação já atualizada.');
} catch (e) { console.error(String(e)); process.exitCode = 1; }
