import json
from typing import List, Iterable

from implied_variables import tsgndpr


def single(variables: List):
    l = []
    k = len(variables)
    for i in range(k):
        for j in range(i + 1, k):
            l.append([-variables[i], -variables[j]])
    return l


def cardinality(variables: Iterable, k: int):
    import pysat.card
    result = pysat.card.CardEnc.atmost(lits=variables, bound=k, encoding=1)
    return result


def read_input(filename):
    def list_to_dict(sample_list):
        return {sample_list[i]: i + 1 for i in range(len(sample_list))}

    def read_groups(data):
        return list_to_dict(data["groups"])

    def read_rooms(data):
        rooms = data["rooms"]
        s_rooms = [number for room_list in rooms.values() for number in room_list]
        s_rooms_dict = list_to_dict(s_rooms)
        new_rooms = {}
        for room_type in rooms:
            new_rooms[room_type] = [s_rooms_dict[number] for number in rooms[room_type] if number in s_rooms_dict]
        return new_rooms, s_rooms_dict

    def read_plan(data):
        return data["plan"]

    def get_teachers_and_subjects_list(plan):
        teachers = list_to_dict(list(plan.keys()))
        subjects = set()
        group_lessons = {g: [] for g in groups.values()}
        teacher_lessons = {}
        for teacher, d in plan.items():
            teacher_lessons[teachers[teacher]] = {'lec': [], 'prac': [], 'lab': []}
            for subj in d:
                subjects.add(f"{subj['subject']}_{subj['subject_type']}")
        subjects = list_to_dict(list(subjects))
        for teacher, d in plan.items():
            teacher_id = teachers[teacher]
            for subj in d:
                type = subj["subject_type"]
                gr = [groups[idd] for idd in subj["groups"]]
                n_times = subj["times_in_a_week"]
                full_name = subjects[f"{subj['subject']}_{type}"]
                teacher_lessons[teacher_id][type].append((full_name, gr, n_times))
                for g in gr:
                    group_lessons[g].append((full_name, teacher_id, n_times))
        return teachers, subjects, group_lessons, teacher_lessons

    with open(filename, 'r') as file:
        data = json.load(file)
        groups = read_groups(data)
        rooms, original_rooms = read_rooms(data)
        plan = read_plan(data)
        teachers, subjects, group_lessons, teacher_lessons = get_teachers_and_subjects_list(plan)
    return groups, teachers, group_lessons, teacher_lessons, rooms, subjects, original_rooms