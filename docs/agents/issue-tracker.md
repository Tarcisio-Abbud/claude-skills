# Issue tracker: GitHub, on a repo that is not this one

Code lands here. Issues and specs live on a **private** tracker, whose slug appears in no
versioned file of this repo — this one is public. The slug lives in the clone's local git
config, which git never pushes.

## Reach the tracker through `bin/tracker-gh`

```bash
bin/tracker-gh issue list -R '{tracker}' --state open --json number,title,labels
bin/tracker-gh api "repos/{tracker}/issues/<n>/sub_issues" --paginate
```

It resolves `tk.tracker` and `tk.ghConfigDir`, substitutes `{tracker}` in every argument,
exports the gh identity, and runs `gh` — **all in the one process that runs the command.**
Exit 78 is the wrapper refusing; any other status is `gh`'s own.

Resolving into a shell variable instead is the trap this replaces, and it fails in two ways
that both end in the same place:

- **Across tool calls.** The cwd persists between an agent's commands; shell state does not.
  Resolve in one call, run `gh` in the next, and the variable is gone.
- **Inside one interactive shell.** `${VAR:?}` does not end an interactive session. The
  message prints, the prompt returns, the next line runs anyway — and because the last
  command overwrites `$?`, checking the status afterwards shows `0`.

What lands in the gap is not an error. `git config` answers a missing key with an empty
string at exit 0, and **`gh` DISCARDS an empty `-R` and falls back to the cwd's remote —
this PUBLIC repo.** Measured: `gh issue view 1 -R ""` returns this repo's issue #1 at exit 0.
Since `issue create`, `comment`, `edit --add-label` and `close` are all built the same way,
the accident WRITES to the public repo, it does not merely read it. An empty
`GH_CONFIG_DIR` degrades just as quietly, to whatever identity the environment carries.

The wrapper closes that because there is no gap: no separate resolution step to lose.

**Naming `{tracker}` is not the same as going there**, and treating it as such was its own
hole — `issue create -R other/repo --title "about {tracker}"` satisfied a presence check and
performed an authenticated WRITE to an arbitrary repo, stamping the private slug into the
title it created. So the wrapper reads back, after substitution, every argument that can
decide the target — the value of `-R`/`--repo`, any `repos/<owner>/<repo>` path, any
`github.com/<owner>/<repo>` URL — and runs only when at least one names the tracker and none
names anything else. A command mentioning `{tracker}` ten times in a body still goes nowhere
if its target is another repo, and a command that decides no target at all is refused too,
because that is where `gh` falls back to the cwd's remote.

The placeholder requirement stays, as HYGIENE rather than safety: typing the slug on a command
line puts it in shell history and in the session transcript, which is the leak this whole
arrangement exists to avoid.

`tk.tracker` is also checked for SHAPE before it is compared or pasted. A value carrying `|`
or `&` used to reach a `sed` replacement, where one emptied every argument while the run still
exited 0 and the other corrupted an argument in silence. Substitution is plain shell expansion
now, and a value outside `<owner>/<repo>` is refused rather than interpreted.

An unconfigured clone gets exit 78 and these two lines to hand the user:

```bash
git config tk.tracker <owner>/<repo>
git config tk.ghConfigDir <path to the gh config directory>
```

`/setup-matt-pocock-skills` answers the same question by writing the slug into this file,
which is versioned — that publishes the private tracker's name. Configure the clone instead.

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
PRs live on this repo, not on the tracker, so this one runs through `gh` directly. `-F
key=@<path>` reads the value from the file, which keeps a body full of backticks and newlines
out of the shell's reach.

## Conventions

| Operation | Command |
|---|---|
| Read a ticket | `bin/tracker-gh issue view <n> -R '{tracker}' --json number,title,state,labels,body,comments` |
| List | `bin/tracker-gh issue list -R '{tracker}' --state open --json number,title,labels` |
| Comment | `bin/tracker-gh issue comment <n> -R '{tracker}' --body-file <file>` |
| Label | `bin/tracker-gh issue edit <n> -R '{tracker}' --add-label "..."` / `--remove-label "..."` |
| Close | `bin/tracker-gh issue close <n> -R '{tracker}' --comment "..."` |
| Publish to the tracker | `bin/tracker-gh issue create -R '{tracker}' ...` |

Quote `'{tracker}'` in single quotes: unquoted braces are a glob pattern to some shells. The
shell also expands backticks inside `-m` and `--body`, so multi-line or code-carrying text
goes through `--body-file` / `-F` with a file.

## Pull requests: the split

A change lands as a PR **on this repo** — the cwd default, so plain `gh`, no wrapper:

- **Create**: push the branch, then `gh pr create --base main --head <branch> --title "..." --body-file <file>`
- **Read**: `gh pr view <n> --json title,body,comments,reviewDecision` + `gh pr diff <n>`
- **Merge**: the human's call, since this repo's `main` is consumed by a running installation.

Keep PR titles, PR bodies and commit messages here free of the tracker's slug, of ticket
numbers from it, and of account or company names: describe the change on its own terms, and
name the work by what it is — "tk v3 slice" — rather than by the ticket's number, which
belongs to the private tracker. The cross-reference goes the other way — comment the PR's URL
onto the ticket.

### The commit guard

