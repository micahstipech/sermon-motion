---
description: Turn this video's feedback into lasting rules, record it in the variation ledger, and sync the house folder
argument-hint: [notes from the user, optional]
---
Use the **motion-designer** skill's learning guide (`${CLAUDE_PLUGIN_ROOT}/skills/motion-designer/references/learning.md`). Notes: $ARGUMENTS

Go through this session's feedback (and the notes above). Write pref/obs/ver/cal lines to `house/rules.md`, fixing any rule they contradict. Run `mg.py ledger add motion/storyboard.json` if the user approved the result. Update the series kit if the look changed. If a rule could be enforced by lint, the ledger or the chunker, propose that change instead. Then offer to commit and push the house folder (and any skill improvements) so the other machine gets them.
