#!/usr/bin/env python3
"""Static checks for the plugin. Run from the repo root; CI runs it on every push.

Checks: the manifests parse and their versions match, every agent and skill has
`name` and `description` frontmatter (and the name matches its file or folder),
the hooks file parses and points at scripts that exist, and every Python file
compiles. Standard library only. Exits 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def fail(msg):
    errors.append(msg)


def load_json(rel):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 - report any parse/read failure
        fail(f"{rel}: {e}")
        return {}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if km:
            fields[km.group(1)] = km.group(2).strip().strip('"')
    return fields


plugin = load_json(".claude-plugin/plugin.json")
market = load_json(".claude-plugin/marketplace.json")
if plugin.get("name") != "sdlc-pipeline":
    fail("plugin.json: name must be sdlc-pipeline")
entries = [p for p in market.get("plugins", []) if p.get("name") == plugin.get("name")]
if not entries:
    fail("marketplace.json: no entry for the plugin")
elif entries[0].get("version") != plugin.get("version"):
    fail(f"version mismatch: plugin.json {plugin.get('version')} vs "
         f"marketplace.json {entries[0].get('version')}")
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
if f"[{plugin.get('version')}]" not in changelog:
    fail(f"CHANGELOG.md: no entry for {plugin.get('version')}")

for path in sorted((ROOT / "agents").glob("*.md")):
    fm = frontmatter(path)
    if not fm or not fm.get("name") or not fm.get("description"):
        fail(f"{path.relative_to(ROOT)}: needs name and description frontmatter")
    elif fm["name"] != path.stem:
        fail(f"{path.relative_to(ROOT)}: name '{fm['name']}' != file name")

for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
    fm = frontmatter(path)
    if not fm or not fm.get("name") or not fm.get("description"):
        fail(f"{path.relative_to(ROOT)}: needs name and description frontmatter")
    elif fm["name"] != path.parent.name:
        fail(f"{path.relative_to(ROOT)}: name '{fm['name']}' != folder name")

hooks = load_json("hooks/hooks.json")
for event, groups in (hooks.get("hooks") or {}).items():
    for group in groups:
        for h in group.get("hooks", []):
            for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"' ]+)", h.get("command", "")):
                if not (ROOT / ref).exists():
                    fail(f"hooks/hooks.json {event}: missing {ref}")

for path in sorted(ROOT.rglob("*.py")):
    if ".git" in path.parts:
        continue
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as e:
        fail(f"{path.relative_to(ROOT)}:{e.lineno}: {e.msg}")

if errors:
    print("\n".join(f"✗ {e}" for e in errors))
    sys.exit(1)
print(f"✓ plugin {plugin.get('name')} {plugin.get('version')} is valid")
