# difyctl skill

One agent skill for the difyctl CLI: `skills/difyctl/`. It uses the standard
Agent Skills layout. `SKILL.md` is the root; the docs it links to sit under
`references/`.

The difyctl binary carries a built-in copy. `difyctl install skills <dir>`
writes that copy into `<dir>`. `--from` points at any GitHub folder with the
same layout, or at a local folder. The same files install through the Vercel
installer: `npx skills add langgenius/dify --skill difyctl -g`.

## Changing the skill

The skill is a tree of linked docs, so an agent reads only the branch it needs.

- `SKILL.md` frontmatter has `name` (`difyctl`) and `description`. The
  description says when to use the skill.
- A doc that links to other docs is a map. Keep each map under 60 lines.
- Every doc is at most 2 hops from `SKILL.md`. Leaves do not link onward.
- Write links as "Read X when ...", so the agent knows when to follow them.
- A leaf over 100 lines opens with a `## Contents` list.
- Put each fact in one place and link to it from elsewhere.
- Any files may sit beside the docs: `scripts/`, `assets/`. Commit scripts as
  executable (`chmod +x`); the installer keeps the bit.

`cli/test/skills/tree.test.ts` checks links, depth, sizes, and that every
`difyctl` command in backticks exists locally or in
`cli/test/fixtures/catalog.json`. Add an op's descriptor there when a doc starts
naming it.

A change here reaches users with the next difyctl build. Anyone can get it
sooner with `--from https://github.com/langgenius/dify/tree/main/skills`.
