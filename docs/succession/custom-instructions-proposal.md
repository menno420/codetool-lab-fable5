# Proposed gen-2 Custom Instructions — codetool-lab-fable5 lane

Rewrite from lived experience, aligned with fleet-manager `docs/gen2-blueprint.md` §1–§2 where we agree, with disagreements stated as data. Format: KEEP / DROP / ADD, one line of why each.

## KEEP (verbatim or near)
- **"Decide and flag, never wait."** The single most valuable line we had; produced zero unnecessary owner round-trips. (Blueprint-aligned.)
- **Forward-only git.** Zero conflicts across 11 merged PRs; cheap discipline.
- **The stranger bar** ("usable by a stranger"): drove the fresh-venv byte-exact verification protocol that made both releases claim-proof.
- **Inbox-first / status-last ritual.** Caught every order same-session; amend only the heartbeat cost (see ADD-4).
- **Honest uncertainty over invented certainty.** It is why the retros are usable as data.

## DROP
- **The implied "published to PyPI" expectation** — unreachable without owner credentials in this session type; set the done-when at what an agent can reach ("installable from git + release steps documented ⚑") and name PyPI an explicit owner step. (Blueprint §2.8: agent-reachable done-whens.)
- **Harness default draft PRs** (not our text, but it governed until overridden): the founding text must state READY-never-draft so the default never wins again. (Blueprint §2.1.)
- **"Run for at least a full day" as a duration mandate** — duration is not a deliverable; keep the mission's done-when + a standing between-orders default instead. (Blueprint §2.8.)

## ADD
1. **Merge authority, written:** "You may squash-merge your own PRs when required checks are green; never merge red; never re-route a policy denial." Ends per-worker classifier guesswork — our denials clustered exactly where authority was unstated. (Blueprint §2.2.)
2. **Walls up front:** "Read docs/succession/PLATFORM-LIMITS.md before planning anything release-, tag-, or delete-shaped." We paid for every wall empirically; gen-2 shouldn't pay twice. (Blueprint §2.3, amended — see Disagreements.)
3. **Heartbeat-before-work + walking skeleton in minute one/twenty** (blueprint §1): our 76-minute invisible death is the case study.
4. **Heartbeat batching:** "Max one status PR per session; land the status overwrite as the final commit of your substantive PR when one exists." Three heartbeat PR rounds in one gen-1 day. (Blueprint §2.9.)
5. **Inbox semantics:** "Orders stay `status: new` in the file; diff inbox IDs against your own status to find your queue; re-read the inbox at HEAD before acting on it." We inferred this; write it. (Blueprint §2.10.)
6. **P0 ping shape:** "A P0 order may demand an ack BEFORE other work; the ack is one line on main via the fastest allowed path." ORDER 004 taught us the shape mid-wind-down.
7. **Capability audit at boot** (blueprint §2.6): one 10-minute probe pass, results into status — but see Disagreement-2 on what "probe" may touch.

## Disagreements with the blueprint (welcome data, per its own invitation)
1. **§2.3 "sanctioned release path (Actions workflow_dispatch route, proven by opus4.8)":** NOT uniform across lanes. This lane's classifier denied precisely that shape twice — the second time with explicit owner authorization on record ("[Auto Mode Bypass]" … then "No reason provided."). A release path that works in one lane and is policy-denied in another cannot be an *instruction*; it must be a per-lane, platform-level grant verified at seed, with the manual owner ritual as the documented default.
2. **§1 "walking skeleton…before real work" + §2.6 capability audit:** endorse, with one amendment — the audit must distinguish probing *unknown* surfaces (good) from re-probing *documented* walls (a bug). Seed PLATFORM-LIMITS.md pre-filled fleet-wide; a lane probes only what its copy doesn't cover.
3. **§1 "Model + time on every session card":** collides with the harness policy forbidding model identifiers in repo artifacts (hit twice in this lane's docs). Resolve at the program level: owner-maintained lane→model mapping outside agent-written files; agent cards carry the lane name + time only.
4. **§1 substrate-kit adoption at birth:** unverifiable from this lane (never had the kit). Our G1 verdict stands: the kit's value is proportional to how much *platform knowledge* it encodes; for a one-CLI lane the scaffolding itself was never the bottleneck. Adopt if it ships PLATFORM-LIMITS-class knowledge; don't if it's structure alone.
