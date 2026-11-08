---
name: maestro-bug-video
description: "Record a mobile app bug with Maestro and turn it into a video people can follow: one run that shows the bug, or the bug build beside the fixed build. Use when: presenting a reproduced bug to a team or reviewer, attaching evidence to a bug report or pull request, or showing that a fix works. Triggers: bug video, before and after video, record the repro, show the bug, show the fix, demo the fix, present the bug."
---

# Maestro Bug Video

Produce an MP4 that a person who has never seen the bug understands without help: a title card that names the bug,
each step in plain language, a caption that states the result, and a held final frame. The video is only evidence
when the run behind it proves the claim, so the Maestro result is part of the deliverable.

Two modes share one workflow:

| Mode      | Shows                                          | Needs                                          |
| --------- | ---------------------------------------------- | ---------------------------------------------- |
| `explain` | One run of the bug build                       | A flow that reproduces the bug                 |
| `compare` | The bug build and the fixed build side by side | The same flow, plus a build containing the fix |

## Preconditions

- A Maestro flow that reproduces the bug: it fails on the bug build at the step that observes the bug, and passes on the
  fixed build. If no such flow exists, write it first; a video of a run that does not observe the bug proves nothing.
- `maestro` on PATH (a project-pinned one through `mise exec --` when the project pins it), `ffmpeg` and `ffprobe`
  with the `drawtext` filter. On Android, also `adb` and Python 3.10 or newer.
- Devices or simulators that can run the bug build and, for `compare`, the fixed build.

## Workflow

1. **Make the flow readable.** Give every command a plain-language `label:` that says what the user does or sees.
   Read [`references/flow-tips.md`](references/flow-tips.md) before editing the flow; it covers labels, the
   recording variant, and speed.
2. **Prepare the recording variant of the bug run.** Copy the flow, mark the step that observes the bug
   `optional: true`, and relabel it as `Expected: <correct behaviour> – <what happens instead>`. A failing step would
   end the run before the renderer finishes; the optional step still shows ⚠ in the video and in the log.
3. **Install the builds.** Build the bug state from the commit before the fix, not by hand-reverting files, unless the
   fix is a single line you restore immediately. A `git worktree` at the base commit with its own build output keeps
   the two builds apart. Put each build on its own device or reinstall between recordings.
4. **Record one run at a time.** On an iOS simulator, use Maestro's renderer:

   ```bash
   maestro --device <bug-device> record --local <bug-variant.yaml> before.mp4
   maestro --device <fix-device> record --local <flow.yaml> after.mp4
   ```

   Always pass `--local`: without it Maestro uploads the recording to its cloud for rendering.

   On an Android device or emulator, use [`scripts/record-maestro-run`](scripts/record-maestro-run) instead.
   `maestro record` cuts the end of an Android run: `screenrecord` writes frames only when the screen changes, and
   the renderer stops at the last frame, before the run's final screen. The script records the screen itself, runs
   `maestro test`, holds the last frame until the run really ended, and draws the steps from Maestro's
   `commands.json`:

   ```bash
   record-maestro-run --device <bug-device> --flow <bug-variant.yaml> --out before.mp4
   record-maestro-run --device <fix-device> --flow <flow.yaml> --out after.mp4 --maestro "mise exec -- maestro"
   ```

   It exits with Maestro's exit code. Recording has no time limit where the device's `screenrecord` allows it, as on
   Android 17; older versions stop recording after 180 seconds.

   A flow that types a secret, such as a test account's password from `${MAESTRO_PASSWORD}`, needs a `label:` on that
   `inputText`: `maestro record` prints the resolved text in its step list, so an unlabelled step shows the secret in
   the video. `record-maestro-run` never shows resolved values, and it keeps Maestro's logs, which record typed text,
   in a temporary directory that it deletes.

   Run recordings sequentially; two Maestro processes started separately compete for the same driver port and both
   runs break. Before starting, check that no earlier run is still alive (`pgrep -fl maestro`) and stop leftovers you
   started.
5. **Confirm the runs prove the claim.** The bug recording must show every setup step passed and the bug step warned
   (✅ and ⚠ from Maestro's renderer; green and amber markers from `record-maestro-run`) with the bug visible on
   screen; the fixed recording must show every step passed. If either differs, the video would mislead: stop and fix
   the flow or the build.
6. **Compose the video** with [`scripts/compose-bug-video`](scripts/compose-bug-video):

   ```bash
   compose-bug-video explain --video before.mp4 \
     --title "<App> · <Screen>" --subtitle "Bug: <one sentence a user would say>" \
     --steps "<the steps in one line>" --caption "<what the viewer should notice>" --out bug.mp4

   compose-bug-video compare --before before.mp4 --after after.mp4 \
     --title "<App> · <Screen>" --subtitle "Bug: <one sentence>" \
     --steps "Same steps on both sides: <steps>" \
     --caption "Left: <what goes wrong>.   Right: <what the fix does>." --out before-after.mp4
   ```

   Write the title card and caption for someone outside the team: name the screen and the visible symptom, not the
   code. Banner labels default to "BEFORE · current app" and "AFTER · with the fix" (`--before-label`,
   `--after-label`); `--hold` sets the final-frame pause.
7. **Check the result before handing it over.** Extract the title frame and the last frame
   (`ffmpeg -ss 1 -i out.mp4 -frames:v 1 title.png`, `ffmpeg -sseof -1 -i out.mp4 -frames:v 1 end.png`) and look at
   them: the text must be complete and legible, and the last frame must show the bug, or the bug beside the fix.

## Completion

Report the video path, its length, which builds or commits each side shows, and the Maestro result for each run. The
output stays local; publishing or attaching it is the user's decision.
