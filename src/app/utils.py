import json
from typing import List, Iterable

from implied_variables import assumption_hash, MOD

exact_teachers = {}
exact_groups = {}
exact_rooms = {}


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

    teachers: None
    subjects: None
    group_lessons: None
    teacher_lessons: None
    original_rooms: None

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
                        from constraints import Group
                        cl = Group.groups_overlapping(groups[arguments['group_1']], groups[arguments['group_2']])
                    case 'teachers_overlapping':
                        from constraints import Teacher
                        cl = Teacher.teachers_overlapping(teachers[arguments['teacher_1']],
                                                          teachers[arguments['teacher_2']])
                    case 'number_of_teaching_days':
                        from constraints import Teacher
                        cl = Teacher.number_of_teaching_days(teachers[arguments['teacher']], arguments['number'])
                    case 'forbidden_period_for_teacher':
                        from constraints import Teacher
                        cl = Teacher.forbidden_period_for_teacher(teachers[arguments['teacher']], arguments['day'],
                                                                  arguments['period'])
                    case 'forbidden_period_for_group':
                        from constraints import Group
                        cl = Group.forbidden_period_for_group(groups[arguments['group']], arguments['day'],
                                                              arguments['period'])
                    case 'forbidden_day_for_teacher':
                        from constraints import Teacher
                        cl = Teacher.forbidden_day_for_teacher(teachers[arguments['teacher']], arguments['day'])
                    case 'forbidden_day_for_group':
                        from constraints import Group
                        cl = Group.forbidden_day_for_group(groups[arguments['group']], arguments['day'])
                    case 'exact_time':
                        from constraints import Lesson
                        cl = []
                        # grs = list(groups[i] for i in arguments['groups'])
                        for i in arguments['groups']:
                            g = groups[i]
                            t = teachers[arguments['teacher']]
                            s = subjects[arguments['subject']]
                            d = arguments['day']
                            p = arguments['period']
                            r = original_rooms[arguments['room']]
                            cl.extend(Lesson.exact_time_for_lesson(t=t,
                                                                   s=s,
                                                                   g=g,
                                                                   d=d,
                                                                   p=p,
                                                                   r=r))
                            if g not in exact_groups:
                                exact_groups[g] = set()
                            if t not in exact_teachers:
                                exact_teachers[t] = set()
                            if r not in exact_rooms:
                                exact_rooms[r] = set()
                            exact_teachers[t].add((d, p))
                            exact_groups[g].add((d, p))
                            exact_rooms[r].add((d, p))
                            # for j in group_lessons[g]:
                            #     if j[1] == g:
                            #         j[2] -= 1
                            # group_lessons[g][2] -= 1
                        # for j in te+++--+-002222222222222222222222222222222222222+2222222+acher_lessons[teachers[arguments['teacher']]].values():
                        #     for k in j:
                        #         if sorted(k[1]) == sorted(grs):
                        #             k[2] -= 1

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
                teacher_lessons[teacher_id][type].append([full_name, gr, n_times])
                for g in gr:
                    group_lessons[g].append([full_name, teacher_id, n_times])
            return teachers, subjects, group_lessons, teacher_lessons

        with open(filename, 'r') as file:
            data = json.load(file)
            groups = read_groups(data)
            rooms, original_rooms = read_rooms(data)
            cls.original_rooms = original_rooms
            plan = read_plan(data)
            teachers, subjects, group_lessons, teacher_lessons = get_teachers_and_subjects_list(plan)
            # print(group_lessons, '\n', teacher_lessons)
            read_constraints(data, groups, teachers)
        return cls.clauses, groups, teachers, group_lessons, teacher_lessons, rooms, subjects, original_rooms, cls.assumptions
