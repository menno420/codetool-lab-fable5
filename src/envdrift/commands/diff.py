"""``envdrift diff`` — key-level diff between two env files."""

from __future__ import annotations

from envdrift.commands import EXIT_FINDINGS, EXIT_OK, emit_json, load


def run(args) -> int:
    file_a = load(args.a)
    file_b = load(args.b)
    map_a = file_a.as_dict()
    map_b = file_b.as_dict()

    added = [k for k in file_b.ordered_keys() if k not in map_a]
    removed = [k for k in file_a.ordered_keys() if k not in map_b]
    changed = [k for k in file_a.ordered_keys() if k in map_b and map_a[k] != map_b[k]]

    ok = not (added or removed or changed)

    if args.format == "json":
        payload = {
            "command": "diff",
            "a": args.a,
            "b": args.b,
            "ok": ok,
            "added": [_entry(k, value=map_b[k] if args.values else None) for k in added],
            "removed": [_entry(k, value=map_a[k] if args.values else None) for k in removed],
            "changed": [
                _entry(k, old=map_a[k], new=map_b[k]) if args.values else _entry(k)
                for k in changed
            ],
        }
        emit_json(payload)
    else:
        if ok:
            print(f"identical: {args.a} and {args.b} define the same keys and values")
        else:
            for key in added:
                print("+ {}{}".format(key, "=" + map_b[key] if args.values else ""))
            for key in removed:
                print("- {}{}".format(key, "=" + map_a[key] if args.values else ""))
            for key in changed:
                if args.values:
                    print(f"~ {key}: {map_a[key]!r} -> {map_b[key]!r}")
                else:
                    print(f"~ {key}: <changed>")
    return EXIT_OK if ok else EXIT_FINDINGS


def _entry(key, value=None, old=None, new=None):
    out = {"key": key}
    if value is not None:
        out["value"] = value
    if old is not None or new is not None:
        out["old"] = old
        out["new"] = new
    return out
