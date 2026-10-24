"""Draw a readable subgraph around shipment S101 -> figures/s101_subgraph.png/.svg

Every edge drawn is checked against cold_chain.ttl, so the figure cannot
show a triple that is not in the data.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from rdflib import Graph, Literal, URIRef

HERE = Path(__file__).parent
g = Graph()
g.parse(HERE / "cold_chain.ttl")
nm = g.namespace_manager

# node id -> (x, y, kind) ; kind: res | lit | cls
N = {
    "cc:Shipment":            (0.0, 6.2, "cls"),
    "shp:S101":               (0.0, 4.6, "res"),
    "agent:frostline":        (-5.4, 6.2, "res"),
    "wh:BLR-N":               (-5.4, 3.0, "res"),
    "wh:MYS-C":               (-5.4, 4.6, "res"),
    "lot:VA-2609-01":         (5.0, 6.2, "res"),
    "prod:vaccine-a":         (5.0, 4.4, "res"),
    "rng:2to8C":              (5.0, 2.6, "res"),
    '"2.0"':                  (2.9, 1.0, "lit"),
    '"8.0"':                  (7.1, 1.0, "lit"),
    "ctr:C7":                 (0.0, 2.6, "res"),
    "sen:T91":                (0.0, 0.6, "res"),
    "obs:T91-20261005T1100":  (-2.6, -1.4, "res"),
    '"9.4"':                  (-6.6, -1.4, "lit"),
    '"2026-10-05T11:00:00+05:30"': (-2.6, -3.0, "lit"),
    "evt:S101-dispatch":      (-5.4, 1.2, "res"),
    '"2026-10-05T08:00:00+05:30"': (-5.4, -0.2, "lit"),
}
E = [
    ("shp:S101", "rdf:type", "cc:Shipment"),
    ("shp:S101", "cc:carriedBy", "agent:frostline"),
    ("shp:S101", "cc:origin", "wh:BLR-N"),
    ("shp:S101", "cc:destination", "wh:MYS-C"),
    ("shp:S101", "cc:containsLot", "lot:VA-2609-01"),
    ("lot:VA-2609-01", "cc:ofProduct", "prod:vaccine-a"),
    ("prod:vaccine-a", "cc:requiredRange", "rng:2to8C"),
    ("rng:2to8C", "cc:minTemperature", '"2.0"'),
    ("rng:2to8C", "cc:maxTemperature", '"8.0"'),
    ("shp:S101", "cc:transportedIn", "ctr:C7"),
    ("ctr:C7", "cc:fittedWith", "sen:T91"),
    ("obs:T91-20261005T1100", "cc:madeBySensor", "sen:T91"),
    ("obs:T91-20261005T1100", "cc:observedContainer", "ctr:C7"),
    ("obs:T91-20261005T1100", "cc:celsiusValue", '"9.4"'),
    ("obs:T91-20261005T1100", "cc:resultTime", '"2026-10-05T11:00:00+05:30"'),
    ("evt:S101-dispatch", "cc:eventOf", "shp:S101"),
    ("evt:S101-dispatch", "cc:atFacility", "wh:BLR-N"),
    ("evt:S101-dispatch", "cc:eventTime", '"2026-10-05T08:00:00+05:30"'),
]


def expand(term):
    return URIRef(nm.expand_curie(term))


for s, p, o in E:  # check every drawn edge exists in the data
    S, P = expand(s), expand(p)
    if o.startswith('"'):
        ok = any(str(v) == o.strip('"') for v in g.objects(S, P))
    else:
        ok = (S, P, expand(o)) in g
    assert ok, f"edge not in graph: {s} {p} {o}"

STYLE = {
    "res": dict(fc="#dbe9f7", ec="#2c5d8a"),
    "lit": dict(fc="#fff4d6", ec="#a8781c"),
    "cls": dict(fc="#e3f2e1", ec="#3f7a38"),
}
fig, ax = plt.subplots(figsize=(13, 9.2))
ax.set_xlim(-7.6, 8.0)
ax.set_ylim(-3.8, 7.0)
ax.axis("off")

for s, p, o in E:
    x0, y0, _ = N[s]
    x1, y1, _ = N[o]
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.2,
                                shrinkA=24, shrinkB=24))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.text(mx, my, p, fontsize=8.5, color="#333", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))

for name, (x, y, kind) in N.items():
    st = STYLE[kind]
    style = "round,pad=0.35" if kind != "lit" else "square,pad=0.35"
    ax.text(x, y, name, fontsize=9.5, ha="center", va="center",
            family="monospace" if kind == "lit" else None,
            bbox=dict(boxstyle=style, fc=st["fc"], ec=st["ec"], lw=1.4))

legend = [("IRI resource (instance)", "res"), ("Literal value", "lit"), ("Class (vocabulary)", "cls")]
for i, (lab, k) in enumerate(legend):
    ax.text(3.4, -2.2 - i * 0.5, "  " + lab, fontsize=9, va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc=STYLE[k]["fc"], ec=STYLE[k]["ec"]))
ax.set_title("Subgraph of shipment S101 (18 triples from cold_chain.ttl)", fontsize=13)

out = HERE / "figures"
out.mkdir(exist_ok=True)
fig.tight_layout()
fig.savefig(out / "s101_subgraph.png", dpi=170)
fig.savefig(out / "s101_subgraph.svg")
print("wrote figures/s101_subgraph.png and .svg")
