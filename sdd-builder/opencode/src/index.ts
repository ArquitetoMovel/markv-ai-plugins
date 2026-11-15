import { Plugin, Skill } from '@opencode/plugin';
import { resources } from './resources.js';
import { registerDispatch } from './runtime.js';
export default Plugin.define({
  id: 'opencode-sdd-builder',
  async setup(ctx) {
    if (ctx.app.version !== '2.2.6') throw new Error('SDD requer OpenCode 2.2.6 validado.');
    const skills = await resources();
    await ctx.skill.transform(editor => {
      for (const skill of skills) {
        const entry = { ...skill, id: Skill.ID.make(skill.id), name: Skill.Name.make(skill.name), path: Skill.Info.fields.path.make(skill.path) };
        const existing = editor.get(skill.id);
        if (existing && existing.path !== skill.path) throw new Error(`Skill SDD em conflito: ${skill.id}`);
        if (!existing) editor.add(entry);
      }
    });
    await ctx.command.transform(editor => {
      for (const [name, agent] of Object.entries({ sdd: 'sdd-builder', 'sdd-prd': 'sdd-prd-builder', 'sdd-spec': 'sdd-spec-builder', 'sdd-feature': 'sdd-feature-builder', 'sdd-solution': 'sdd-solution-builder' })) {
        editor.add({ name, description: `Executar ${agent}`, execute: async ({ sessionID, prompt, delivery }) => {
          await ctx.session.switchAgent({ sessionID, agent });
          await ctx.session.prompt({ ...prompt, sessionID, delivery });
        } });
      }
    });
    await registerDispatch(ctx);
  },
});
