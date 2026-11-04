import sys
from pathlib import Path

from rdflib import Graph, URIRef

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import draw_graph  # noqa: E402


def data():
    return Graph().parse(draw_graph.HERE / "cold_chain.ttl")


def test_every_drawn_edge_is_in_the_data():
    assert draw_graph.missing_edges(data()) == []


def test_a_removed_triple_is_caught():
    g = data()
    g.remove((URIRef("http://example.org/coldchain/id/shipment/S101"),
              URIRef("http://example.org/coldchain/vocab#transportedIn"), None))
    assert draw_graph.missing_edges(g) == [("shp:S101", "cc:transportedIn", "ctr:C7")]


def test_every_edge_endpoint_has_a_position():
    assert {n for s, _, o in draw_graph.E for n in (s, o)} <= set(draw_graph.N)
