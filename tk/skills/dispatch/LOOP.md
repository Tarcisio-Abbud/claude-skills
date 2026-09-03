# The `loop.md` contract

`.claude/loop.md` at the project root replaces plain `/loop`'s default prompt, turning `/loop`
into the dispatcher of the `next-steps.md` queue. Create the file the first time you dispatch a
project's queue this way, and check on every later dispatch that it still matches the contract:

```markdown
Read the queue at ~/.claude/projects/<cwd-slug>/memory/next-steps.md. Execute ONLY the
top AUTONOMOUS item — one slice per iteration — and verify the result. Resolve it via
`tk-queue done <id> --how "<pointer>"` (the script is the queue's only writer; its
contract is `reference/queue.md` of the `tk` plugin). No AUTONOMOUS item left: end
the loop and summarize what remains.
```

An edit takes effect on the next iteration. The file belongs to the project and is versioned
there; the queue stays in auto-memory.
