---
description: Place a Stipech Motion package on the open DaVinci Resolve timeline (one clip per graphic on V3, one Text+ clip per subtitle on V4, go up on conflicts)
argument-hint: [package folder] [--replace] [--no-subtitles]
---
Use the **motion-designer** skill's Resolve guide (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/references/resolve.md`) for: $ARGUMENTS

If this session can run commands on the editing PC: confirm the right timeline is open and SM Carrier is in this project's Media Pool, prefer `--new-timeline` so the editor's timeline stays as it is, run `place.py --dry-run` and summarise the plan (tracks, overflow), then place, read `placement-report.json`, and check the first graphic against its HTML still (Calibration). New media goes in its own bin, Motion Graphics/<project>. When a new version replaces older timelines, offer `--archive-older`, which moves them to Older Versions. Never touch the editor's clips; `--replace` only affects SM tracks, and only when the user asks for it. If not connected, give the user the package path and the README steps.
