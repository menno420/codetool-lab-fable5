"""``envdrift check`` — compare .env against .env.example."""

from __future__ import annotations

from envdrift.commands import EXIT_FINDINGS, EXIT_OK, emit_json, load


def run(args) -> int:
    env = load(args.env)
    example = load(args.example)

    env_map = env.as_dict()
    example_map = example.as_dict()

    missing = [k for k in example.keys() if k not in env_map]
    extra = [] if args.allow_extra else [k for k in env.keys() if k not in example_map]
    # Heuristic: a key that has a non-empty value in the example but an empty
    # value in the env is treated as "required but empty".
    empty = [
        k
        for k in example.keys()
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
            print("ok: %s matches %s" % (args.env, args.example))
        else:
            for key in missing:
                print("missing: %s (in %s but not in %s)" % (key, args.example, args.env))
            for key in extra:
                print("extra: %s (in %s but not in %s)" % (key, args.env, args.example))
            for key in empty:
                print("empty: %s (empty in %s but non-empty in %s)" % (key, args.env, args.example))
            print(
                "drift: %d missing, %d extra, %d empty" % (len(missing), len(extra), len(empty))
            )
    return EXIT_OK if ok else EXIT_FINDINGS
