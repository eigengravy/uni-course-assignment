import csv
import sys
import networkx as nx


profs = set()
courses = set()

x1_profs = set()
x2_profs = set()
x3_profs = set()
# prof2cat = dict()
prof2course = dict()
# course2prof = dict()

nodes = list()

# node2idx = dict()


with open(sys.argv[1]) as f:
    for line in csv.reader(f):
        prof = line[0]

        profs.add(prof)
        courses.update(line[2:])

        prof2course[prof] = line[2:]

        match line[1]:
            case "x1":
                x1_profs.add(prof)
            case "x2":
                x2_profs.add(prof)
            case "x3":
                x3_profs.add(prof)


course_nodes = [{"label": course, "bipartite": 0} for course in list(courses) * 2]

prof_nodes = [
    {"label": prof, "bipartite": 1}
    for prof in list(x1_profs) + list(x2_profs) * 2 + list(x3_profs) * 3
]

nodes = list(enumerate(course_nodes + prof_nodes))


G = nx.Graph()

G.add_nodes_from(nodes)

for node in G.nodes(data=True):
    print(node)

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

# allotment = {c: set() for c in courses}
# for edge in set(
#     [tuple(sorted(i)) for i in nx.bipartite.minimum_weight_full_matching(G).items()]
# ):
#     allotment[nodes[edge[0]][1]["label"]].add(nodes[edge[1]][1]["label"])


def matching2allotment(matching):
    allotment = {c: set() for c in courses}
    for edge in set([tuple(sorted(i)) for i in matching.items()]):
        allotment[nodes[edge[0]][1]["label"]].add(nodes[edge[1]][1]["label"])
    return allotment


def allotment2cost(allotment):
    c = 0
    for k in allotment.keys():
        for v in allotment[k]:
            c += prof2course[v].index(k)
    return c


min_match = nx.bipartite.minimum_weight_full_matching(G)
min_allotment = matching2allotment(min_match)
min_cost = allotment2cost(min_allotment)

print(min_cost, min_allotment)

max_match = nx.bipartite.hopcroft_karp_matching(G)
max_allotment = matching2allotment(max_match)
max_cost = allotment2cost(max_allotment)

print(max_cost, max_allotment)

# from matplotlib import pyplot as plt

# nx.draw(G, with_labels=True)

# plt.show()
