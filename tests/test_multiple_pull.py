import pytest as pt
import itertools as i

import kegg_pull.pull as p


expected_pull_calls = [
    ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9'],
    ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9'],
    ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
    ['D0', 'D1']
]

mock_entry_ids = list(i.chain.from_iterable(expected_pull_calls))

expected_successful_entry_ids = (
    'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
    'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'D0'
)

expected_failed_entry_ids = ('A9', 'B9', 'C9', 'D1')
expected_timed_out_entry_ids = ()
test_multiple_pull_data = [(p.SingleProcessMultiplePull, {}), (p.MultiProcessMultiplePull, {'n_workers': 2})]

# TODO: Test with force_single_pull with an entry field that can have multiple entries
# TODO: Test with an entry field that can only have one entry without force_single_pull
@pt.mark.parametrize('MultiplePull,kwargs', test_multiple_pull_data)
def test_multiple_pull(mocker, MultiplePull: type, kwargs: dict):
    mock_single_pull = MockSinglePull()

    if MultiplePull is p.SingleProcessMultiplePull:
        mock_single_pull.pull = mocker.MagicMock(wraps=MockSinglePull.pull)

    multiple_pull = MultiplePull(single_pull=mock_single_pull, **kwargs)
    multiple_pull_result: p.PullResult = multiple_pull.pull(entry_ids=mock_entry_ids)

    assert multiple_pull_result.successful_entry_ids == expected_successful_entry_ids
    assert multiple_pull_result.failed_entry_ids == expected_failed_entry_ids
    assert multiple_pull_result.timed_out_entry_ids == expected_timed_out_entry_ids

    if MultiplePull is p.SingleProcessMultiplePull:
        actual_pull_calls = getattr(mock_single_pull.pull, 'call_args_list')

        for actual_calls, expected_calls in zip(actual_pull_calls, expected_pull_calls):
            assert actual_calls.kwargs == {'entry_ids': expected_calls}


class MockSinglePull:
    def __init__(self):
        self.entry_field = None

    @staticmethod
    def pull(entry_ids: list):
        successful_entry_ids: list = tuple(entry_ids[:-1])
        failed_entry_ids: list = tuple(entry_ids[-1:])
        single_pull_result = p.PullResult()
        setattr(single_pull_result, '_successful_entry_ids', successful_entry_ids)
        setattr(single_pull_result, '_failed_entry_ids', failed_entry_ids)
        setattr(single_pull_result, '_timed_out_entry_ids', ())

        return single_pull_result
