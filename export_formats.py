"""Serialise cold_chain.ttl to other RDF formats for tools that do not read Turtle.

Usage:  python export_formats.py           (writes exports/cold_chain.{nt,jsonld,rdf})
        python export_formats.py --check   (exit 1 if the committed exports are stale)
"""
import argparse
import sys
from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic

HERE = Path(__file__).parent
FORMATS = {"nt": "nt", "jsonld": "json-ld", "rdf": "xml"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="verify the exports instead of writing them")
    args = ap.parse_args(argv)

    g = Graph().parse(HERE / "cold_chain.ttl", format="turtle")
    out = HERE / "exports"
    stale = []
    for ext, fmt in FORMATS.items():
        path = out / f"cold_chain.{ext}"
        if args.check:
            if not path.exists() or not isomorphic(g, Graph().parse(path, format=fmt)):
                stale.append(path.name)
            continue
        out.mkdir(exist_ok=True)
        text = g.serialize(format=fmt)
        if ext == "nt":  # N-Triples has no fixed order; sort for stable diffs
            text = "\n".join(sorted(l for l in text.splitlines() if l)) + "\n"
        path.write_text(text)
        print(f"wrote {path.relative_to(HERE)} ({len(g)} triples)")
    if stale:
        print("stale or missing: " + ", ".join(stale))
    elif args.check:
        print(f"all {len(FORMATS)} exports match cold_chain.ttl ({len(g)} triples)")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
