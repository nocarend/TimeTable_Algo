import pysat.solvers
from pysat.formula import CNF, WCNF

from constraints import checker
from implied_variables import map_tsgndpr, map_iktdp, map_lkgd
from utils import Reader


class Algorithm:
    clauses = []

    def __init__(self, filename):
        (self.clauses, self.groups, self.teachers, self.group_lessons, self.teacher_lessons, self.rooms,
         self.subjects, self.original_rooms, self.assumptions) = Reader.read_input(filename)

    def calculate(self):

        from requirements import Correctness
        room_requirements = Correctness(self.teachers, self.original_rooms, self.rooms, self.teacher_lessons)
        from requirements import Mixed
        mixed_requirements = Mixed(self.teachers, self.teacher_lessons, self.group_lessons, self.original_rooms,
                                   self.rooms)
        cnf = CNF()
        assumptions = []
        clauses_copy = self.clauses.copy()
        for i in clauses_copy:
            for j in i:
                assumptions.append(abs(j))
        self.clauses.extend(room_requirements.room_all() + mixed_requirements.mixed_all())
        cnf.from_clauses(self.clauses)
        solver = pysat.solvers.Glucose4()
        solver.append_formula(cnf)
        if solver.solve(assumptions=self.assumptions):
            self._print_input(solver.get_model())
        else:
            self._print_unsatisfiable()
        print(f"Number of clauses: {len(self.clauses)}", file=sys.stderr)

    def _print_input(self, model):
        print('SUCCESSFULLY')

        def _simple_print(d):
            for i in sorted(d.items(), key=lambda x: (x[0][2], x[0][3])):
                print(i)

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
        _simple_print(d)
        import sys
        sys.stdout = open('algorithm_output.txt', 'w')
        _simple_print(d)

    def _print_unsatisfiable(self):
        def get_swap_dict(d):
            return {v: k for k, v in d.items()}

        print('FAILED')
        s = ['Teacher', 'Subject', 'Group', 'Times in a week', 'Day', 'Period', 'Room']
        ss = [get_swap_dict(self.teachers), get_swap_dict(self.subjects), get_swap_dict(self.groups), range(0, 8),
              range(0, 10), range(0, 100), get_swap_dict(self.original_rooms)]
        from pysat.examples.musx import MUSX
        wcnf = WCNF()
        for i in self.clauses:
            wcnf.append(i, weight=1)
        musx = MUSX(wcnf, verbosity=0)
        r = musx.compute()
        for i in r:
            if i in map_tsgndpr.keys():
                v = map_tsgndpr[i]
                print("Problem with ", end='')
                for k in range(len(v)):
                    # print(v[k])
                    if v[k] > 0:
                        print(f'{s[k]}: {ss[k][v[k]]}', end='')
                    if k == len(v) - 1:
                        print()
                    elif v[k] > 0:
                        print(', ', end='')
        # checker(r, self.assumptions)


if __name__ == '__main__':
    import sys
    import time

    args = sys.argv
    filename = "../resources/config_example.json"
    if len(args) > 1:
        filename = args[1]
    start = time.time()
    Algorithm(filename).calculate()
    end = time.time()
    print(f"Time: {end - start}", file=sys.stderr)
    # создать массив forbidden time, где будут периоды и дни, в которые для данного препода ничего не генерируется
    # Для остальных это время в данном кабинете и группе будет запрещено
