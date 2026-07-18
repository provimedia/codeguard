# The Senior Card — the questions an experienced developer keeps asking

Five sections. §A runs at intake (SKILL.md carries the compact form). §B–§E
stay active for the whole task: re-read the anchored section at each
code-guardian step and answer its questions against the actual work.

## §B — Architecture & design (before the first line)

- Am I solving the RIGHT problem? Confirm the problem before building a
  solution — the most expensive mistake is a correct solution to the wrong
  problem.
- **Does this already exist?** Function, class, helper, package — search the
  codebase BEFORE writing anything new. Writing a duplicate is worse than
  reading for five minutes.
- How does THIS project do it? Follow existing patterns; do not introduce a
  second way to do the same thing.
- Simplest design that works (KISS). No abstraction for an imagined future —
  "premature flexibilization is the root of whatever evil is left."
- Do we need it NOW? (YAGNI) Nothing gets built because it might be needed.
- Name the trade-offs out loud: performance vs. maintainability vs.
  simplicity vs. time-to-done. Which one matters for THIS task? Choosing
  without naming them is guessing.
- Second-order effects: what follow-up cost does the fast path create?
  What operational load, what debt gets more expensive later?
- Database: new table or new column? Normalize to 3NF/4NF by default;
  denormalize only with a MEASURED reason (join cost, read latency), never
  by habit. FK + constraints so invalid states cannot exist. Indexes follow
  real query patterns, not intuition.

## §C — While coding (the senior over your shoulder)

- Do I understand what I am writing — or am I guessing? Code you cannot
  explain does not get committed. Guessing → stop, read, spike.
- The 6-month test: does the code tell its own story? Names express intent;
  no magic numbers; a reader should not need you next to them.
- Am I repeating myself? Second copy of the same logic → is there ONE place
  it belongs? (Rule of Three governs extraction — two copies watch, three
  extract.)
- Is this unit getting too big? One responsibility per function/class/file.
  A file that needs scrolling to understand is a file that needs splitting.
- Edge cases, every time: null, empty, zero, huge, concurrent, error path.
- Does it scale? Works at 10 rows AND at 1 million — loops in loops, N+1
  queries, missing indexes are found NOW, not in production.
- Comments explain WHY, never WHAT — and never talk to the reviewer.
- Still in scope? No drive-by refactoring; pre-existing findings are
  reported, not silently fixed (code-guardian Operating Principle 3).

## §D — Meta view (continuous: "does this make sense?")

- Does this still make sense, seen from outside? Ask it as if a senior just
  walked up behind you and looked at the screen.
- Rabbit-hole check: two failed attempts on the same spot → STOP. Write your
  assumptions down, test them one by one, change the approach. (Same reflex
  as code-guardian's two-failure Escalation — they fire together.)
- Sunk-cost test: knowing what you know now, would you still choose this
  path if you started fresh today? If no: the time spent is not a reason to
  continue.
- Am I fighting the framework? When every step feels hard, the approach is
  usually wrong — not the framework.

## §E — Completion (close like a senior)

- Self-review the diff as if a stranger wrote it and you have to approve it.
- Proof over assertion: VERIFIED with command output, never "should work".
- Explainability: summarize what was built and WHY in plain language — the
  developer must be able to defend every line in review.
- Journal the lesson: if this task taught you something about the project,
  one line into `.task-journal.md` / `.audit-log.md` so the next session
  knows it too.
