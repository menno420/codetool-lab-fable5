"""``envdrift check`` — compare .env against .env.example.

With ``--fix``, missing keys are appended to the env file exactly as
``envdrift sync`` would (under a ``# added by envdrift sync`` comment,
example values verbatim as placeholders). Only the "missing" category is
fixable; "extra" and "empty" findings are reported but never auto-fixed.
Exit codes with ``--fix``: 0 if everything fixable was fixed and nothing
unfixable remains, 1 if unfixable drift (extra/empty) remains, 2 errors.
"""

from __future__ import annotations

from envdrift.commands import EXIT_FINDINGS, EXIT_OK, emit_json, load
from envdrift.commands.sync import append_missing, missing_entries


def run(args) -> int:
    env = load(args.env)
    example = load(args.example)

    env_map = env.as_dict()
    example_map = example.as_dict()

    missing = [k for k in example.ordered_keys() if k not in env_map]
    extra = [] if args.allow_extra else [k for k in env.ordered_keys() if k not in example_map]
    # Heuristic: a key that has a non-empty value in the example but an empty
    # value in the env is treated as "required but empty".
    empty = [
        k
        for k in example.ordered_keys()
        if k in env_map and env_map[k] == "" and example_map[k] != ""
    ]

    ok = not (missing or extra or empty)

    fixed: list[str] = []
    if args.fix and missing:
        entries = missing_entries(env_map, example)
        append_missing(args.env, entries)
        fixed = [entry.key for entry in entries]

    if args.format == "json":
        payload = {
            "command": "check",
            "env": args.env,
            "example": args.example,
            "ok": ok,
            "missing": missing,
            "extra": extra,
            "empty": empty,
        }
        if args.fix:
            payload["fixed"] = fixed
        emit_json(payload)
    else:
        if ok:
            print(f"ok: {args.env} matches {args.example}")
        else:
            for key in missing:
                print(f"missing: {key} (in {args.example} but not in {args.env})")
            for key in extra:
                print(f"extra: {key} (in {args.env} but not in {args.example})")
            for key in empty:
                print(f"empty: {key} (empty in {args.env} but non-empty in {args.example})")
            print(
                f"drift: {len(missing)} missing, {len(extra)} extra, {len(empty)} empty"
            )
            for key in fixed:
                print(f"fixed: added {key} to {args.env}")
            if args.fix:
                unfixable = len(extra) + len(empty)
                print(
                    f"fix: added {len(fixed)} key(s); "
                    f"{unfixable} unfixable finding(s) remain"
                )

    if args.fix:
        # Missing keys were fixed; only extra/empty drift remains unfixable.
        return EXIT_OK if not (extra or empty) else EXIT_FINDINGS
    return EXIT_OK if ok else EXIT_FINDINGS
