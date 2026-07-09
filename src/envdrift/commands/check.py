"""``envdrift check`` — compare .env against .env.example."""

from __future__ import annotations

from envdrift.commands import EXIT_FINDINGS, EXIT_OK, emit_json, load


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

    if args.format == "json":
        emit_json(
            {
                "command": "check",
                "env": args.env,
                "example": args.example,
                "ok": ok,
                "missing": missing,
                "extra": extra,
                "empty": empty,
            }
        )
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
    return EXIT_OK if ok else EXIT_FINDINGS
