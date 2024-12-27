
from itertools import combinations


def gen(L_k, k):
    """
    Candidate generation.
    """
    C_k = []
    
    for i in range(len(L_k)):
        print(f'\ni={i}, L_k[i]={L_k[i]}')
        for j in range(len(L_k)):
            print(f'\tj={j}, L_k[j]={L_k[j]}')
            # Compare all but the last element of sequences i and j
            if i != j and L_k[i][:-1] == L_k[j][:-1]:
                # Create a new sequence
                new_candidate = L_k[i] + [L_k[j][-1]]
                print('\t\t added new candidate =', new_candidate)
                if new_candidate not in C_k:
                    C_k.append(new_candidate)
    
    return C_k

if __name__ == '__main__':

    L_k = [
        [set('1'), set('2'), set('3')],
        [set('1'), set('2'), set('4')],
        [set('1'), set('3'), set('4')],
        [set('1'), set('3'), set('5')],
        [set('2'), set('3'), set('5')],
    ]

    test = gen(L_k, k=4)
    print(test)