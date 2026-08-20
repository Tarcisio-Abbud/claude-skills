# Issue tracker: GitHub, on a repo that is not this one

Code lands here. Issues and specs live on a **private** tracker, whose slug appears in no
versioned file of this repo — this one is public. The slug lives in the clone's local git
config, which git never pushes.

## Resolve the tracker before anything else

Read both values from git config — linked worktrees share one config, so this works from any
of them — and let the resolution ITSELF refuse an absent value:

```bash
TRACKER="$(git config tk.tracker)"
GH_CONFIG_DIR="$(git config tk.ghConfigDir)"
: "${TRACKER:?this clone has no tk.tracker — configure it before running any gh command}"
: "${GH_CONFIG_DIR:?this clone has no tk.ghConfigDir — configure it before running any gh command}"
export GH_CONFIG_DIR
```

The two `:?` lines are the load-bearing part, not decoration. `git config` answers a missing
key with an empty string and exit 0, and **`gh` discards an empty `-R` and falls back to the
cwd's remote — which here is the PUBLIC repo.** Measured: `gh issue view 1 -R ""` returns this
repo's issue #1 at exit 0. Every command below is built as `-R "$TRACKER"`, and the table
includes `issue create`, `comment`, `edit --add-label` and `close`, so in an unconfigured
clone an unguarded empty value does not merely read the wrong repo — it WRITES to the public
one. `${VAR:?}` turns that silent redirection into a non-zero exit before any `gh` runs.

When it does refuse, the clone was never configured. Give the user these two lines, wait for
them, then resolve again:

```bash
git config tk.tracker <owner>/<repo>
git config tk.ghConfigDir <path to the gh config directory>
```

`/setup-matt-pocock-skills` answers the same question by writing the slug into this file,
which is versioned — that publishes the private tracker's name. Configure the clone instead.

## Every issue command carries `-R "$TRACKER"`

The cwd's `git remote` points at this public repo, so a command without `-R` reads and writes
the wrong tracker. Pull requests are the exception: they belong to this repo and take no `-R`.

## Read single items through `--json`

The `gh` here is 2.23.0, and every command that walks the classic-Projects GraphQL path dies
on its deprecation notice with exit 1: `gh issue view <n>` and `gh pr view <n>`, with or
without `--comments`, and `gh pr edit <n>` whatever flag it carries.

Reads have an escape: `--json` takes them off that path, so ask for fields and they work.
Add `--jq` when you want the answer shaped — it is not what makes the command succeed.

`gh pr edit` has no such escape, which makes a PR's title and body right-at-creation work:
pass them to `gh pr create`, the body through `--body-file`. To change either afterwards, go
around `gh pr edit` through the REST endpoint, which does not touch that GraphQL path:

```bash
gh api -X PATCH "repos/{owner}/{repo}/pulls/<n>" -F body=@<path to a file>
```

`{owner}/{repo}` is `gh`'s own placeholder for the cwd's repo, which is the right one here —
PRs live on this repo, not on `$TRACKER`.

`-F key=@<path>` reads the value from the file, which keeps a body full of backticks and
newlines out of the shell's reach.

List, create, comment and diff behave normally.

## Conventions

| Operation | Command |
|---|---|
| Read a ticket | `gh issue view <n> -R "$TRACKER" --json number,title,state,labels,body,comments` + `--jq` |
| List | `gh issue list -R "$TRACKER" --state open --json number,title,labels` |
| Comment | `gh issue comment <n> -R "$TRACKER" --body "..."` |
| Label | `gh issue edit <n> -R "$TRACKER" --add-label "..."` / `--remove-label "..."` |
| Close | `gh issue close <n> -R "$TRACKER" --comment "..."` |
| Publish to the tracker | `gh issue create -R "$TRACKER" ...` |

The shell expands backticks inside `-m` and `--body`, so multi-line or code-carrying text goes
through `--body-file` / `-F` with a file.

## Pull requests: the split

A change lands as a PR **on this repo** — the cwd default:

- **Create**: push the branch, then `gh pr create --base main --head <branch> --title "..." --body-file <file>`
- **Read**: `gh pr view <n> --json title,body,comments,reviewDecision` + `gh pr diff <n>`
- **Merge**: the human's call, since this repo's `main` is consumed by a running installation.

