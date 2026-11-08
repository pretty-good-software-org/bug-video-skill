# bug-video-skill

An [Agent Skill](https://agentskills.io/specification), `maestro-bug-video`, that records a mobile app bug with
[Maestro](https://maestro.dev/) and turns the recording into a video a person can follow without help: a title card
that names the bug, each step in plain language, a caption that states the result, and a held final frame.

It has two modes:

| Mode      | Shows                                          | Needs                                          |
| --------- | ---------------------------------------------- | ---------------------------------------------- |
| `explain` | One run of the bug build                       | A flow that reproduces the bug                 |
| `compare` | The bug build and the fixed build side by side | The same flow, plus a build containing the fix |

The skill checks that each run proves the claim before it composes the video: the bug run warns at the step that
observes the bug, and the fixed run passes every step. Recordings stay local; `maestro record` always runs with
`--local`, so nothing is uploaded to Maestro's cloud.

## Requirements

- A Maestro flow that fails on the bug build at the step that observes the bug and passes on the fixed build.
- [`maestro`](https://docs.maestro.dev/getting-started/installing-maestro), with an iOS simulator or an Android device
  or emulator for each build.
- `ffmpeg` and `ffprobe` built with the `drawtext` filter (libfreetype).
- Fonts: Arial on macOS, or DejaVu Sans on Linux. `compose-bug-video` also accepts `--font` and `--font-bold`.
- For Android recordings: `adb` and Python 3.10 or newer.

Tested with Maestro 2.12.1 on iOS 26.4 simulators and on a Pixel 7 with Android 17.

## Installation

With [APM](https://github.com/microsoft/apm), pinned to a release:

```bash
apm install pretty-good-software-org/bug-video-skill#v1.1.1
```

Without APM, copy the skill directory into your agent's skills directory, for example for Claude Code:

```bash
git clone --depth 1 --branch v1.1.1 https://github.com/pretty-good-software-org/bug-video-skill.git
cp -R bug-video-skill/skills/maestro-bug-video ~/.claude/skills/
```

## Usage

Ask the agent for a bug video, for example "record the repro and make a before and after video". The skill's
[`SKILL.md`](skills/maestro-bug-video/SKILL.md) holds the workflow, and
[`references/flow-tips.md`](skills/maestro-bug-video/references/flow-tips.md) covers writing a flow that records well.
The two scripts also run on their own:

- [`compose-bug-video`](skills/maestro-bug-video/scripts/compose-bug-video) `explain|compare` composes the final
  video from one or two recordings.
- [`record-maestro-run`](skills/maestro-bug-video/scripts/record-maestro-run) records an Android run with its final
  screen and draws each step beside it. `maestro record` cuts the end of Android runs.

## Development

Development uses [mise](https://mise.jdx.dev/), which installs the pinned tools from the lock files:

```bash
mise run setup:default
mise run lint:default
mise run test:default
```

`setup:default` also installs the Git hooks. Changes are recorded with [Changie](https://changie.dev/) in `.changes/`
and merged into [`CHANGELOG.md`](CHANGELOG.md).

## License

[MIT](LICENSE)
