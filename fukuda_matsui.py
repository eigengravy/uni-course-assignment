import json
import sys
import csv
import itertools

from tqdm import tqdm


def augment_bipartite_matching(g, m, u_cover=None, v_cover=None):
    level = set(g)
    level.difference_update(m.values())
    u_parent = {u: None for u in level}
    v_parent = {}
    while level:
        next_level = set()
        for u in level:
            for v in g[u]:
                if v in v_parent:
                    continue
                v_parent[v] = u
                if v not in m:
                    while v is not None:
                        u = v_parent[v]
                        m[v] = u
                        v = u_parent[u]
                    return True
                if m[v] not in u_parent:
                    u_parent[m[v]] = v
                    next_level.add(m[v])
        level = next_level
    if u_cover is not None:
        u_cover.update(g)
        u_cover.difference_update(u_parent)
    if v_cover is not None:
        v_cover.update(v_parent)
    return False


def max_bipartite_matching_and_min_vertex_cover(g):
    m = {}
    u_cover = set()
    v_cover = set()
    while augment_bipartite_matching(g, m, u_cover, v_cover):
        pass
    return m, u_cover, v_cover


def max_bipartite_matchings(g, m):
    if not m:
        yield {}
        return
    m_prime = m.copy()
    # print("mprime", m_prime)
    v, u = m_prime.popitem()
    g_prime = {w: g[w] - {v} for w in g if w != u}
    for m in max_bipartite_matchings(g_prime, m_prime):
        assert v not in m
        m[v] = u
        yield m
    g_prime_prime = {w: g[w] - {v} if w == u else g[w] for w in g}
    if augment_bipartite_matching(g_prime_prime, m_prime):
        yield from max_bipartite_matchings(g_prime_prime, m_prime)


def is_bipartite_matching(g, m):
    for v, u in m.items():
        if u not in g or v not in g[u]:
            return False
    return len(set(m.values())) == len(m)


def is_bipartite_vertex_cover(g, u_cover, v_cover):
    for u in g:
        if u in u_cover:
            continue
        for v in g[u]:
            if v not in v_cover:
                return False
    return True


def is_max_bipartite_matching(g, m, u_cover, v_cover):
    return (
        is_bipartite_matching(g, m)
        and is_bipartite_vertex_cover(g, u_cover, v_cover)
        and len(m) == len(u_cover) + len(v_cover)
    )


def brute_force_count_bipartite_matchings(g, k):
    g_edges = [(v, u) for u in g for v in g[u]]
    count = 0
    c = 0
    for m_edges in itertools.combinations(g_edges, k):
        m = dict(m_edges)
        c += 1
        if len(m) == k and is_bipartite_matching(g, m):
            count += 1
    print(c)
    return count


if __name__ == "__main__":
    profs = set()
    courses = set()

    prof2cat = dict()
    prof2course = dict()
    course2prof = dict()

    nodes = list()

    node2idx = dict()

    G = {}

    with open(sys.argv[1]) as f:
        for line in csv.reader(f):
            prof = line[0]

            profs.add(prof)
            courses.update(line[2:])

            prof2cat[prof] = line[1]
            prof2course[prof] = line[2:]

            for course in line[2:]:
                course2prof.setdefault(course, []).append(prof)

    for prof in profs:
        match prof2cat[prof]:
            case "x1":
                nodes.extend([prof])
                node2idx.setdefault(prof, []).extend(range(len(nodes))[-1:])
            case "x2":
                nodes.extend([prof] * 2)
                node2idx.setdefault(prof, []).extend(range(len(nodes))[-2:])
            case "x3":
                nodes.extend([prof] * 3)
                node2idx.setdefault(prof, []).extend(range(len(nodes))[-3:])

    for course in courses:
        nodes.extend([course, course])
        node2idx.setdefault(course, []).extend(range(len(nodes))[-2:])

    G = {
        idx: {
            course_node
            for course in (prof2course[node] if node in profs else course2prof[node])
            for course_node in node2idx[course]
        }
        for idx, node in enumerate(nodes)
    }

    m, u_cover, v_cover = max_bipartite_matching_and_min_vertex_cover(G)
    assert is_max_bipartite_matching(G, m, u_cover, v_cover), "no matchings found"
    allotments = list()
    count = 0
    for m_prime in tqdm(
        max_bipartite_matchings(G, m), total=int(sys.argv[2]), leave=False
    ):
        allotment = dict()
        for k, v in m_prime.items():
            if nodes[k] in courses:
                allotment.setdefault(nodes[k], set()).add(nodes[v])
        if allotment not in allotments:
            allotments.append(allotment)
        assert is_bipartite_matching(G, m_prime)
        assert len(m_prime) == len(m)
        count += 1
        # print(count)

        if (count) > int(sys.argv[2]):
            break

    def cost(allotment):
        c = 0
        for k in allotment.keys():
            for v in allotment[k]:
                c += prof2course[v].index(k)
        return c

    allotments.sort(key=cost)

    print("min cost", cost(allotments[0]), allotments[0])
    # print(len(allotments), allotments)

    json_object = json.dumps(
        [
            ({k: list(v) for k, v in allotment.items()}, cost(allotment))
            for allotment in allotments
        ],
        indent=4,
    )
    with open("output.json", "w") as outfile:
        outfile.write(json_object)

    # c = brute_force_count_bipartite_matchings(G, len(m))
    # print(c)
    # assert c == count
