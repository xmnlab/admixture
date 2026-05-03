# Bridge script used by the Python admixture package.
# It intentionally depends only on Julia stdlib packages plus OpenADMIXTURE.jl.

using DelimitedFiles
using Random
using Base.Threads
using OpenADMIXTURE

function parse_cli(args)
    parsed = Dict{String,String}()
    i = 1
    while i <= length(args)
        arg = args[i]
        if !startswith(arg, "--")
            error("Unexpected positional argument: $(arg)")
        end
        key = arg[3:end]
        if isempty(key)
            error("Empty command-line flag is not allowed")
        end
        if i == length(args) || startswith(args[i + 1], "--")
            parsed[key] = "true"
            i += 1
        else
            parsed[key] = args[i + 1]
            i += 2
        end
    end
    return parsed
end

function require_arg(parsed, key)
    if !haskey(parsed, key)
        error("Missing required argument --$(key)")
    end
    return parsed[key]
end

function optional_int(parsed, key, default)
    if haskey(parsed, key)
        return parse(Int, parsed[key])
    end
    return default
end

function optional_float(parsed, key, default)
    if haskey(parsed, key)
        return parse(Float64, parsed[key])
    end
    return default
end

function optional_bool(parsed, key, default)
    if !haskey(parsed, key)
        return default
    end
    value = lowercase(parsed[key])
    if value in ("1", "true", "yes", "y")
        return true
    elseif value in ("0", "false", "no", "n")
        return false
    end
    error("--$(key) must be true or false, got $(parsed[key])")
end

function bed_path_from_prefix(prefix)
    if endswith(lowercase(prefix), ".bed")
        return prefix
    end
    return prefix * ".bed"
end

function main(args)
    parsed = parse_cli(args)
    allowed = Set([
        "bfile",
        "k",
        "out",
        "seed",
        "threads",
        "max-iter",
        "tol",
        "em-iter",
        "em-iters",
        "use-gpu",
        "verbose",
        "sparsity",
        "skfr-tries",
        "skfr-max-inner-iter",
        "skfr-mode",
    ])
    unknown = setdiff(Set(keys(parsed)), allowed)
    if !isempty(unknown)
        error("Unknown argument(s): " * join(sort(collect(unknown)), ", "))
    end

    bfile = require_arg(parsed, "bfile")
    k = parse(Int, require_arg(parsed, "k"))
    out_prefix = require_arg(parsed, "out")
    bed_file = bed_path_from_prefix(bfile)

    seed = optional_int(parsed, "seed", nothing)
    requested_threads = optional_int(parsed, "threads", nothing)
    max_iter = optional_int(parsed, "max-iter", 1000)
    tol = optional_float(parsed, "tol", 1e-7)
    em_iters = if haskey(parsed, "em-iters")
        optional_int(parsed, "em-iters", 5)
    else
        optional_int(parsed, "em-iter", 5)
    end
    use_gpu = optional_bool(parsed, "use-gpu", false)
    verbose = optional_bool(parsed, "verbose", false)
    sparsity = optional_int(parsed, "sparsity", nothing)
    skfr_tries = optional_int(parsed, "skfr-tries", 1)
    skfr_max_inner_iter = optional_int(parsed, "skfr-max-inner-iter", 50)
    skfr_mode = Symbol(get(parsed, "skfr-mode", "global"))

    if requested_threads !== nothing && requested_threads != nthreads()
        println(
            stderr,
            "Requested ",
            requested_threads,
            " Julia thread(s), but this session has ",
            nthreads(),
            ". Pass --threads before the script path when launching Julia.",
        )
    end

    out_dir = dirname(out_prefix)
    if !isempty(out_dir)
        mkpath(out_dir)
    end

    rng = seed === nothing ? Random.GLOBAL_RNG : MersenneTwister(seed)

    println("Running OpenADMIXTURE.jl")
    println("Input BED: $(bed_file)")
    println("K: $(k)")
    println("Output prefix: $(out_prefix)")
    println("Julia threads: $(nthreads())")

    d, clusters, aims = OpenADMIXTURE.run_admixture(
        bed_file,
        k;
        rng=rng,
        sparsity=sparsity,
        prefix=out_prefix,
        skfr_tries=skfr_tries,
        skfr_max_inner_iter=skfr_max_inner_iter,
        skfr_mode=skfr_mode,
        admix_n_iter=max_iter,
        admix_rtol=tol,
        admix_n_em_iters=em_iters,
        use_gpu=use_gpu,
        verbose=verbose,
        progress_bar=false,
    )

    q_path = out_prefix * ".Q"
    p_path = out_prefix * ".P"
    log_path = out_prefix * ".log"

    # OpenADMIXTURE.jl stores q as K x samples. The conventional .Q layout is
    # samples x K, so transpose q before writing it for Python parsing.
    writedlm(q_path, permutedims(d.q), ' ')
    writedlm(p_path, d.p, ' ')

    open(log_path, "w") do io
        println(io, "backend=OpenADMIXTURE.jl")
        println(io, "input_bed=$(bed_file)")
        println(io, "k=$(k)")
        println(io, "julia_threads=$(nthreads())")
        println(io, "max_iter=$(max_iter)")
        println(io, "tol=$(tol)")
        println(io, "em_iters=$(em_iters)")
        println(io, "use_gpu=$(use_gpu)")
        println(io, "log_likelihood=$(d.ll_new)")
        println(io, "q_path=$(q_path)")
        println(io, "p_path=$(p_path)")
        clusters_text = clusters === nothing ? "nothing" : string(length(clusters))
        aims_text = aims === nothing ? "nothing" : string(length(aims))
        println(io, "clusters=$(clusters_text)")
        println(io, "aims=$(aims_text)")
    end

    println("Wrote Q: $(q_path)")
    println("Wrote P: $(p_path)")
    println("Wrote log: $(log_path)")
    return nothing
end

try
    main(ARGS)
catch err
    showerror(stderr, err, catch_backtrace())
    println(stderr)
    exit(1)
end
