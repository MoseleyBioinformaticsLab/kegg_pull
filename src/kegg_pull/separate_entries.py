def separate_entries(res: str, entry_field: str) -> list:
    if entry_field is None:
        separator = _standard_separator
    else:
        separator = _field_to_separator[entry_field]

    entries: list = separator(res=res)
    entries = [entry.strip() for entry in entries]

    return entries


def _gene_separator(res: str) -> list:
    return res.split('>')[1:]


def _mol_separator(res: str) -> list:
    return _split_and_remove_last(res=res, sep='$$$$')


def _split_and_remove_last(res: str, sep: str) -> list:
    return res.split(sep)[:-1]


def _standard_separator(res: str) -> list:
    return _split_and_remove_last(res=res, sep='///')


_field_to_separator = {
    'aaseq': _gene_separator, 'kcf': _standard_separator, 'mol': _mol_separator, 'ntseq': _gene_separator
}
