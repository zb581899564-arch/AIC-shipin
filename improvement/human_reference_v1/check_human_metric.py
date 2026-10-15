"""Hand-computed cases for real failure risks: segment IDs and frame mismatch."""
import numpy as np
from human_metrics import mean_pairwise

if __name__ == '__main__':
    # Two judges select disjoint halves; positive integers are segment IDs.
    labels = np.array([[7, 0], [7, 0], [0, 4], [0, 4]])
    value = mean_pairwise([1, 1, 0, 0], labels)
    assert value['user_f1'] == [1, 0] and value['f1'] == .5
    assert value['recall'] == value['precision'] == .5
    assert mean_pairwise([0, 0, 0, 0], labels)['f1'] == 0
    assert mean_pairwise([1, 1, 1, 1], labels)['f1'] == 2/3
    try:
        mean_pairwise([1, 1, 0], labels)
    except ValueError:
        pass
    else:
        raise AssertionError('Mismatched source frames silently repaired')
    print('PASS: independent hand metrics, positive segment IDs, empty prediction, frame-mismatch rejection')
