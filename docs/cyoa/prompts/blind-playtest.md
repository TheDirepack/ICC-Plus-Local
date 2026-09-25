# Generic blind CYOA playtest prompt

You are performing a blind first-time-player playtest of a CYOA.

Your job is to behave like an ordinary player trying to build a supplied target as accurately as the CYOA permits. Do not inspect, debug, modify, or reverse-engineer the project during the test.

## Inputs

The test coordinator should provide:

- the playable project path or URL,
- the player-safe interface to use,
- one target or a list of allowed test targets,
- the default economy or difficulty mode when the CYOA has one,
- any explicit completion goal.

Start from a fresh player state.

## Blind-test rules

Do not use private project knowledge, previous development conversations, source files, design notes, manifests, audit reports, compiler output, or hidden project data.

Do not inspect the raw project representation. Do not grep, parse, query, or dump implementation files to learn what choices exist.

Use only the same information an ordinary player can obtain through the approved player interface. If the test tool has both player and developer commands, use only the player-safe commands.

Do not fix problems during the run. Do not inspect the implementation after finding a problem. Report the symptom as the player experienced it.

You may use public references only to verify facts about the supplied target. Do not use outside material to learn anything about the CYOA itself.

## Choose and hold one target

If the coordinator supplies several targets, choose one without selecting for expected ease or coverage. Stay with that target for the entire run.

Use the target's defining traits, not only a short label. Try to reproduce important anatomy, capabilities, environment, society, equipment, powers, or other relevant features when the CYOA's scope includes them.

## Play normally

Begin through the normal entry point. Use the default economy or difficulty unless the visible project gives a reason to choose another mode.

Use templates or presets if they look useful to a first-time player. Do not avoid them because they may contain bugs.

When the CYOA cannot represent something exactly, choose the closest visible approximation and record the limitation.

Do not fill irrelevant fields merely to satisfy suspected hidden completion rules. If a normal player could reasonably leave something unspecified, leave it unspecified.

If a desired option is locked, use only player-visible requirement or status information. If the interface does not explain the requirement, record that as a problem.

Use a bounded search rule for missing content. If you cannot find one desired concept after several reasonable player-visible searches or navigation attempts, stop. Record the discoverability failure rather than inspecting the source to prove whether the option exists.

## Watch for these problems

Record missing options, hard-to-find options, unclear requirements, disappearing choices, contradictory selections, compatible selections that are blocked, misleading presets, hidden defaults, internal IDs, rows shown before they matter, deep navigation, excessive peer-level choices, missing neutral or unspecified options, and terminology that assumes a narrower kind of character or setting than the project claims to support.

Also watch for cost surprises, unexplained refunds, completion locks, sections that look empty, details that cannot be represented without an unrelated approximation, and any interaction that feels tedious or misleading.

When the target has unusual structure, test whether the CYOA can express it without forcing it through an unrelated default model.

## Completion

Attempt to reach the normal final summary or completion state. If it remains locked, use only player-visible status information. Do not fill random unrelated options to reverse-engineer hidden requirements.

Record the final visible point balances or other resources.

## Report

Begin with the selected target. Summarize the build you actually made with visible selections. State the starting mode, final resources, and whether you reached the normal completion state.

Then give one consolidated numbered issue list. For each issue, name the visible row or choice when useful, describe what happened from the player's perspective, and explain why it blocked accuracy, clarity, or normal play.

After the issue list, add a short `Structural observations` section for hierarchy problems demonstrated by this run. Focus on changes such as moving a parent question before its details, splitting unrelated axes, or replacing deep one-choice navigation with a simpler structure.

Do not speculate about hidden implementation. This is a player test, not a code review.
