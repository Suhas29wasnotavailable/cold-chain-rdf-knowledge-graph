"""Validate cold_chain.ttl against the SHACL shapes in shapes.ttl.

Usage:  python shacl_check.py      (exit code 0 if the data conforms)

The data graph is expanded with RDFS inference first, so sh:class
constraints accept instances of subclasses. Results with severity
sh:Warning (in-transit temperature excursions) are printed but do not
make the data non-conforming.
"""
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

HERE = Path(__file__).parent


def check(data):
    shapes = Graph().parse(HERE / "shapes.ttl", format="turtle")
    return validate(data, shacl_graph=shapes, inference="rdfs", allow_warnings=True)


def warnings(data):
    """Messages of the sh:Warning results, e.g. temperature excursions."""
    _, report, _ = check(data)
    q = """PREFIX sh: <http://www.w3.org/ns/shacl#>
           SELECT ?m WHERE { ?r sh:resultSeverity sh:Warning ; sh:resultMessage ?m } ORDER BY ?m"""
    return [str(row.m) for row in report.query(q)]


def main():
    data = Graph().parse(HERE / "cold_chain.ttl", format="turtle")
    conforms, _, text = check(data)
    print(text.strip())
    print()
    for m in warnings(data) or ["no warnings"]:
        print(f"WARNING {m}" if m != "no warnings" else m)
    return 0 if conforms else 1


if __name__ == "__main__":
    sys.exit(main())
