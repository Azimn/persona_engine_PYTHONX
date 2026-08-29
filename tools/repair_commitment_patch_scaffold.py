#!/usr/bin/env python3
"""Repair a quoting collision in the one-time commitment integration scaffold."""

from pathlib import Path

path = Path(__file__).with_name("apply_minimal_commitment_constraint.py")
text = path.read_text(encoding="utf-8")
old_start = "    return f'''# Minimal Commitment Constraint Probe\n"
new_start = '    return f"""# Minimal Commitment Constraint Probe\n'
old_end = "renderer speech retain no direct write authority.\n'''\n\n\ndef main() -> None:\n"
new_end = 'renderer speech retain no direct write authority.\n"""\n\n\ndef main() -> None:\n'
if old_start not in text or old_end not in text:
    raise RuntimeError("expected quoting anchors not found")
text = text.replace(old_start, new_start, 1).replace(old_end, new_end, 1)
path.write_text(text, encoding="utf-8")
print("Repaired commitment integration scaffold quoting")
