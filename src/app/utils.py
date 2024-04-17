import json
from typing import List, Iterable

from implied_variables import assumption_hash, MOD


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
    return list(result)


class Reader:
    clauses = []
    assumptions = []

    @classmethod
    def read_input(cls, filename):
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

        def read_constraints(data, groups, teachers):

            def switch_name(given_name, arguments):
                cl = []
                match given_name:
                    case 'groups_overlapping':
                        from src.app.constraints import Group
                        cl = Group.groups_overlapping(groups[arguments['group_1']], groups[arguments['group_2']])
                    case 'teachers_overlapping':
                        from src.app.constraints import Teacher
                        cl = Teacher.teachers_overlapping(teachers[arguments['teacher_1']],
                                                          teachers[arguments['teacher_2']])
                    case 'number_of_teaching_days':
                        from src.app.constraints import Teacher
                        cl = Teacher.number_of_teaching_days(teachers[arguments['teacher']], arguments['number'])
                    case 'forbidden_period_for_teacher':
                        from src.app.constraints import Teacher
                        cl = Teacher.forbidden_period_for_teacher(teachers[arguments['teacher']], arguments['day'],
                                                                  arguments['period'])
                    case 'forbidden_period_for_group':
                        from src.app.constraints import Group
                        cl = Group.forbidden_period_for_group(groups[arguments['group']], arguments['day'],
                                                              arguments['period'])
                    case 'forbidden_day_for_teacher':
                        from src.app.constraints import Teacher
                        cl = Teacher.forbidden_day_for_teacher(teachers[arguments['teacher']], arguments['day'])
                    case 'forbidden_day_for_group':
                        from src.app.constraints import Group
                        cl = Group.forbidden_day_for_group(groups[arguments['group']], arguments['day'])
                assumption_h = assumption_hash(cl) % MOD
                # cls.assumptions.append(assumption_h)
                cls.clauses.extend(cl)
                # cls.clauses.extend(to_cnf.do(assumption_h, cl))
                # cls.clauses.append([assumption_h])

            constraints_list = data["constraints"]
            for d in constraints_list:
                switch_name(d['name'], d['args'])

        def get_teachers_and_subjects_list(plan):
            teachers = set()
            for i in plan:
                teachers.add(i["teacher"])
            teachers = list_to_dict(list(teachers))
            subjects = set()
            group_lessons = {g: [] for g in groups.values()}
            teacher_lessons = {}
            for d in plan:
                teacher = d['teacher']
                teacher_lessons[teachers[teacher]] = {'lec': [], 'prac': [], 'lab': []}
                subjects.add(f"{d['subject']}_{d['subject_type']}")
            subjects = list_to_dict(list(subjects))
            for d in plan:
                teacher = d['teacher']
                teacher_id = teachers[teacher]
                type = d["subject_type"]
                gr = [groups[idd] for idd in d["groups"]]
                n_times = d["times_in_a_week"]
                full_name = subjects[f"{d['subject']}_{type}"]
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
            read_constraints(data, groups, teachers)
        return cls.clauses, groups, teachers, group_lessons, teacher_lessons, rooms, subjects, original_rooms, cls.assumptions
