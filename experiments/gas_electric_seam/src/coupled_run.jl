# Coupled gas–electric run (v2: adds scheduled compressor-station failures): GasTranSim stepped with the electric rules applied every coupling interval.
# Usage: julia --project=<env> coupled_run.jl <case_dir> <coupling_data.json> <out.json> <mode: uri|posturi> [couple_dt_s=60]
#
# Rules (agreed 24 Nov 2026):
#  1. Plant gas node below floor (2.8 MPag) -> units run back to Pmin; below trip level -> trip to 0. Latched.
#  2. Lost MW replaced from non-gas headroom first, then gas plants still above floor (pro rata to headroom);
#     remainder = firm load shed, pro rata statewide (copper plate, v1).
#  3. Loop (mode "uri" only): shed fraction s cuts every processing plant's supply by s (latched at max s);
#     electric-driven compressors (10% placeholder) lose boost in proportion to s (latched).
#  4. Plant gas withdrawal follows plant MW (factor = MW / base MW).
# Compressor failures (optional, scenario.json "compressor_failures": list of {comps, mode, t_fail_s, ramp_s}):
#   mode "bypass":  station units trip, gas passes through the bypass; ratio ramps to 1.0 over ramp_s.
#   mode "isolate": station valved off (e.g. fire or rupture shut-in); flow ramps from its value at t_fail to 0 over ramp_s.
#   A failed station is latched failed and is no longer scaled by the electric loop.
using GasTranSim, JSON
const G = GasTranSim

folder, datafile, outfile, mode = ARGS[1] * "/", ARGS[2], ARGS[3], ARGS[4]
couple_dt = length(ARGS) > 4 ? parse(Float64, ARGS[5]) : 60.0
cd_ = JSON.parsefile(datafile)
scen = JSON.parsefile(folder * "scenario.json")
H = Float64(scen["horizon_s"])

ts = initialize_simulator(folder; eos = :simple_cnga)
t_f = G.params(ts, :t_f); t_0 = G.params(ts, :t_0)
tscale = (t_f - t_0) / H                      # internal time units per second
pnom = G.nominal_values(ts)[:pressure]
P(i) = G.ref(ts, :node, i, "pressure") * pnom # Pa

plants = Dict(parse(Int, k) => v for (k, v) in cd_["plants"])
pids = sort(collect(keys(plants)))
state = Dict(i => 0 for i in pids)            # 0 normal, 1 runback, 2 trip
floorP, tripP = cd_["floor_pa"], cd_["trip_pa"]

# wrap boundary conditions with live multipliers
bcn = ts.boundary_conditions[:node]
wmult = Dict(i => Ref(1.0) for i in pids)
for i in pids
    orig = bcn[i]["spl"]; ct = bcn[i]["control_type"]; m = wmult[i]
    bcn[i] = Dict{String,Any}("spl" => (t -> orig(t) * m[]), "control_type" => ct)
end
smult = Ref(1.0)
for i in cd_["processing_nodes"]
    haskey(bcn, i) || continue
    orig = bcn[i]["spl"]; ct = bcn[i]["control_type"]
    bcn[i] = Dict{String,Any}("spl" => (t -> orig(t) * smult[]), "control_type" => ct)
end
cmult = Ref(1.0)
bcc = ts.boundary_conditions[:compressor]
for c in cd_["electric_compressors"]
    orig = bcc[c]["spl"]
    bcc[c] = Dict{String,Any}("spl" => (t -> begin
        ctp, v = orig(t); Int(ctp) == 0 ? (ctp, 1.0 + (v - 1.0) * cmult[]) : (ctp, v)
    end))
end

total_load = cd_["total_load_mw"]; ng_head = cd_["nongas_headroom_mw"]
s_max = 0.0
rec = Dict("t_s" => Float64[], "pressure_kPa" => Dict(string(i) => Float64[] for i in pids),
           "state" => Dict(string(i) => Int[] for i in pids), "lost_mw" => Float64[], "redisp_nongas_mw" => Float64[],
           "redisp_gas_mw" => Float64[], "shed_mw" => Float64[], "shed_frac" => Float64[], "supply_mult" => Float64[],
           "compressor_mult" => Float64[], "plants_runback" => Int[], "plants_trip" => Int[])
events = Dict{String,Any}()

