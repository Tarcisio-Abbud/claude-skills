#!/usr/bin/env python3
"""tk_site — the SITE file: what this machine is, and which environments exist.

Read by `tk-queue` (to validate an item's **Env:** field) and by the sibling
bins that came after it. It is the ONE place a deployment's proper names live:
the plugin ships no machine name, no roster and no ceiling of its own, exactly
as git ships no `user.name`.

ADDRESS: `~/.claude/tk/env` — beside the `~/.claude/tk/<skill>.md` site
extensions the skills already read. A fresh install has none, and nothing in tk
needs one until an item names an environment: `tk-queue --env` then refuses and
says what to write.

FORMAT — one `key = value` per line; `#` starts a comment; blank lines ignored.

    # this machine, and the environments an item may name
    identity = <this machine's environment name>
    environments = <name>, <name>, <name>
    # ceilings, per machine
    max-local-subagents = 3
    max-cloud-subagents = 4

  identity              REQUIRED. Which roster entry this machine IS. An item
                        whose Env names it — or names nothing — runs here.
  environments          REQUIRED. The whole roster, comma-separated. A value is
                        matched against it by EXACT equality: nothing is
                        normalised, because a normalised near-miss is precisely
                        the phantom environment the roster exists to prevent.
  max-local-subagents   optional. Concurrent LOCAL subagents this machine can
                        hold — a RAM ceiling, measured per machine.
  max-cloud-subagents   optional. Concurrent CLOUD subagents — a concurrency
                        ceiling only; it says nothing about quota, which is one
                        window shared by both venues.
  fleet-allow           optional. If present, the ONLY projects the fleet may
                        sweep. Absent means every queue on the machine enters.
  fleet-deny            optional. Projects the fleet must not touch. Applied
                        after `fleet-allow`, and it WINS over it: a name in both
                        is denied, because a "do not touch" that a second list
                        can overrule protects nothing.

A PROJECT is named either by the directory `~/.claude/projects/<name>` its queue
lives in, or by its absolute path — the two are the same name, since the first is
the second with every character outside `[A-Za-z0-9-]` replaced by `-`. Both are
matched by exact equality, the path after that encoding; nothing is normalised
here either. Which form to write is a matter of taste: the path is the readable
one, the directory name the one that survives a project being moved.

An environment NAME is a lowercase slug (`[a-z0-9][a-z0-9_-]*`, at most 32
chars), and never the word `none`, which every tk flag reserves for DELETING a
field: a roster entry spelled that way could be written into an item and never
removed from it.

UNKNOWN KEYS ARE IGNORED, so a later reader can add its own without an older tk
refusing the whole file — `fleet-allow` and `fleet-deny` below arrived exactly
that way, and the next key will too.
The cost is that a MISTYPED key reads as an absent one — so a missing required
key is reported together with the keys the file does carry, which puts the typo
in the message itself.

Every other defect is REFUSED, never guessed: a duplicate key, a line that is
not `key = value`, a malformed name, an identity outside its own roster, a
ceiling that is not a positive whole number. This file decides where work runs
and how much of it runs at once; a half-read one is worse than none.
"""

import os
import re

SITE_FILE = os.path.join("~", ".claude", "tk", "env")
# a roster entry: the slug shape, with a bound. The bound is not decoration —
# this value is written verbatim into an item's **Env:** field, and the field
# ceilings that bound every other field are measured against flags, not against
# a file the user hand-writes
NAME_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}\Z")
RESERVED_NAME = "none"
REQUIRED = ("identity", "environments")
CEILINGS = ("max-local-subagents", "max-cloud-subagents")
# The fleet's allow/denylist. Both optional, both comma-separated like
# `environments`, and both read by the roster sweep rather than by this module,
# which only says whether the file is trustworthy.
FLEET_LISTS = ("fleet-allow", "fleet-deny")
# The alphabet a project's queue DIRECTORY is spelled in, defined once and used
# both ways: `project_slug` encodes a path into it, and PROJECT_NAME_RE is what a
# name written by hand has to already be. Two spellings of one alphabet drift
# into a validator that accepts names the encoder can never produce.
PROJECT_ALPHABET = "A-Za-z0-9-"
UNSAFE_IN_PATH = re.compile(f"[^{PROJECT_ALPHABET}]")
# a name outside the alphabet (a relative path, a `~`, a Windows drive) is
# refused rather than encoded: encoding it would invent a project nobody has
PROJECT_NAME_RE = re.compile(f"[{PROJECT_ALPHABET}]+\\Z")