Keep PR titles, PR bodies and commit messages here free of the tracker's slug, of ticket
numbers from it, and of account or company names: describe the change on its own terms, and
name the work by what it is — "tk v3 slice" — rather than by the ticket's number, which
belongs to the private tracker. The cross-reference goes the other
way — comment the PR's URL onto the ticket with `gh issue comment <n> -R "$TRACKER"`.

`githooks/private-values` guards the commits. Install it once per clone, as both hooks:

```bash
hooks="$(git rev-parse --path-format=absolute --git-common-dir)/hooks"
install -m 755 githooks/private-values "$hooks/pre-commit"
install -m 755 githooks/private-values "$hooks/commit-msg"
```

Copying the script into the git directory, rather than pointing `core.hooksPath` at
`githooks/`, is deliberate: a worktree checked out at a branch older than that directory would
leave the guard silently inert.

**What it catches, each proved by a test that fails when the check is removed.** It reads
three surfaces — the lines a commit adds, the paths it introduces, and the commit message —
and names the one that fired. A value is recognised through the disguises that defeated
earlier versions of it: a different case (a GitHub slug is case-insensitive, so a re-cased
copy publishes the same identity), `%2F` in place of the slash, a value wrapped across two
lines, a value inside a staged binary, and a pure rename INTO a leaky path, which adds no
line at all.

**What it does not catch. Read this before trusting it.**

- **`git cherry-pick` and `git rebase` run neither hook.** Measured by instrumenting the
  script: it is never invoked. A commit made with `--no-verify` on a private branch therefore
  reaches this public repo through either of them with nothing in its way. Closing that needs
  a `pre-push` hook, which does not exist here — so on a branch built by rebase or cherry-pick,
  read the diff yourself before pushing.
- **It reads only what a commit ADDS.** A value already tracked stays; this is a gate on new
  writes, not an audit of history.
- **PR titles and bodies travel through `gh`, never through git**, so no hook sees them. That
  half is yours to keep clean.
- **It knows two literals, not a category.** It greps the values of `tk.tracker` and
  `tk.ghConfigDir`. Company names, people's names and ticket numbers of the private tracker
  are equally unwelcome here and equally invisible to it.

Re-prove the lot with `python3 githooks/tests/mutations_private_values.py`, which puts each
defect back and requires the test named for it to fail.

## Wayfinding operations

A package's map is an issue on `$TRACKER` carrying the `wayfinder:map` label. Find it by the
label rather than by a number, which goes stale as packages come and go:

```bash
gh issue list -R "$TRACKER" --label wayfinder:map --state open --json number,title
```

Zero rows means no package is live; add `--state all` to reach a concluded one. More than one
row means more than one package is live — pick the map that owns the ticket you were handed,
and say which one you picked.

### Count the children before trusting the frontier

The tickets are meant to be the map's children through GitHub sub-issues, but **the edge is
not reliably there**: measured on this tracker, open tickets of a live package carry
`parent: null`, never having been linked. So ask how many children exist BEFORE asking which
are free, or an unlinked package reads as a finished one:

```bash
gh api "repos/$TRACKER/issues/<map>/sub_issues" --paginate --jq 'length'
```

- **Zero** — the edges were never made. This is not an empty frontier, and the package is not
  done. Fall back to the tracker's own open list, and use the map's body to decide which of
  those rows belong to it:
  `gh issue list -R "$TRACKER" --state open --search "no:assignee" --json number,title`
- **More than zero** — the edges exist, so the frontier is the open children with no assignee:

```bash
gh api "repos/$TRACKER/issues/<map>/sub_issues" --paginate \
  --jq '.[] | select(.state == "open" and .assignee == null) | "\(.number)\t\(.title)"'
```

Either way, say which route gave you the list, so the next reader can tell a real empty
frontier from a missing one. Claim a ticket with
`gh issue edit <n> -R "$TRACKER" --add-assignee @me`; resolve it with a comment and a close.
Edges between tickets go through `gh api`:

```bash
gh api "repos/$TRACKER/issues/<n>/dependencies/blocked_by" -F issue_id=<blocker DATABASE id>
```

The database id comes from `gh api "repos/$TRACKER/issues/<n>" --jq .id`, and differs from the
`#number`. A ticket carrying an open blocker is not on the frontier even when nobody has
claimed it.
