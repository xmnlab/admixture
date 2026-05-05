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

## Installation from PyPI

```bash
pip install admixture
admixture setup
```

The wheel includes a Julia project under the Python package at
`admixture/julia-env`. `admixture setup` runs `Pkg.instantiate()` for that
packaged project.

## Installation for development

This repository uses **conda and Poetry together**. Conda provides the base
Python environment and common compiled packages; Poetry installs the project.
`juliaup` is included in the conda environment. Use it to install/select a Julia
runtime inside `makim setup.install`.

```bash
conda env create -f conda/dev-linux.yaml
conda activate admixture
poetry config virtualenvs.create false
makim setup.install
```

Use the environment file for your operating system:

- Linux: `conda/dev-linux.yaml`
- macOS: `conda/dev-macos.yaml`
- Windows: `conda/dev-win.yaml`

`makim setup.install` runs `poetry install --with dev` and then instantiates the
packaged Julia project.

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

Julia is an external runtime, not a Python dependency. The development conda
environments include `juliaup`, a cross-platform Julia installer and version
manager from conda-forge:

```bash
juliaup add release
juliaup default release
julia --version
```

The conda environment files in this repository include `juliaup` instead of the
old `julia` conda package because `juliaup` is available on Linux, macOS, and
Windows. If you are not using the provided conda environment files, install it
with `conda install -c conda-forge juliaup` first.

For non-conda installs, the official Julia installer from
<https://julialang.org/downloads/> is also supported as long as `julia` is on
`PATH`.

The Python package ships a Julia project with `Project.toml` and
`Manifest.toml`. Instantiate it with:

```bash
admixture setup
```

From Poetry, run `poetry run admixture setup`.

Or bootstrap from Python:

```python
import admixture

project_dir = admixture.setup()
```

`admixture.setup()` and `admixture setup` never modify the global Julia
environment. `OpenAdmixtureRunner()` always uses the packaged Julia project.
`OpenAdmixtureRunner(install_if_missing=True)` is also available for explicit
opt-in instantiation during a run.

## Basic usage

```python
from admixture import OpenAdmixtureRunner

runner = OpenAdmixtureRunner(
    julia="julia",
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
conda env create -f conda/dev-win.yaml
conda activate admixture
juliaup add release
juliaup default release
julia --version
poetry config virtualenvs.create false
poetry install --with dev
```

If Julia is not on `PATH`, pass the executable explicitly:

```python
runner = OpenAdmixtureRunner(
    julia=r"C:\Users\you\AppData\Local\Programs\Julia-1.11.0\bin\julia.exe"
)
```

The Windows conda environment does not include the Google Cloud CLI. To run
manual malariagen-data experiments against Google Cloud Storage on Windows,
install Google Cloud CLI with the official Windows installer, open a new
terminal, and then authenticate:

```powershell
(New-Object Net.WebClient).DownloadFile(
  "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe",
  "$env:Temp\GoogleCloudSDKInstaller.exe"
)
& "$env:Temp\GoogleCloudSDKInstaller.exe"
gcloud auth application-default login
```

Paths with spaces are passed as separate subprocess arguments, not through a
shell command string.

## Troubleshooting

### Julia not found

Install Julia from <https://julialang.org/downloads/> or pass the executable
path to `OpenAdmixtureRunner(julia=...)`.

### OpenADMIXTURE.jl not installed

Run `admixture setup` to instantiate the packaged Julia project.

### Missing PLINK files

Ensure the `.bed`, `.bim`, and `.fam` files all exist and are non-empty. Pass
the shared prefix, not a directory.

### Output files not found

Check `result.stdout`/`result.stderr` or the raised exception. Remove stale
outputs if multiple candidate `.Q` files match the same output prefix.

### OpenADMIXTURE runtime tests

Runtime tests require all of:

- Julia on `PATH`;
- OpenADMIXTURE.jl installed;

These tests fail if Julia or OpenADMIXTURE.jl is unavailable. The default
runtime test uses a tiny local PLINK data set and does not read from Google
Cloud Storage.

The malariagen-data compatibility test is development-only, skips on Python
3.13+, and imports `malariagen_data` inside the test only, so the package does
not gain a production dependency on malariagen-data.

For manual experiments against real MalariaGEN data on Google Cloud Storage, you
need access to the relevant bucket and Google Cloud Application Default
Credentials. Authenticate locally with:

```bash
makim gcloud.auth
```

For non-interactive local runs with a service-account JSON key:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

For custom GitHub Actions workflows that need real MalariaGEN-GCS access, set
the `GOOGLE_CREDENTIALS` repository secret to a service-account JSON key with
access to MalariaGEN data on Google Cloud Storage. A Google API key is not
sufficient because malariagen-data uses Google Cloud Application Default
Credentials for GCS. This is not required by the default CI test suite.

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
