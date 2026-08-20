# Triage labels

The five canonical triage roles carry their canonical names on the tracker, so the mapping is
the identity:

| Canonical role | Label string on the tracker | Meaning |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | Maintainer needs to evaluate this issue |
| `needs-info` | `needs-info` | Waiting on the reporter for more information |
| `ready-for-agent` | `ready-for-agent` | Fully specified, ready for an AFK agent |
| `ready-for-human` | `ready-for-human` | Requires human implementation |
| `wontfix` | `wontfix` | Will not be actioned |

All five exist on the tracker. [`issue-tracker.md`](issue-tracker.md) resolves `$TRACKER` and
`GH_CONFIG_DIR` and carries the `gh` gotchas that shape every command here — read it first,
then:

```bash
gh issue edit <n> -R "$TRACKER" --add-label "<label>"
```
