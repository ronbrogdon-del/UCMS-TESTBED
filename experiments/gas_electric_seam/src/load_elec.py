"""Load Texas7k.m into pandapower and solve the base AC power flow."""
import sys, time, warnings
warnings.filterwarnings("ignore")
from matpowercaseframes import CaseFrames
import pandapower as pp
from pandapower.converter.pypower import from_ppc
cf = CaseFrames(sys.argv[1])
ppc = {k: getattr(cf, k).values for k in ("bus", "gen", "branch")}
ppc["baseMVA"] = cf.baseMVA; ppc["version"] = "2"
if hasattr(cf, "gencost"): ppc["gencost"] = cf.gencost.values
net = from_ppc(ppc, f_hz=60, validate_conversion=False)
print("buses", len(net.bus), "loads", len(net.load), "gens", len(net.gen), "ext_grid", len(net.ext_grid), "sgen", len(net.sgen), "lines", len(net.line), "trafos", len(net.trafo))
print("total load MW %.0f | gen setpoints MW %.0f (+ext grid)" % (net.load.p_mw.sum(), net.gen.p_mw[net.gen.in_service].sum()))
t = time.time()
pp.runpp(net, algorithm="nr", init="dc", max_iteration=50)
print("AC power flow converged:", net.converged, "in %.1f s" % (time.time() - t))
print("slack/ext grid MW %.1f | losses MW %.1f" % (net.res_ext_grid.p_mw.sum(), net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()))
print("voltage pu min %.3f max %.3f | max line loading %.0f%%" % (net.res_bus.vm_pu.min(), net.res_bus.vm_pu.max(), net.res_line.loading_percent.max()))
pp.to_pickle(net, sys.argv[2])
