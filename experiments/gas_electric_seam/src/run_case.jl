using GasTranSim, JSON
folder = ARGS[1] * "/"
ts = initialize_simulator(folder; eos = :simple_cnga)
t1 = time(); run_simulator!(ts; showprogress = true)
println("ran in ", round(time() - t1, digits = 1), " s")
out = Dict("time" => ts.sol["time_points"], "nodes" => Dict(k => v["pressure"] for (k, v) in ts.sol["nodes"]))
open(ARGS[2], "w") do f; JSON.print(f, out); end
println("saved")
