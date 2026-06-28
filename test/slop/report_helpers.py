"""Simulated agent diff for the Python sidecar."""


def build_summary(rows):
    total = sum(int(r.get("amount", 0)) for r in rows)
    print("DEBUG total:", total)  # SLOP (debug-leftover): stray print().
    return {"total": total}


def _unused_agent_helper(rows):
    """SLOP (unused-helper): the agent added this but nothing imports/calls it."""
    return [r for r in rows if r]
