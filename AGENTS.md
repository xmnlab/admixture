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

## Documentation

Documentation lives in `docs/` and uses Quarto.

```bash
quarto render docs
quarto preview docs
```

Generated output goes to `docs/_site/` and should not be committed. Keep docs in
`.qmd` files unless there is a specific reason to add another format.

## Tests and checks

Unit tests must pass without Julia installed:

```bash
pytest -m "not integration"
```

Optional integration tests require Julia, OpenADMIXTURE.jl, and a real binary
PLINK prefix via `ADMIXTURE_TEST_PLINK_PREFIX`.

Common checks:

```bash
ruff check src tests
mypy src/admixture
poetry check --lock
```

## Implementation constraints

- Do not vendor OpenADMIXTURE.jl source code.
- Do not add GPL or closed-source ADMIXTURE as a dependency.
- Do not run network-installing Julia bootstrap code during import or tests.
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
from admixture import OpenAdmixtureRunner, OpenAdmixtureResult, run_openadmixture
```

Package-specific exceptions should inherit from `OpenAdmixtureError`.
