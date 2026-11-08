# Flow Tips for Bug Videos

Read this before writing or editing the flow a bug video records. Verified with Maestro 2.12.1 on iOS 26.4 simulators
and, where marked, on a Pixel 7 with Android 17 over USB. Other Android behaviour below is untested.

## Plain-language labels

Every Maestro command accepts `label:`, which replaces the command's technical description in the CLI output and in
`maestro record`. Label each step with what a user does or sees, in the order they would say it:

```yaml
- tapOn:
    label: "Tap the note to edit it"
    text: "Buy milk on the way home."
- assertVisible:
    label: "The keyboard opens"
    id: "shift"
```

Labels help the regression run too, so keep them in the committed flow, not only in the recording copy.

## Prove both sides of the claim

- Before the step that observes the bug, assert the precondition that makes it meaningful. "The keyboard closes" is
  only evidence after "The keyboard opens" passed; otherwise a run that never opened the keyboard would pass.
- Observe the bug with a check that fails on the bug build and passes on the fixed build. Run it on both builds before
  recording; a check that passes on both proves nothing.

## The recording variant

Only the copy you record for the bug side changes:

```yaml
- extendedWaitUntil:
    label: "Expected: the keyboard closes – it stays open"
    notVisible:
      id: "shift"
    timeout: 3000
    optional: true
```

`optional: true` turns the failure into a ⚠ warning, so the run reaches the end and the renderer finishes. Keep the
committed flow strict.

## Speed

Long waits make a video tedious and a regression run slow. Measure before optimising: each run writes per-command
durations to `commands.json` under the run's debug output directory.

- **Absence checks:** `assertNotVisible` polls until its default timeout before failing, about 17 s in Maestro 2.12.
  When the expected change is immediate, use `extendedWaitUntil` with `notVisible` and a short `timeout`.
- **Scrolling:** `scrollUntilVisible` defaults to speed 40. Use `speed: 100`, and add `centerElement: true` only when
  the target would otherwise sit under an overlay such as a docked panel.
- **Settling:** before each command Maestro waits for the screen to stop changing. Live content such as maps or
  spinners keeps it changing; `waitToSettleTimeoutMs` on `tapOn` and `swipe` caps that wait.
- **Pauses for viewers:** `waitForAnimationToEnd` steps slow the run without testing anything. The composed video's
  title card and held final frame give viewers time instead.

## Platform notes

- **iOS keyboard:** Maestro sees the software keyboard's keys; `id: "shift"` is visible exactly while it is up. A
  simulator with *I/O ▸ Keyboard ▸ Connect Hardware Keyboard* on never shows it, which fails the check for the wrong
  reason.
- **Taps in the video:** iOS simulators cannot draw Maestro's synthetic taps; the labelled step list in
  `maestro record --local` stands in for them. Android draws taps itself after
  `adb shell settings put system show_touches 1` (untested with `maestro record`).
- **Launch arguments on iOS:** a key that starts with `-`, such as `"-SomeDebugFlag": value`, reaches the app's
  `UserDefaults` argument domain unchanged.
- **Secrets typed by the flow:** pass them as `MAESTRO_*` environment variables, which Maestro reads without `-e`,
  so they stay out of the process list, and give the `inputText` a `label:`: without one, `maestro record` shows the
  resolved text in its step list (Android, verified). The label does not reach Maestro's logs, which can record the
  typed text, so keep `--debug-output` and `--test-output-dir` out of anything shared.
- **Airplane mode on Android:** `setAirplaneMode: enabled` switches it through a system command, so the video shows
  only the status bar icon (verified). When viewers need to see the switch, open Quick Settings with a swipe down from
  the top edge before the command and close it after (untested in a flow). Use USB: airplane mode drops `adb` over
  Wi-Fi (verified).