TEMPLATE = """  identity = <this machine's environment name>
  environments = <name>, <name>
  max-local-subagents = <concurrent local subagents>
  max-cloud-subagents = <concurrent cloud subagents>"""


class SiteError(Exception):
    """The site file exists and cannot be trusted. Callers report it verbatim:
    the message names the file and the line, which is the whole diagnosis."""


class Site:
    def __init__(self, path, identity, environments, ceilings,
                 fleet_allow=(), fleet_deny=()):
        self.path = path
        self.identity = identity          # str, always a member of environments
        self.environments = environments  # tuple, in the file's own order
        self.ceilings = ceilings          # {key: int}, only the keys present
        # both tuples, in the file's own order, EMPTY when the key is absent —
        # and an absent `fleet-allow` means every project enters, which is the
        # opposite of an empty one. That is why a present-but-empty list is
        # refused below instead of read as this same tuple
        self.fleet_allow = fleet_allow
        self.fleet_deny = fleet_deny


def project_slug(path):
    """The directory under ~/.claude/projects that holds `path`'s queue.

    The rule is `tk-queue`'s — it derives its own queue directory from the
    working directory this way, inline in memory_dir(). It lives here because
    two readers of the site file now need it (this module, to validate a
    fleet list; the roster sweep, to run it backwards), and a rule copied per
    reader is a rule that stops agreeing. The copy still in tk-queue is one
    import away from this one, and merges the day that file is free to edit.

    It is ONE-WAY: `/w/p/x-y` and `/w/p/x/y` produce the same name.
    """
    return UNSAFE_IN_PATH.sub("-", path)


def site_path():
    """Resolved at call time, never at import: a caller may set HOME (the test
    suite does, to stay off the real machine's file)."""
    return os.path.expanduser(SITE_FILE)


def missing_file_message(path=None):
    """Why `--env` cannot be honoured, and what to write. Not a bare 'not
    found': the file is one every deployment writes by hand, once, and a reader
    who is told only that it is missing has to go find its format."""
    return (f"the site file {path or site_path()} does not exist, so there is no roster "
            "to validate against — and an environment name nothing validated is a "
            f"phantom one, a typo no machine ever picks up. Create it:\n\n{TEMPLATE}\n\n"
            "`identity` is which of those environments THIS machine is.")


def missing_key_message(path, key, keys):
    """A required key is absent — reported WITH the keys the file does carry,
    because an unknown key is ignored (see the module docstring) and the most
    likely cause is one of those being this one, mistyped."""
    have = ", ".join(sorted(keys)) or "(no keys at all)"
    return (f"{path} declares no `{key}`. Keys it does carry: {have}. "
            f"Add the missing line — the file reads:\n\n{TEMPLATE}")


