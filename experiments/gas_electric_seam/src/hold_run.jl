# Steady-hold run of the converted Texas7k gas network (no injection).
# Usage: julia --project=<env> hold_run.jl <case_dir> <out_json>
using GasTranSim, JSON
folder = ARGS[1] * "/"
t0 = time()
ts = initialize_simulator(folder; eos = :simple_cnga)
println("initialized in ", round(time() - t0, digits = 1), " s")
t1 = time()
run_simulator!(ts; showprogress = false)
println("ran in ", round(time() - t1, digits = 1), " s")
out = Dict("time" => ts.sol["time_points"], "nodes" => Dict(), "pipes_in" => Dict())
for (k, v) in ts.sol["nodes"]
    out["nodes"][k] = v["pressure"]
end
for (k, v) in ts.sol["pipes"]
    out["pipes_in"][k] = v["in_flow"]
end
open(ARGS[2], "w") do f
    JSON.print(f, out)
end
println("saved")
