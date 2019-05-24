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
        return (self.position, self.name) == (other.position, other.name)

    def __lt__(self, other):
        return (self.name, self.position).__lt__((other.name, other.position))

    def __hash__(self):
        return hash((self.name, self.position))

    def distance_to(self, other):
        if isinstance(other, Candidate):
            return abs(self.position - other.position)
        else:
            'assume other is a number (representing a position)'
            return abs(self.position - other)


all_candidates: list = []
#TODO fill all_candidates with candidates


if __name__ == '__main__':
    a: Candidate = Candidate()
    b: Candidate = Candidate('E', 5)
    print(a)
    print(b)

    print(a.__hash__())
    print(b.__hash__())
