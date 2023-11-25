import pysat.solvers
from pysat.formula import CNF

from implied_variables import map_tsgndpr
from utils import read_input


class Algorithm:
    def __init__(self, filename):
        (self.groups, self.teachers, self.group_lessons, self.teacher_lessons, self.rooms,
         self.subjects, self.original_rooms) = read_input(filename)

    def calculate(self):
        from requirements import Correctness
        room_requirements = Correctness(self.teachers, self.original_rooms, self.rooms, self.teacher_lessons)
        from requirements import Mixed
        mixed_requirements = Mixed(self.teachers, self.teacher_lessons, self.group_lessons, self.original_rooms,
                                   self.rooms)
        cnf = CNF()
        clauses = room_requirements.room_all() + mixed_requirements.mixed_all()
        cnf.from_clauses(clauses)
        solver = pysat.solvers.Glucose4()
        solver.append_formula(cnf)
        print(solver.solve())
        print(len(clauses))
        model = solver.get_model()
        self._print_input(model)

    def _print_input(self, model):
        def _format(collection, target):
            for k, v in collection.items():
                if v == target:
                    return k

        res = []
        for i in model:
            if i > 0 and i in map_tsgndpr:
                var = map_tsgndpr[i]
                if (t := var[0]) in self.teachers.values() and (l := var[1]) in self.subjects.values() and (g := var[
                    2]) in self.groups.values() and var[-3] != 0 and var[-2] != 0 and var[-1] != 0:
                    r = [_format(self.teachers, t), _format(self.subjects, l), _format(self.groups, g), var[-3],
                         var[-2], _format(self.original_rooms, var[-1])]
                    res.append(r)
        res.sort(key=lambda x: (x[3], x[4]))
        d = {}
        for i in res:
            if (i[0], i[1], i[3], i[4], i[5]) not in d:
                d[(i[0], i[1], i[3], i[4], i[5])] = []
            d[(i[0], i[1], i[3], i[4], i[5])].append(i[2])
        for i in sorted(d.items(), key=lambda x: (x[0][2], x[0][3])):
            print(i)


if __name__ == '__main__':
    Algorithm("config_example.json").calculate()
