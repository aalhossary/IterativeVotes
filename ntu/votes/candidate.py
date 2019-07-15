# from __future__ import annotations


class Candidate:

    __doc__ = "One of alternatives to be selected in the voting process"

    def __init__(self, name='', position=None):
        self.name = name
        self.position = position

    def __repr__(self):
        return f"{self.name}:{self.position}"

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        return (self.position, self.name) == (other.position, other.name)

    def __lt__(self, other):
        return (self.name, self.position).__lt__((other.name, other.position))

    def __hash__(self):
        return hash((self.name, self.position))

    def distance_to(self, other):
        if isinstance(other, Candidate):
            return abs(self.position - other.position)
        else:
            # Assume other is a number (representing a position)
            return abs(self.position - other)


if __name__ == '__main__':
    a: Candidate = Candidate()
    e: Candidate = Candidate('E', 5)
    print(a)
    print(e)

    print(a.__hash__())
    print(e.__hash__())

    a: Candidate = Candidate('A', 1)
    b: Candidate = Candidate('B', 2)
    c: Candidate = Candidate('C', 3)
    d: Candidate = Candidate('D', 4)
    e: Candidate = Candidate('E', 5)

    lst = [a, e, c, b, d, b, b, d, e]
    print(lst)
    lst.sort()
    print(lst)
