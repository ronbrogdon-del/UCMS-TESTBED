using GasTranSim
ts = initialize_simulator(ARGS[1] * "/"; eos = :simple_cnga)
run_simulator!(ts; showprogress = true)
write_final_state(ts; output_path = ARGS[1] * "/", final_state_file = "ic_final.json")
println("spin done")
