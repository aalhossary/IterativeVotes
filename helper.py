
def permute_identityless(bin_names: list, n_voters: int) -> list:
    """generate the exhaustive list of deterministic voters positions.

    :param bin_names: All available bins (empty or full). Typically they represent candidate names + intermediate gaps.
    :param n_voters:
    :return:
    """
    bin_load_permutations = __permute_bin_loads(len(bin_names), n_voters, n_voters, 0, [], set(), list())
    # print(ret)
    positions = []
    for line in bin_load_permutations:
        # Remember that the sum of a line = n_balls
        i = 0
        positions_permutation = []
        for bin in line:
            for voter in range(bin):
                positions_permutation.append(bin_names[i])
            i += 1
        positions.append(positions_permutation)
    return positions


def __permute_bin_loads(n_pins: int, n_balls: int, max_bin_load, level_index: int, partial_result: list = None,
                        history: set = None, ret: list = None) -> list:
    # print(level_index, ret)
    if level_index >= n_pins:
        # Control mirror images
        potential_result = tuple(partial_result)
        if potential_result in history:
            return ret
        ret.append(potential_result)
        history.add(potential_result)
        history.add(tuple(reversed(potential_result)))
        return ret

    reminder = n_balls - sum(partial_result[:level_index])
    for level_val in range(min(max_bin_load, reminder)+1):

        # control mirror images
        if level_index == 0 and level_val > n_balls / 2:
            return ret

        # last level can have only one value
        if level_index == n_pins - 1 and level_val != reminder:
            continue
        partial_result.append(level_val)
        __permute_bin_loads(n_pins, n_balls, max_bin_load, level_index + 1, partial_result, history, ret)
        partial_result.pop()
    return ret


if __name__ == '__main__':
    ret = __permute_bin_loads(2, 2, 2, 0, [], set(), [])
    print(ret)
    ret = __permute_bin_loads(4, 2, 2, 0, [], set(), [])
    print(ret)
    ret = __permute_bin_loads(2, 4, 4, 0, [], set(), [])
    print(ret)
    ret = __permute_bin_loads(10, 5, 1, 0, [], set(), [])
    print(ret)


    ret = permute_identityless(['a', 'b'], 2)
    print(ret)
    ret = permute_identityless(['a', 'b'], 3)
    print(ret)
    ret = permute_identityless(['a', 'b'], 4)
    print(ret)
    ret = permute_identityless(['a', 'b'], 5)
    print(ret)
    ret = permute_identityless(['a', 'b'], 6)
    print(ret)
    ret = permute_identityless(['a', 'b'], 7)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 3)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 4)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 5)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 6)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 4)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 5)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 6)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 7)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 8)
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 9)
    print(ret)
