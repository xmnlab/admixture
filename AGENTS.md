# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project purpose

`admixture` is a Python wrapper around the upstream Julia package
[OpenADMIXTURE.jl](https://github.com/OpenMendel/OpenADMIXTURE.jl). It must not
claim to be the OpenADMIXTURE implementation and must not reimplement the
algorithm in Python.

The wrapper is responsible for:

- validating binary PLINK `.bed` / `.bim` / `.fam` prefixes;
- finding and checking Julia;
- invoking OpenADMIXTURE.jl through a subprocess with `shell=False`;
- parsing `.Q`, `.P`, and `.log` outputs;
- returning Python objects such as `pandas.DataFrame` and dataclasses.

## Environment

The conda environment name is `admixture`.

```bash
conda activate admixture
poetry install --with dev
```

This project intentionally uses conda and Poetry together. Conda supplies the
base development environment and external tools such as Quarto. Poetry manages
Python packaging and Python dependencies.

## Dependency management

Keep production dependencies in `[tool.poetry.dependencies]`. Keep development
dependencies in `[tool.poetry.group.dev.dependencies]`, mirroring them in
`[project.optional-dependencies].dev` so `pip install -e ".[dev]"` continues to
work. Do not remove or rewrite dependency entries unless the task explicitly
requires it. When dependencies change, update `poetry.lock` and run
`poetry check --lock`.

## Documentation

Documentation lives in `docs/` and uses Quarto.

```bash
makim docs.build
makim docs.preview
```

Generated output goes to `docs/_site/` and should not be committed. Keep docs in
`.qmd` files unless there is a specific reason to add another format.

## Docstrings

Python docstrings use Douki YAML format, with at least a `title` field. Do not
add NumPy, Google, or plain-text docstrings. Run Douki after editing Python
docstrings:

```bash
douki sync src tests
```

Ruff should not be used for pydocstyle checks in this project; Douki is the
docstring source of truth.

## Tests and checks

Run tests with:

```bash
makim tests.unit
```

OpenADMIXTURE runtime tests require Julia and OpenADMIXTURE.jl. They should
fail, not skip, when the Julia runtime or OpenADMIXTURE.jl is unavailable.

Tests may use `malariagen-data` as a development-only dependency. Do not import
`malariagen_data` from `src/`; keep it test-only to avoid a future circular
dependency if `malariagen-data` depends on `admixture`. Tests that import
`malariagen_data` must skip on Python 3.13+.

Common checks:

```bash
makim lint.all
makim package.build
```

## Implementation constraints

- Do not vendor OpenADMIXTURE.jl source code.
- Do not add GPL or closed-source ADMIXTURE as a dependency.
- Do not run network-installing Julia bootstrap code during import,
  post-install, or tests. Use explicit `admixture.setup(project_dir=...)` for
  opt-in Julia project setup, or the installed `admixture-setup` command.
- Use `pathlib.Path` for paths.
- Use `subprocess.run([...], shell=False, capture_output=True, text=True)`.
- Never build shell command strings for Julia execution.
- Keep paths with spaces working on Linux, macOS, and Windows.
- Keep pure Python parsing and validation code testable without Julia.

## Upstream Julia API

The bridge script should call the verified upstream API:

```julia
OpenADMIXTURE.run_admixture(filename, K; ...)
```

If upstream OpenADMIXTURE.jl changes its API or installation instructions,
verify against upstream source/docs before changing the bridge or docs.

## Public Python API

Maintain the top-level exports:

```python
from admixture import OpenAdmixtureRunner, OpenAdmixtureResult, run_openadmixture, setup
```

Package-specific exceptions should inherit from `OpenAdmixtureError`.
