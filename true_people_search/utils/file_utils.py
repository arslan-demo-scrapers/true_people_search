from csv import DictReader

from true_people_search.true_people_search.utils.spider_utils import log_info


def get_phone_cols(start=1, stop=15):
    return [f"phone number {i}" for i in range(start, stop + 1)]


def get_csv_rows(file_name):
    persons = [dict(r) for r in DictReader(open(f'../input/{file_name}', encoding='utf-8')) if r]
    if not persons:
        log_info(f"{file_name} FILE EMPTY!")
    return persons
