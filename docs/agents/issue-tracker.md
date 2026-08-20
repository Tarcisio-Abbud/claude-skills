# Issue tracker: GitHub, on a repo that is not this one

Code lands here. Issues and specs live on a **private** tracker, whose slug appears in no
versioned file of this repo — this one is public. The slug lives in the clone's local git
config, which git never pushes.

## Resolve the tracker before anything else

Read both values from git config. Linked worktrees share one config, so this works from any
of them:

```bash
TRACKER=$(git config tk.tracker)                     # owner/repo of the private tracker
export GH_CONFIG_DIR="$(git config tk.ghConfigDir)"  # directory holding the gh token
```

An empty `TRACKER` means this clone was never configured. Stop there and give the user these
two lines to run, then continue:

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
gh api -X PATCH "repos/OWNER/REPO/pulls/<n>" -F body=@<path to a file>
```

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

It refuses a commit whose staged content or message carries either configured value —
`pre-commit` sees the content, `commit-msg` sees the message, and one script covers both.
**PR titles and bodies reach GitHub through `gh`, never through git, so no hook sees them:
that half is yours to keep clean.** The guard reads only the lines a commit ADDS and the paths it
touches, so a value already in the tree is left alone rather than blamed on the commit that
edited its neighbour. It guards new writes; it is not an audit of history.

Copying the script into the git directory, rather than pointing `core.hooksPath` at
`githooks/`, is deliberate: a worktree checked out at a branch older than that directory would
leave the guard silently inert. Prove it still bites with
`python3 githooks/tests/mutations_private_values.py`.

## Wayfinding operations

A package's map is an issue on `$TRACKER` carrying the `wayfinder:map` label, and its tickets
are the map's children through GitHub sub-issues. Find the map by the label rather than by a
number, which goes stale as packages come and go:

```bash
gh issue list -R "$TRACKER" --label wayfinder:map --state open --json number,title
```

More than one row means more than one package is live: pick the map whose children include
the ticket you were handed, and say which one you picked. Add `--state all` only to reach a
concluded package.

List the children, and with them the frontier — the open ones carrying no assignee:

```bash
gh api "repos/$TRACKER/issues/<map>/sub_issues" --paginate \
  --jq '.[] | select(.state == "open" and .assignee == null) | "\(.number)\t\(.title)"'
```

Claim one with `gh issue edit <n> -R "$TRACKER" --add-assignee @me`; resolve it with a comment
and a close. Edges between tickets go through `gh api`:

```bash
gh api "repos/$TRACKER/issues/<n>/dependencies/blocked_by" -F issue_id=<blocker DATABASE id>
```

The database id comes from `gh api "repos/$TRACKER/issues/<n>" --jq .id`, and differs from the
`#number`. A ticket carrying an open blocker is not on the frontier even when nobody has
claimed it.
