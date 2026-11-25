using GasTranSim, JSON
folder = ARGS[1] * "/"
ts = initialize_simulator(folder; eos = :simple_cnga)
run_simulator!(ts; showprogress = false)
write_final_state(ts; output_path = folder, final_state_file = "ic_final.json")
nodes = split(ARGS[2], ",")
open(folder * "track.json", "w") do f
    JSON.print(f, Dict("time" => ts.sol["time_points"], "nodes" => Dict(n => ts.sol["nodes"][n]["pressure"] for n in nodes)))
end
println("chunk done")