`githooks/private-values` guards the commits. Install it once per clone, as both hooks:

```bash
hooks="$(git rev-parse --path-format=absolute --git-common-dir)/hooks"
install -m 755 githooks/private-values "$hooks/pre-commit"
install -m 755 githooks/private-values "$hooks/commit-msg"
```

Copying the script into the git directory, rather than pointing `core.hooksPath` at
`githooks/`, is deliberate: a worktree checked out at a branch older than that directory would
leave the guard silently inert.

**What it catches, each proved by a test that fails when the check is removed.** It reads four
surfaces — the lines a commit adds, the paths it introduces, the commit message, and the
branch name, which is pushed and public exactly like a path — and names the one that fired. A
value is recognised through the disguises that defeated earlier versions of it: a different
case, `%2F` and `%252F` in place of the slash, a value wrapped across two lines, a value
inside a staged binary, a pure rename INTO a leaky path, and a branch name spelling the
identity through any punctuation or none — `Owner-repo`, `Owner.repo`, `Ownerrepo` — since on
that surface every character that is not a letter or a digit is dropped before comparing.

**What it does not catch. Read this before trusting it.**

- **`git cherry-pick` and `git rebase` run neither hook.** Measured by instrumenting the
  script: it is never invoked. A commit made with `--no-verify` on a private branch therefore
  reaches this public repo through either of them with nothing in its way. Closing that needs
  a `pre-push` hook, which does not exist here — so on a branch built by rebase or cherry-pick,
  read the diff yourself before pushing.
- **It reads only what a commit ADDS.** A value already tracked stays; this is a gate on new
  writes, not an audit of history.
- **PR titles and bodies travel through `gh`, never through git**, so no hook sees them. Tag
  names are not read either. That half is yours to keep clean.
- **It knows two literals, not a category.** It greps the values of `tk.tracker` and
  `tk.ghConfigDir`, following encoding two levels deep and no further. Company names, people's
  names and ticket numbers of the private tracker are equally unwelcome here and equally
  invisible to it.
- **One refusal is genuinely ambiguous.** When the value appears only after consecutive added
  lines of a file are joined, that is either a wrapped value or two unrelated lines meeting at
  its seam. The message says so and prints the command that shows the two lines; deciding is
  yours, and `--no-verify` is the right answer for a real coincidence.

Re-prove the lot with `python3 githooks/tests/mutations_private_values.py`, which puts each
defect back and requires the test named for it to fail. The wrapper answers to
`python3 bin/tests/mutations_tracker_gh.py` the same way.

## Wayfinding operations

A package's map is an issue on the tracker carrying the `wayfinder:map` label. Find it by the
label rather than by a number, which goes stale as packages come and go:

```bash
bin/tracker-gh issue list -R '{tracker}' --label wayfinder:map --state open --json number,title
```

Zero rows means no package is live; add `--state all` to reach a concluded one. More than one
row means more than one package is live — pick the map that owns the ticket you were handed,
and say which one you picked.

### The frontier is a heuristic, and it rests on data that is often absent

Read this before using it, because the failure is silent: it returns an empty list, which
reads as "no work left".

The frontier — the package's open tickets that nobody has claimed — is computed from the
map's **sub-issue edges**:

```bash
bin/tracker-gh api "repos/{tracker}/issues/<map>/sub_issues" --paginate \
  --jq '[.[] | select(.state == "open")] | length'
```

**More than zero** — the edges are live, and the frontier is trustworthy:

```bash
bin/tracker-gh api "repos/{tracker}/issues/<map>/sub_issues" --paginate \
  --jq '.[] | select(.state == "open" and .assignee == null) | "\(.number)\t\(.title)"'
```

**Zero** — stop. It does NOT mean the package is finished, and this is the case that actually
occurs. Measured on this tracker: a map carried 19 children, every one of them closed, while
five open tickets of the same package carried `parent: null` — never linked at all. The count
was truthful and the conclusion drawn from it would have been wrong.

Nothing queryable distinguishes the two, because the heuristic depends on data that may simply
not exist. It needs **one** of these, and on the measured map neither held:

- the **parent-child edge**, which is what `sub_issues` reads; or
- the **map's body listing its tickets**. On the measured map the body cited none of the five
  open ones — they appear only in the comments, and their titles share a prefix that is
  written down in no contract, so matching on it would be guessing dressed as a query.

So when the count is zero, do not write a fourth query. **Ask the user which tickets belong to
the package**, and say that you are asking because the map's edges are missing. If they want
the guessing removed for good, the fix is in the DATA, not here: linking the tickets as
sub-issues of their map is an action on the tracker, outside this repo.

Whatever route produced your list, say which one it was, so the next reader can tell a
frontier that is empty from one that was never found.

Claim a ticket with `bin/tracker-gh issue edit <n> -R '{tracker}' --add-assignee @me`; resolve
it with a comment and a close. Edges between tickets go through `gh api`:

```bash
bin/tracker-gh api "repos/{tracker}/issues/<n>/dependencies/blocked_by" \
  -F issue_id=<blocker DATABASE id>
```

The database id comes from `bin/tracker-gh api "repos/{tracker}/issues/<n>" --jq .id`, and
differs from the `#number`. A ticket carrying an open blocker is not on the frontier even when
nobody has claimed it.
