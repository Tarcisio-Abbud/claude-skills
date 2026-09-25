# The brief the lens is handed

`SKILL.md` §2 reaches this file once the angle is picked. Hand the block over whole, filled in;
the angle's line below fills its `Attack:` field, and §1's prose exception adds two constraints
to it.

- **system**: extract the state machine; every state needs a named entry and exit; find the
  seam where two parts must agree and neither is wrong alone.
- **data**: feed the ugly, duplicated, real input and watch what comes out.
- **regression**: a KEEP / MOVE / DROP table of every behaviour against the base.

```
You are the <ANGLE> lens on <slice>. Base: <base>. Diff: git diff <base>...HEAD.
Read the item or issue that ordered this slice, body and comments: <the ready command>.
Invariants the slice must hold, beyond the ones you find there: <list them>.
Firing receipt: <receipt>. A receipt that is wrong is itself a defect: report it.
Attack: <the angle's line>.
You are alone. Cover what carries the worst failure, not what is cheapest to check.
Run the artifact on inputs you build from the real population it will meet.
Reproduce every finding and paste the run: a code reading is not proof.
Switch each new guard off in a copy and run the suite; green is a finding.
Find the input or the state that walks past each new guard while the guard is still there.
Where the slice writes data a later reader consumes, interrupt and replay every write
path and read back what it left behind.
Ask what the code does with input it never enumerated: a default that absorbs the
unknown destroys data in silence, a default that refuses is recoverable.
Report each finding as: grade (nit | defect), the guard or invariant it violates, a
concrete failure scenario (input or state -> wrong output), and the run that proves it.
Close with the class of defect this slice keeps producing, where there is one.
Finding nothing is a full answer, and it carries the same evidence: every attack you ran,
the artifact it touched, and the run that shows it ran.
```
