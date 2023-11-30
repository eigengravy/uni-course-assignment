import json
import networkx as nx
import numpy as np

# Open the JSON file



def min_weight_matching(file_path):
    course_dictionary = {} #course and number
    prof_dictionary = {} #prof and number
    prof_preference_list = {} #prof and their preference lisr

    with open(file_path, 'r') as file:
    # Load the JSON data into a Python dictionary
        data = json.load(file)

    if data:
        for row in data:
            # Each row is a list representing the columns in that row
            prof_name = row["name"]
            prof_category = row["category"]
            preference_order = row["preference_order"]

            prof1 = prof_name + "_1"
            prof2 = prof_name + "_2"
            prof3 = prof_name + "_3"

            prof_preference_list[prof1] = preference_order
            prof_preference_list[prof2] = preference_order
            prof_preference_list[prof3] = preference_order

            #Adding asigning prof to indices
            if prof1 not in prof_dictionary.keys():
                n = len(prof_dictionary)
                if prof_category == 1.5:
                    prof_dictionary[prof1] = n
                    prof_dictionary[prof2] = n+1
                    prof_dictionary[prof3] = n+2
                elif prof_category == 1:
                    prof_dictionary[prof1] = n
                    prof_dictionary[prof2] = n+1
                elif prof_category == 0.5:
                    prof_dictionary[prof1] = n

            #adding courses to course dictionary
            for course in preference_order:
                course1 = course + "_1"
                course2 = course + "_2"
                if course1 not in course_dictionary.keys():
                    m = len(course_dictionary)
                    course_dictionary[course1] = m
                    course_dictionary[course2] = m+1

    #make adjacency matrix -> need to write the code for check too
    rows_prof = len(prof_dictionary)
    cols_courses = len(course_dictionary)

    adjacency_matrix = np.full((rows_prof, cols_courses), float("inf"))

    for prof in prof_dictionary:
        preference_order = prof_preference_list[prof]
        prof_row = prof_dictionary[prof]
        weight = 1
        for course in preference_order:
            course1 = course + "_1"
            course2 = course + "_2"
            course_col1 = course_dictionary[course1]
            course_col2 = course_dictionary[course2]

            adjacency_matrix[prof_row][course_col1] = weight
            adjacency_matrix[prof_row][course_col2] = weight

            weight += 1

    #creating edge list using adjacency matrix:
    edges = []
    for i in range(len(adjacency_matrix)):
        for j in range(len(adjacency_matrix[0])):
            row = i
            col = j + len(adjacency_matrix)
            weight = adjacency_matrix[i][j]
            if weight == float("inf"):
                continue

            edges.append((row, col, weight))


    G = nx.Graph()
    G.add_weighted_edges_from(edges)
    matches = sorted(nx.min_weight_matching(G))

    def get_prof_name(index):
        for prof in prof_dictionary:
            if prof_dictionary[prof] == index:
                return prof

    def get_course_name(index):
        for course in course_dictionary:
            if course_dictionary[course] == index:
                return course

    #matching allotments to indices
    prof_allotments = {}

    score = 0
    for e in matches:
        prof_row = min(e)
        course_row = max(e) - len(adjacency_matrix)

        prof_name = get_prof_name(prof_row)[:-2]
        course_name = get_course_name(course_row)[:-2]
        score += adjacency_matrix[prof_row][course_row]

        if prof_name in prof_allotments.keys():
            if course_name not in prof_allotments[prof_name]:
                prof_allotments[prof_name].append(course_name)
        else:
            prof_allotments[prof_name] = [course_name]

    if score == float("inf"):
        return {"Crashed": "Algorihtm failed to find any minimum weighted matchings"}

    prof_allotments["Minimum Sum of Weights"] = score
    return prof_allotments

if __name__ == "__main__":
    print(min_weight_matching("./exps/run2/input2.json"))