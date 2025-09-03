
def _generate_candidates(L_k, k):
    """
    Generate candidate sequences of size k+1 from existing k-sequences.
    """

    C_k = []

    # When joining L1 with itself, all items should be added as part
    # of an itemset and as a separate element 
    if k == 2:
        for i in range(len(L_k)):
            for j in range(len(L_k)):
                if i == j:
                    continue
                # i-extension
                C_k.append([L_k[i][-1] + L_k[j][-1]]) 
                # s-extension
                C_k.append(L_k[i] + [L_k[j][-1]])

    # When k > 2
    else:
        for i in range(len(L_k)):
            for j in range(len(L_k)):
                if i == j:
                    continue
                # Subsequence check
                if not _join_check(L_k[i], L_k[j]):
                    continue
                # Create a new sequence
                new_item, multi = _get_element(L_k[j], pos=-1)
                if multi:
                    new_candidate = L_k[i][:-1] + [L_k[i][-1] + (new_item,)]
                else:
                    new_candidate = L_k[i] + [(new_item,)]
                if new_candidate not in C_k:
                    C_k.append(new_candidate)
    
    return C_k

def _join_check(s1, s2):
    """
    s1 joins with s2 if the subsequence obtained by dropping the first item of 
    s1 is the same as the subsequence obtained by dropping the last item of s2.
    """

    # s1
    first_element, multi = _get_element(s1, pos=0)
    s1_cut = _drop_item(s1, first_element, multi, 0)

    # s2
    last_element, multi = _get_element(s2, pos=-1)
    s2_cut = _drop_item(s2, last_element, multi, -1)
    
    # print(f'\ns1={s1}  ;  s1_cut={s1_cut}')
    # print(f's2={s2}  ;  s2_cut={s2_cut}')
    return s1_cut == s2_cut 

def _get_element(s, pos):
    """
    Get the pth element in a sequence.
    Also returns whether the element was part of an itemset of length > 1. 
    """

    # Create a flattened list along with information about tuple length
    flat_list = []
    for itemset in s:
        # Check if the tuple has more than one element
        is_multi = len(itemset) > 1  
        # Add to list
        flat_list.extend((item, is_multi) for item in itemset)
    
    # Access the element and its context at the specified position
    element, is_multi = flat_list[pos]
    return element, is_multi

def _drop_item(s, item, multi, pos):
    """
    Drop item from an itemset at a given position.
    """
    if multi:
        if pos == -1:
            return s[:pos] + [tuple(i for i in s[pos] if i != item)]
        return s[:pos] + [tuple(i for i in s[pos] if i != item)] + s[pos+1:]
    else:
        if pos == -1:
            return s[:pos]
        return s[:pos] + s[pos+1:]

def _prune_candidates(L_k, C_k, k):
    """
    Remove each candidate that contains a (k-1)-itemset that is not frequent.
    """

    # If k=2, all sequences are frequent
    if k == 2:
        return C_k
        
    pruned_candidates = []
    
    # Iterate over the candidates
    for candidate in C_k:
        valid = True

        # subseq = _contiguous_subsequences(candidate)
        # print('contiguous subsequences =', subseq)

        # Get continuous subsequences and check if they're frequent
        for subseq in _contiguous_subsequences(candidate):
            if subseq not in L_k:
                valid = False
                break
        
        if valid:
            pruned_candidates.append(candidate)

    return pruned_candidates



def _contiguous_subsequences(s):
    """
    Create all contiguous subsequences of a given sequence.
    Given a sequence s = <s1, ..., sn> and a subsequence c, c is a contiguous
    subsequence of s if any of the following conditions hold:
        1. c is derived from s by dropping an item from either s1 or sn.
        2. c is derived from s by dropping an item from an element si which has at least 
    2 items.
        3. c is a contiguous subsequence of c', and c' is a contiguous subsequence of s.
    
    Note that condition 3 is not used during the pruning step as a subsequence of a contiguous
    subsequence is of length k-2 and cannot be compared with the frequent sequence set L_{k-1}. 
    """

    # Condition 2
    for i_itemset, itemset in enumerate(s):
        # print(f'\t i_itemset={i_itemset}, itemset={itemset}')

        # Check itemset length
        l_itemset = len(itemset)
        if not l_itemset > 1:

            # Handle Condition 1: dropping from s1
            if i_itemset == 0:
                first_element, multi = _get_element(s, 0)
                yield _drop_item(s, first_element, multi, 0)
            
            # Handle Condition 1: dropping from sn
            elif i_itemset == len(s):
                last_element, multi = _get_element(s, pos=-1)
                yield _drop_item(s, last_element, multi, -1)
            
            # Conditions not met
            else:
                continue
    
        # Iterate over the items
        for i_item in range(l_itemset):
            # print(f'\t\ti_item={i_item}, itemset[i_item]={itemset[i_item]}')
            # print('\t\t subseq =', _drop_item(s, itemset[i_item], True, i_itemset))
            yield _drop_item(s, itemset[i_item], True, i_itemset)



if __name__ == '__main__':

    test = [
        [('1', '2'), ('3',)],
        [('1', '2'), ('4',)],
        [('1',), ('3', '4')],
        [('1', '3'), ('5',)],
        [('2',), ('3', '4')],
        [('2',), ('3',), ('5',)],
    ]

    candidates = _generate_candidates(test, k=4)
    print('\nall_candidates =', candidates, '\n')

    print('*** Test ***')
    for candidate in candidates:
        print('\t candidate:', candidate)
        print('\t -> contig seq =', list(_contiguous_subsequences(candidate)))

    candidates = _prune_candidates(test, candidates, 4)
    print('\npruned candidates =', candidates, '\n')



