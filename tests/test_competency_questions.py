"""Check the actual answers to the competency questions, not only row counts."""
import sys
from pathlib import Path

import owlrl
import pytest
from rdflib import Graph

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate  # noqa: E402

QUERIES = {title.split()[0]: q for title, q in validate.load_queries()}


@pytest.fixture(scope="module")
def graph():
    g = Graph()
    g.parse(validate.TTL, format="turtle")
    return g


def answer(g, qid):
    return validate.run(g, QUERIES[qid])[0]


def test_triple_count(graph):
    assert answer(graph, "Q1") == [("334",)]


def test_cq2_permitted_ranges(graph):
    rows = answer(graph, "Q3")
    assert [(r[0], float(r[2]), float(r[3])) for r in rows] == [("S101", 2.0, 8.0), ("S102", -25.0, -15.0)]


def test_cq3_only_the_in_transit_excursion_is_reported(graph):
    (shipment, sensor, time, value, _, maximum), = answer(graph, "Q4")
    assert (shipment, sensor, float(value), float(maximum)) == ("S101", "T91", 9.4, 8.0)
    assert "T11:00" in time


def test_cq5_reading_counts_per_sensor(graph):
    assert {(r[2], int(r[4])) for r in answer(graph, "Q6")} == {("T91", 5), ("T92", 3)}


def test_cq6_needs_rdfs_inference(graph):
    assert answer(graph, "Q7") == []
    gi = Graph()
    for t in graph:
        gi.add(t)
    owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(gi)
    assert len(validate.run(gi, QUERIES["Q7"])[0]) == 14


def test_data_quality_query_finds_no_problems(graph):
    assert answer(graph, "Q8") == []


def test_data_quality_query_catches_a_broken_range(graph):
    broken = Graph()
    for t in graph:
        broken.add(t)
    broken.update("""PREFIX cc: <http://example.org/coldchain/vocab#>
        DELETE { ?r cc:minTemperature ?lo } INSERT { ?r cc:minTemperature 99.0 }
        WHERE { ?r cc:minTemperature ?lo } """)
    assert {r[0] for r in validate.run(broken, QUERIES["Q8"])[0]} == {"min not below max"}
