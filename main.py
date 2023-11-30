import json
import sys
import networkx as nx
import py_bipartite_matching as pbm
from tqdm import tqdm

import argparse


parser = argparse.ArgumentParser()
parser.add_argument("input", help="input json file", type=str)
parser.add_argument("iters", help="number of iterations", type=int)
parser.add_argument("output", help="output json file", type=str, default="output.json")
parser.add_argument(
    "-v", "--verbose", action="store_true", help="increase output verbosity"
)

args = parser.parse_args()

profs = set()
cat2profs = dict()

fd_cdc = set()
fd_el = set()
hd_cdc = set()
hd_el = set()

courses = set()

prof2course = dict()

nodes = list()

print("parsing input")
with open(args.input) as f:
    config = json.loads(f.read())
    for item in config:
        prof = item["name"]

        profs.add(prof)
        fd_cdc.update(item["fd cdc"])
        fd_el.update(item["fd el"])
        hd_cdc.update(item["hd cdc"])
        hd_el.update(item["hd el"])
        prof2course[prof] = (
            item["fd cdc"] + item["fd el"] + item["hd cdc"] + item["hd el"]
        )
        cat2profs.setdefault(item["category"], set()).add(prof)

courses = fd_cdc.union(fd_el).union(hd_cdc).union(hd_el)

print(f"found {len(profs)} profs and {len(courses)} courses\n")
if args.verbose:
    print("courses:", courses)
    print("profs:", profs)
    print()

course_nodes = [{"label": course, "bipartite": 0} for course in list(courses) * 2]

prof_nodes = [
    {"label": prof, "bipartite": 1}
    for profs in map(lambda item: list(item[1]) * int(item[0] / 0.5), cat2profs.items())
    for prof in profs
]

if len(course_nodes) < len(prof_nodes):
    print(
        f"unable to generate assignments. consider adding electives or reducing a profs load by {(len(prof_nodes)-len(course_nodes))/2} units."
    )
    sys.exit()

if len(course_nodes) > len(prof_nodes):
    print(
        f"unable to generate assignments. consider removing electives or increasing a profs load by {(len(course_nodes)-len(prof_nodes))/2} units."
    )
    sys.exit()

nodes = list(enumerate(course_nodes + prof_nodes))

G = nx.Graph()

G.add_nodes_from(nodes)


print(f"created bipartite graph with {len(G.nodes())} nodes")
if args.verbose:
    for node in G.nodes(data=True):
        print(
            node,
        )
    print()

graph_course_nodes = [n for n in G.nodes(data=True) if n[1]["bipartite"] == 0]
graph_prof_nodes = [n for n in G.nodes(data=True) if n[1]["bipartite"] == 1]


for p in graph_prof_nodes:
    for c in graph_course_nodes:
        G.add_edge(
            p[0],
            c[0],
            weight=prof2course[p[1]["label"]].index(c[1]["label"])
            if c[1]["label"] in prof2course[p[1]["label"]]
            else float("inf"),
        )


def matching_to_allotment(matching):
    allotment = {p: set() for p in profs}
    for edge in set([tuple(sorted(i)) for i in matching.items()]):
        allotment[nodes[edge[1]][1]["label"]].add(nodes[edge[0]][1]["label"])
    return allotment


def allotment_to_cost(allotment):
    c = 0
    for k in allotment.keys():
        for v in allotment[k]:
            if v in prof2course[k]:
                c += prof2course[k].index(v)
    return c


def verify_allotment(allotment):
    alloted_courses = {c for p in allotment.keys() for c in allotment[p]}
    return fd_cdc.issubset(alloted_courses) and hd_cdc.issubset(alloted_courses)


print("generating matchings")


allotments = []
count = 0
for matching in tqdm(pbm.enum_perfect_matchings(G), total=int(sys.argv[2])):
    allotment = matching_to_allotment(matching)
    count += 1
    if allotment not in allotments:
        allotments.append(allotment)
    if count >= int(args.iters):
        break


allotments = sorted(
    filter(verify_allotment, allotments),
    key=allotment_to_cost,
)

print(f"\nfound {len(allotments)} unique and valid assignments")


with open(args.output, "w") as f:
    f.write(
        json.dumps(
            [
                {
                    "courses": {k: list(v) for k, v in allotment.items()},
                    "score": allotment_to_cost(allotment),
                }
                for allotment in allotments
            ],
            indent=4,
        )
    )
print("saved to output.json")
