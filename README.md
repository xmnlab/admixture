# admixture

A Python wrapper around
[OpenADMIXTURE.jl](https://github.com/OpenMendel/OpenADMIXTURE.jl) from the
[OpenMendel](https://openmendel.github.io/) project.

> This package is **not** the original OpenADMIXTURE implementation and does
> **not** reimplement the algorithm. It validates inputs, launches Julia, runs
> OpenADMIXTURE.jl, and parses the resulting files into Python objects.

OpenADMIXTURE.jl is a separate upstream Julia package for maximum-likelihood
ancestry estimation on binary PLINK 1 BED datasets. Users install
OpenADMIXTURE.jl separately in their Julia environment; this Python package does
not vendor or relicense OpenADMIXTURE.jl.

## Why this package exists

Many genomics workflows are Python-based, while OpenADMIXTURE.jl provides the
core ancestry-inference implementation in Julia. This package provides a small
Python layer for:

- validating a PLINK `.bed`/`.bim`/`.fam` prefix;
- building a cross-platform Julia subprocess command without `shell=True`;
- capturing stdout/stderr and surfacing helpful errors;
- parsing `.Q` ancestry proportions and `.P` allele frequencies into
  `pandas.DataFrame` objects.

## Installation for development

This repository uses **conda and Poetry together**. Conda provides the base
Python environment and common compiled packages; Poetry installs the project.

```bash
conda env create -f conda.yaml
conda activate admixture
poetry config virtualenvs.create false
poetry install --with dev
```

For a pip-style editable install inside the activated conda environment:

```bash
pip install -e ".[dev]"
```

## Documentation

Documentation lives in `docs/` and uses Quarto. The conda environment includes
the Quarto CLI.

Render the site with Makim:

```bash
makim docs.build
```

Preview while editing with:

```bash
makim docs.preview
```

Direct Quarto commands also work when your temp/cache directories are writable:

```bash
quarto render docs
quarto preview docs
```

Generated documentation output is written to `docs/_site/` and is ignored by
Git.

## Julia and OpenADMIXTURE.jl setup

Julia is an external runtime, not a Python dependency.

Install Julia from <https://julialang.org/downloads/> and check it is available:

```bash
julia --version
```

The upstream OpenADMIXTURE.jl documentation installs from GitHub URLs:

```bash
julia -e 'using Pkg; Pkg.add(url="https://github.com/kose-y/SparseKmeansFeatureRanking.jl"); Pkg.add(url="https://github.com/OpenMendel/OpenADMIXTURE.jl")'
```

For a project-local Julia environment:

```bash
mkdir julia_env
julia --project=julia_env -e 'using Pkg; Pkg.add(url="https://github.com/kose-y/SparseKmeansFeatureRanking.jl"); Pkg.add(url="https://github.com/OpenMendel/OpenADMIXTURE.jl")'
```

Then pass the project directory from Python:

```python
from admixture import OpenAdmixtureRunner

runner = OpenAdmixtureRunner(project_dir="julia_env")
```

You may also opt in to Python-triggered Julia project bootstrapping:

```python
runner = OpenAdmixtureRunner(
    project_dir="julia_env",
    install_if_missing=True,
)
```

`install_if_missing=True` requires `project_dir` so the global Julia environment
is not modified unexpectedly.

## Basic usage

```python
from admixture import OpenAdmixtureRunner

runner = OpenAdmixtureRunner(
    julia="julia",
    project_dir=None,
    install_if_missing=False,
)

result = runner.run(
    bfile="data/example",
    k=3,
    out_prefix="results/example_k3",
    seed=42,
    threads=4,
)

print(result.q)          # ancestry proportions, individuals x K
print(result.p)          # allele frequencies, if produced
print(result.metadata)   # paths and runtime metadata
```

Convenience function:

```python
from admixture import run_openadmixture

result = run_openadmixture(
    bfile="data/example",
    k=3,
    out_prefix="results/example_k3",
    seed=42,
    threads=4,
)
```

## Input format

Pass a binary PLINK prefix. For these files:

```text
data/example.bed
data/example.bim
data/example.fam
```

use:

```python
bfile="data/example"
```

Passing `data/example.bed` is normalized to the same prefix when safe.

## Output

The wrapper writes and discovers common ADMIXTURE-style outputs:

```text
<out_prefix>.Q
<out_prefix>.P
<out_prefix>.log
```

The returned `OpenAdmixtureResult` contains:

- `result.q`: ancestry proportions as a `pandas.DataFrame`;
- `result.p`: allele-frequency matrix as a `pandas.DataFrame`, or `None`;
- `result.q_path`, `result.p_path`, `result.log_path`;
- `result.stdout` and `result.stderr` from Julia;
- `result.metadata` with runtime and input-file metadata.

## Platform support

The wrapper is designed for Linux, macOS, and Windows. It uses `pathlib`,
`shutil.which`, and `subprocess.run(..., shell=False)` so paths with spaces are
passed safely as single arguments.

## Windows notes

PowerShell example:

```powershell
conda env create -f conda.yaml
conda activate admixture
poetry config virtualenvs.create false
poetry install --with dev
julia --version
```

If Julia is not on `PATH`, pass the executable explicitly:

```python
runner = OpenAdmixtureRunner(
    julia=r"C:\Users\you\AppData\Local\Programs\Julia-1.11.0\bin\julia.exe"
)
```

Paths with spaces are passed as separate subprocess arguments, not through a
shell command string.

## Troubleshooting

### Julia not found

Install Julia from <https://julialang.org/downloads/> or pass the executable
path to `OpenAdmixtureRunner(julia=...)`.

### OpenADMIXTURE.jl not installed

Install the upstream Julia package in the selected Julia environment, or create
a project-local environment and pass `project_dir=...`.

### Missing PLINK files

Ensure the `.bed`, `.bim`, and `.fam` files all exist and are non-empty. Pass
the shared prefix, not a directory.

### Output files not found

Check `result.stdout`/`result.stderr` or the raised exception. Remove stale
outputs if multiple candidate `.Q` files match the same output prefix.

### OpenADMIXTURE test skipped

The runtime test requires all of:

- Julia on `PATH`;
- OpenADMIXTURE.jl installed;
- `ADMIXTURE_TEST_PLINK_PREFIX` set to a real PLINK prefix.

The malariagen-data runtime test is development-only. It skips on Python 3.13+
and imports `malariagen_data` inside the test only, so the package does not gain
a production dependency on malariagen-data.

Run tests with:

```bash
makim tests.unit
```

## Citation and attribution

If this wrapper helps your work, cite the upstream OpenADMIXTURE.jl project and
paper:

- OpenADMIXTURE.jl: <https://github.com/OpenMendel/OpenADMIXTURE.jl>
- OpenMendel: <https://openmendel.github.io/>
- OpenADMIXTURE paper: <https://pmc.ncbi.nlm.nih.gov/articles/PMC9943729/>

## Roadmap

Version 0 focuses on one task: run OpenADMIXTURE.jl on an existing binary PLINK
prefix and parse the result. Future work may add multi-K runs, multiple seeds,
plotting helpers, and tighter integration with other genomics tools.
