---
last_validated: 2026-11-08T19:02:44Z
project_type: agent-skill
---

# Agent Instructions: bug-video-skill

## Repository Overview

`bug-video-skill` publishes the `maestro-bug-video` Agent Skill as a Claude plugin. The skill records a reproduced
mobile app bug with Maestro and composes a video people can follow, of one run or of the bug build beside the fixed
build. The repository is public under the MIT license and derives from the organization's `template-agent-skill`.

## Ownership

- `apm.yml` is the source of the plugin manifest: `apm pack --force` generates `.claude-plugin/plugin.json`, and
  `mise run test:plugin-manifest` fails when the committed manifest drifts from that output.
- `skills/maestro-bug-video/SKILL.md` is the authoritative skill. The plugin name, skill directory, and frontmatter
  name are `maestro-bug-video`; the repository name differs on purpose and is not part of the plugin identity.
- `skills/maestro-bug-video/scripts/compose-bug-video` (bash) composes the final video with ffmpeg.
  `skills/maestro-bug-video/scripts/record-maestro-run` (Python 3.10+, no extension so it runs by name) records an
  Android run. Ruff covers it through `extend-include` in `pyproject.toml`; `lint:shell` runs shellcheck on the bash
  script.
- The development profile pins the private `skillctl` release for `mise run lint:development`. CI uses only the public
  base toolchain, so outside contributors run the checks with `MISE_ENV=ci`.
- `pyproject.toml` and `uv.lock` own Python dependencies; `UV_NO_MANAGED_PYTHON=1` forces uv onto Mise's Python.
- Changie owns `CHANGELOG.md`: add entries under `.changes/unreleased/`, batch them into `.changes/<version>.md`, and
  merge.
- OpenTofu in `pretty-good-software-org/org-github-infrastructure` owns repository settings and rulesets.

## Repository Structure

```text
.
├── .actionlint.yml
├── .changes
│   ├── 1.0.0.md
│   ├── 1.1.0.md
│   ├── header.tpl.md
│   └── unreleased
│       └── .gitkeep
├── .changie.yaml
├── .claude-plugin
│   └── plugin.json
├── .coderabbit.yaml
├── .github
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows
│       ├── lint.yml
│       └── test.yml
├── .gitignore
├── .mise.ci.toml
├── .mise.development.toml
├── .mise.toml
├── .miserc.toml
├── .rumdl.toml
├── .yamllint.yml
├── AGENTS.md
├── CHANGELOG.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── apm.yml
├── cog.toml
├── lefthook
│   ├── commit-msg.yml
│   ├── files.yml
│   ├── lint.yml
│   ├── python.yml
│   └── secrets.yml
├── lefthook.yml
├── mise-tasks
│   ├── check
│   │   └── markdown-format
│   ├── format
│   │   └── markdown
│   ├── lint
│   │   ├── actionlint
│   │   ├── audit
│   │   ├── default
│   │   ├── development
│   │   ├── python
│   │   ├── rumdl
│   │   ├── shell
│   │   ├── skill
│   │   └── yamllint
│   ├── setup
│   │   └── default
│   └── test
│       ├── default
│       ├── plugin-manifest
│       └── python-runtime
├── mise.development.lock
├── mise.lock
├── pyproject.toml
├── skills
│   └── maestro-bug-video
│       ├── SKILL.md
│       ├── references
│       └── scripts
├── tests
│   ├── test_compose_bug_video.py
│   ├── test_record_maestro_run.py
│   └── test_template_contract.py
└── uv.lock
```

## Commands

```bash
mise run setup:default
mise run lint:default
mise run test:default
mise run lint:development
```

Use the fastest loop that exercises the change: a focused pytest test first, then the complete lint and test tasks.

## Development Guidelines

This repository is public.

- Keep product names, customer data, test accounts, hostnames, session links, and local paths out of files and commit
  messages. Examples use neutral apps and text.
- CI runs on GitHub-hosted runners: the organization's self-hosted runner groups refuse public repositories, and fork
  pull requests must not reach organization hosts.

## Testing

Tests cover what the scripts decide on their own: the step text `record-maestro-run` draws, which must never be an
evaluated value, its step timing and `commands.json` discovery, and every input `compose-bug-video`
rejects, with stub `ffmpeg` and `ffprobe` on an isolated `PATH`. Device recording and ffmpeg encoding are verified by
hand on real devices; record the device and Maestro version in the pull request.

## Git Workflow

Check status first, work on feature branches, use Conventional Commits, and open a pull request; run
`mise run lint:default` and `mise run test:default` before opening it. To release, bump `version` in `apm.yml`, run
`apm pack --force`, batch the changie entries for that version, and merge to `main` through a pull request. Tag the
merged commit `v<version>` with an annotated tag and publish a GitHub release; the `pretty-good-skills` marketplace pins
the tagged commit's full SHA.
