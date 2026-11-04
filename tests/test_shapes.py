import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shacl_check  # noqa: E402

CC = "http://example.org/coldchain/vocab#"
T91_1100 = URIRef("http://example.org/coldchain/id/observation/T91-20261005T1100")


def data():
    return Graph().parse(shacl_check.HERE / "cold_chain.ttl", format="turtle")


def test_data_conforms():
    assert shacl_check.check(data())[0]


def test_reading_with_two_values_or_a_string_value_is_rejected():
    g = data()
    g.add((T91_1100, URIRef(CC + "celsiusValue"), Literal("9.4 C")))
    conforms, _, text = shacl_check.check(g)
    assert not conforms and "celsiusValue" in text


def test_shipment_without_container_is_rejected():
    g = data()
    g.remove((URIRef("http://example.org/coldchain/id/shipment/S102"), URIRef(CC + "transportedIn"), None))
    assert not shacl_check.check(g)[0]


def test_in_transit_excursion_is_a_warning_not_a_violation():
    g = data()
    assert shacl_check.check(g)[0]
    assert shacl_check.warnings(g) == ["In-transit temperature excursion: 9.4 C outside 2.0..8.0 for shipment S101"]


def test_pre_dispatch_reading_is_not_reported():
    assert not any("1.6" in m for m in shacl_check.warnings(data()))
