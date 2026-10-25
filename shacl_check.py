"""Validate cold_chain.ttl against the SHACL shapes in shapes.ttl.

Usage:  python shacl_check.py      (exit code 0 if the data conforms)

The data graph is expanded with RDFS inference first, so sh:class
constraints accept instances of subclasses.
"""
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

HERE = Path(__file__).parent


def check(data):
    shapes = Graph().parse(HERE / "shapes.ttl", format="turtle")
    return validate(data, shacl_graph=shapes, inference="rdfs")


def main():
    data = Graph().parse(HERE / "cold_chain.ttl", format="turtle")
    conforms, _, text = check(data)
    print(text.strip())
    return 0 if conforms else 1


if __name__ == "__main__":
    sys.exit(main())
