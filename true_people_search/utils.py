import logging
import re
import time
from csv import DictReader
from html import unescape

import usaddress
from nameparser import HumanName


def get_name_parts(name):
    name_parts = HumanName(name)
    punctuation_re = re.compile(r'[^\w-]')

    return {
        'full name': name.strip(),
        # 'prefix': re.sub(punctuation_re, '', name_parts.title),
        'first name': re.sub(punctuation_re, '', name_parts.first),
        # 'middle name': re.sub(punctuation_re, '', name_parts.middle),
        'last name': re.sub(punctuation_re, '', name_parts.last),
        # 'suffix': re.sub(punctuation_re, '', name_parts.suffix)
    }


def clean(text):
    if isinstance(text, (int, float)):
        return text

    text = unescape(text or '')
    for c in ['\r\n', '\n\r', u'\n', u'\r', u'\t', u'\xa0', '...']:
        text = text.replace(c, ' ')
    return re.sub(' +', ' ', text).strip()


def clean_all(seq):
    return [clean(e) for e in seq if clean(e)]


def get_phone_cols(start=1, stop=15):
    return [f"phone number {i}" for i in range(start, stop + 1)]


def log_info(message):
    logging.info(f"{message}")
    # print(message)


def retry_invalid_response(callback):
    def wrapper(spider, response):
        if response.status >= 400:
            if response.status == 404:
                log_info('Person not found.')
                return

            retry_times = response.meta.get('retry_times', 0)
            if retry_times < 3:
                time.sleep(7)
                response.meta['retry_times'] = retry_times + 1
                return response.request.replace(dont_filter=True, meta=response.meta)

            log_info("Dropped after 3 retries. url: {}".format(response.url))
            response.meta.pop('retry_times', None)

            person = response.meta['person']

            if 'addresses' in person:
                records = []
                for address in person['addresses']:
                    person.update(address)
                    records.append(person)

                # return [{**person, **address} for address in person['addresses']]
                return records
            else:
                return response.meta['person']
        return callback(spider, response)

    return wrapper


def get_csv_rows(file_name):
    persons = [dict(r) for r in DictReader(open(f'../input/{file_name}', encoding='utf-8')) if r]
    if not persons:
        log_info(f"{file_name} FILE EMPTY!")
    return persons


def get_address_parts(address):
    if not address:
        return {}
    address1, city, state, zip_code = '', '', '', ''

    for value, key in usaddress.parse(address):
        value = value.replace(',', '') + ' '
        if key in ['OccupancyIdentifier', 'Recipient']:
            continue
        if key == 'PlaceName':
            if len(value.strip()) == 2:
                continue
            city += value
        elif key == 'StateName':
            state += value
        elif key == 'ZipCode':
            zip_code += value
        else:
            address1 += value

    address_item = {}
    address_item['street address'] = clean(address1)
    address_item['city'] = clean(city)
    address_item['state'] = state.strip().upper()
    address_item['zip code'] = zip_code.strip()
    return address_item
