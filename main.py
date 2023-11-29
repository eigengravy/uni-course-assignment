import json
import sys
import networkx as nx
import py_bipartite_matching as pbm
from tqdm import tqdm

import argparse


parser = argparse.ArgumentParser()
parser.add_argument("input", help="input json file", type=str)
parser.add_argument("iters", help="number of iterations", type=int)

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

# course_popularity = {c: 0 for c in courses}
# for prof in prof2course.keys():
#     for course in prof2course[prof]:
#         course_popularity[course] += 1

# print(courses)
# print(course_popularity)

course_nodes = [{"label": course, "bipartite": 0} for course in list(courses) * 2]

prof_nodes = [
    {"label": prof, "bipartite": 1}
    for profs in map(lambda item: list(item[1]) * int(item[0] / 0.5), cat2profs.items())
    for prof in profs
]

if len(course_nodes) != len(prof_nodes):
    print(
        "invalid preferences. consider removing an elective or reducing a profs load."
    )
    sys.exit()
# print(len(course_nodes), len(prof_nodes))
# print(prof2course)
# while len(course_nodes) != len(prof_nodes):
#     if len(course_nodes) < len(prof_nodes):
#         pro

nodes = list(enumerate(course_nodes + prof_nodes))

G = nx.Graph()

G.add_nodes_from(nodes)


print(f"created bipartite graph with {len(G.nodes())} nodes")
for node in G.nodes(data=True):
    print(
        node,
    )
print()

graph_course_nodes = [n for n in G.nodes(data=True) if n[1]["bipartite"] == 0]
graph_prof_nodes = [n for n in G.nodes(data=True) if n[1]["bipartite"] == 1]


print(len(graph_course_nodes), len(graph_prof_nodes))
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

min_match = nx.bipartite.minimum_weight_full_matching(G)
min_allotment = matching_to_allotment(min_match)

# print(min_cost, )

allotments = [min_allotment]
count = 1
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


with open("output.json", "w") as f:
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
