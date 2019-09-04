
def permute_identityless(bin_names: list, n_voters: int, accepts_mirror_symmetry=False, ret: list = list()) -> list:
    """generate the exhaustive list of deterministic voters positions.

    :param bin_names: All available bins (empty or full). Typically they represent candidate names + intermediate gaps.
    :param n_voters:
    :param accepts_mirror_symmetry:
    :param ret:
    :return:
    """
    ret = __permute_bin_sizes(bin_names, len(bin_names), n_voters, 0, [], accepts_mirror_symmetry, ret)
    # print(ret)
    positions = []
    for line in ret:
        # remember that sum of line = n_voters
        i = 0
        positions_permutation = []
        for bin in line:
            for voter in range(bin):
                positions_permutation.append(bin_names[i])
            i += 1
        positions.append(positions_permutation)
    return positions


def __permute_bin_sizes(alphabet: list, n_pins: int, n_voters: int, level_index: int, partial_result: list = None,
                        accepts_mirror_symmetry=False, ret: list = None) -> list:
    # print(level_index, ret)
    if level_index >= n_pins:
        # Control mirror images
        if not accepts_mirror_symmetry:
            if tuple(reversed(partial_result)) in ret:
                return ret
        ret.append(tuple(partial_result))
        return ret

    reminder = n_voters - sum(partial_result[:level_index])
    for level_val in range(reminder+1):

        # control mirror images
        if not accepts_mirror_symmetry:
            if level_index == 0 and level_val > n_voters / 2:
                return ret

        # last level can have only one value
        if level_index == n_pins - 1 and level_val != reminder:
            continue
        partial_result.append(level_val)
        __permute_bin_sizes(alphabet, n_pins, n_voters, level_index + 1, partial_result, accepts_mirror_symmetry, ret)
        partial_result.pop()
    return ret


if __name__ == '__main__':
    ret = permute_identityless(['a', 'b'], 2, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b'], 3, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b'], 4, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b'], 5, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b'], 6, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b'], 7, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 3, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 4, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 5, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c'], 6, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 4, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 5, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 6, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 7, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 8, ret=list())
    print(ret)
    ret = permute_identityless(['a', 'b', 'c', 'd'], 9, ret=list())
    print(ret)