def parse(text, path):
    pairs = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key, sep, value = line.partition("=")
        if not sep:
            raise SiteError(f"{path}:{n}: not a `key = value` line: {line!r}. "
                            "Comment it with '#' or remove it.")
        key = key.strip()
        if key in pairs:
            # last-wins is how a line the user thought they had replaced keeps
            # deciding: two `identity` lines and the file says two things
            raise SiteError(f"{path}:{n}: duplicate key {key!r} — it is already set "
                            f"to {pairs[key]!r} earlier in the file. Keep one line.")
        pairs[key] = value.strip()

    for key in REQUIRED:
        if key not in pairs:
            raise SiteError(missing_key_message(path, key, pairs))
    names = [p.strip() for p in pairs["environments"].split(",") if p.strip()]
    if not names:
        # an empty roster validates nothing, so it is refused exactly like an
        # absent one — with its own wording, because "declares no environments"
        # about a file that plainly declares one sends the reader looking for a
        # line that is already there
        raise SiteError(f"{path}: `environments` is empty. The roster is the only thing "
                        "that says an environment exists, so an empty one validates "
                        f"nothing. The file reads:\n\n{TEMPLATE}")
    for name in names:
        if name == RESERVED_NAME:
            raise SiteError(
                f"{path}: {RESERVED_NAME!r} cannot be an environment name — every tk flag "
                f"reserves it for DELETING a field, so `--env {RESERVED_NAME}` clears an "
                "item's environment instead of setting this one. Rename it.")
        if not NAME_RE.match(name):
            raise SiteError(
                f"{path}: {name!r} is not a valid environment name — a lowercase slug "
                "(letters, digits, '-'/'_', at most 32 chars), no spaces, dots or capitals. "
                "The name is matched by exact equality, so it has to be typeable.")
    identity = pairs["identity"]
    if identity not in names:
        raise SiteError(
            f"{path}: identity {identity!r} is not one of the environments "
            f"({', '.join(names)}). A machine that is not in its own roster is a machine "
            "where NOTHING counts as local — every item would look like another "
            "machine's. Add it to `environments`, or fix the spelling.")
    ceilings = {}
    for key in CEILINGS:
        if key not in pairs:
            continue
        value = pairs[key]
        if not re.fullmatch(r"[0-9]+", value):
            raise SiteError(f"{path}: {key} must be a whole number of subagents, "
                            f"not {value!r}.")
        if int(value) < 1:
            raise SiteError(f"{path}: {key} is {value} — a ceiling of zero lets nothing "
                            "run at all. Use 1 or more, or drop the line to leave it unset.")
        ceilings[key] = int(value)
    lists = {}
    for key in FLEET_LISTS:
        raw = pairs.get(key)
        if raw is None:
            # deliberately not the ceilings loop's `if key not in pairs: continue`
            # above: that literal is a mutation anchor, and a second copy of it in
            # this file makes the mutation match twice and stop running at all
            continue
        entries = [p.strip() for p in raw.split(",") if p.strip()]
        if not entries:
            # an absent list and an empty one mean OPPOSITE things (see Site):
            # read as the absent one, `fleet-allow =` would silently sweep every
            # project the line was written to keep out
            raise SiteError(f"{path}: `{key}` is empty. Absent, it lets every project "
                            "through; written, it is a list. Name a project, or delete "
                            "the line.")
        for entry in entries:
            if entry.startswith("/"):
                continue          # a path, encoded to a directory name by the reader
            if not PROJECT_NAME_RE.match(entry):
                raise SiteError(
                    f"{path}: {entry!r} in `{key}` is neither a project directory under "
                    "~/.claude/projects (letters, digits and '-') nor an absolute path "
                    "starting with '/'. A relative path names no project: write the path "
                    "the project is opened at, or the directory its queue lives in.")
        lists[key] = tuple(entries)
    return Site(path, identity, tuple(names), ceilings,
                fleet_allow=lists.get("fleet-allow", ()),
                fleet_deny=lists.get("fleet-deny", ()))


def load(path=None):
    """The parsed site file, or None when there is none — the two cases the
    caller answers differently (one asks the user to create it; the other names
    the defect). Raises SiteError for a file that exists and is unusable.

    The reading itself is guarded, and not only the parsing: a defect does not
    have to be in the file's TEXT to exist. Measured on this module — a site
    file that was a DIRECTORY, and one carrying a single non-UTF-8 byte, each
    came back as a Python traceback, which names a line of THIS file while the
    line that has to change is in the user's. Both are ordinary ways to mistype
    a path or save from the wrong editor, and the module's whole contract is
    that a defect comes back as a diagnosis.

    The BOM is stripped for the same reason: an editor that writes one glues it
    onto the first key, so `identity` read as ABSENT while sitting in plain view
    on line 1 — a diagnosis honest about what it saw and useless to the reader,
    who has no reason to suspect an invisible character. It is removed
    EVERYWHERE rather than by decoding with `utf-8-sig`, which strips exactly
    one, at the very start: two of them (a file saved twice, or two files
    concatenated) put the bug straight back, and so does one at the head of any
    later line. U+FEFF has no legitimate use in a file of slugs and numbers, and
    `str.strip()` does not remove it — it is not whitespace.

    The regular-file check is the third of these: `open()` on a FIFO with no
    writer does not raise, it BLOCKS — the session hangs with no output at all,
    which is worse than the traceback the guards above replace, and no timeout
    anywhere would explain it.
    """
    path = path or site_path()
    if not os.path.exists(path):
        return None
    if not os.path.isfile(path):
        raise SiteError(f"{path} is not a plain file (it is a directory, a device or a "
                        "pipe). The site file is hand-written text — check the path.")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read().replace("﻿", "")
    except OSError as e:
        raise SiteError(f"{path} cannot be read: {e.strerror}. It has to be a plain "
                        "text file — check that the path is not a directory and that "
                        "it is readable.")
    except UnicodeDecodeError as e:
        raise SiteError(f"{path} is not valid UTF-8 (byte {e.object[e.start]:#04x} at "
                        f"position {e.start}). Save it as UTF-8 — a machine name is a "
                        "plain slug, so the offending byte is almost certainly in a "
                        "comment.")
    return parse(text, path)