function couple!(tsec)
    global s_max
    for i in pids
        p = P(i)
        if state[i] < 2 && p < tripP
            state[i] = 2
        elseif state[i] < 1 && p < floorP
            state[i] = 1
        end
    end
    lost = 0.0; head_gas = Dict{Int,Float64}(); mw = Dict{Int,Float64}()
    for i in pids
        pl = plants[i]
        mw[i] = state[i] == 0 ? pl["pg"] : state[i] == 1 ? min(pl["pmin"], pl["pg"]) : 0.0
        lost += pl["pg"] - mw[i]
        state[i] == 0 && (head_gas[i] = max(pl["pmax"] - pl["pg"], 0.0))
    end
    r1 = min(lost, ng_head)
    hg = sum(values(head_gas); init = 0.0)
    r2 = min(lost - r1, hg)
    for (i, h) in head_gas
        hg > 0 && (mw[i] += r2 * h / hg)
    end
    shed = max(lost - r1 - r2, 0.0)
    s = shed / total_load
    for i in pids
        pg = plants[i]["pg"]
        pg > 0 && (wmult[i][] = mw[i] / pg)
    end
    if mode == "uri"
        s_max = max(s_max, s)
        smult[] = 1.0 - s_max
        cmult[] = 1.0 - s_max
    end
    nrb = count(i -> state[i] == 1, pids); ntr = count(i -> state[i] == 2, pids)
    (nrb + ntr > 0) && !haskey(events, "first_runback_s") && (events["first_runback_s"] = tsec)
    ntr > 0 && !haskey(events, "first_trip_s") && (events["first_trip_s"] = tsec)
    shed > 0 && !haskey(events, "first_shed_s") && (events["first_shed_s"] = tsec)
    push!(rec["t_s"], tsec)
    for i in pids
        push!(rec["pressure_kPa"][string(i)], P(i) / 1000); push!(rec["state"][string(i)], state[i])
    end
    push!(rec["lost_mw"], lost); push!(rec["redisp_nongas_mw"], r1); push!(rec["redisp_gas_mw"], r2)
    push!(rec["shed_mw"], shed); push!(rec["shed_frac"], s); push!(rec["supply_mult"], smult[])
    for c in fcomps
        r = rec["failed_comp"][string(c)]; cc = G.ref(ts, :compressor, c)
        push!(r["flow_kg_s"], cc["flow"] * fnom); push!(r["p_suction_kPa"], P(cc["fr_node"]) / 1000)
        push!(r["p_discharge_kPa"], P(cc["to_node"]) / 1000)
    end
    push!(rec["compressor_mult"], cmult[]); push!(rec["plants_runback"], nrb); push!(rec["plants_trip"], ntr)
end

failures = get(scen, "compressor_failures", Any[])
for f in failures
    f["t_int"] = t_0 + Float64(f["t_fail_s"]) * tscale; f["done"] = false
end
function apply_failure!(f)
    rs = max(Float64(get(f, "ramp_s", 60.0)), 1.0) * tscale; tf = f["t_int"]
    for c in f["comps"]
        if f["mode"] == "bypass"
            _, r0 = bcc[c]["spl"](tf)
            bcc[c] = Dict{String,Any}("spl" => (t -> (0, r0 + (1.0 - r0) * clamp((t - tf) / rs, 0.0, 1.0))))
        elseif f["mode"] == "isolate"
            F0 = G.ref(ts, :compressor, c)["flow"]
            bcc[c] = Dict{String,Any}("spl" => (t -> (2, F0 * (1.0 - clamp((t - tf) / rs, 0.0, 1.0)))))
        else
            error("unknown failure mode " * string(f["mode"]))
        end
    end
    f["done"] = true
    events["compressor_failure_s"] = get(events, "compressor_failure_s", Float64(f["t_fail_s"]))
    println("compressor failure applied: ", f["comps"], " ", f["mode"], " at ", f["t_fail_s"], " s"); flush(stdout)
end

fcomps = sort(unique(Int[c for f in failures for c in f["comps"]]))
rec["failed_comp"] = Dict(string(c) => Dict("flow_kg_s" => Float64[], "p_suction_kPa" => Float64[], "p_discharge_kPa" => Float64[]) for c in fcomps)
fnom = G.nominal_values(ts)[:mass_flow]

ts.params[:load_adjust] = false
base_dt = G.params(ts, :base_dt)
next_couple = t_0
nsteps = 0; t_wall = time()
while G.ref(ts, :current_time) < t_f - G.TOL
    global next_couple, nsteps
    tnow = G.ref(ts, :current_time)
    for f in failures
        (!f["done"] && tnow >= f["t_int"] - G.TOL) && apply_failure!(f)
    end
    if tnow >= next_couple - G.TOL
        couple!((tnow - t_0) / tscale)
        next_couple += couple_dt * tscale
    end
    dt_step = min(base_dt, t_f - tnow)
    ts.params[:dt] = dt_step
    G.advance_current_time!(ts, dt_step)
    G.advance_pipe_density_internal!(ts, :serial)
    G.advance_node_pressure_mass_flux!(ts, :serial)
    G.advance_pipe_mass_flux_internal!(ts, :serial)
    G._compute_compressor_flows!(ts)
    nsteps += 1
    if nsteps % 5000 == 0
        println("t = ", round((G.ref(ts, :current_time) - t_0) / tscale / 3600, digits = 2), " h | wall ",
                round(time() - t_wall), " s | runback ", rec["plants_runback"][end], " trip ", rec["plants_trip"][end],
                " shed ", round(rec["shed_mw"][end]), " MW"); flush(stdout)
    end
end
couple!(H)
rec["events"] = events; rec["mode"] = mode; rec["couple_dt_s"] = couple_dt; rec["scenario"] = scen
open(outfile, "w") do f; JSON.print(f, rec); end
println("done: ", events)
