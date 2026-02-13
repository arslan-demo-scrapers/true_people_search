import re

import usaddress
from nameparser import HumanName

from true_people_search.true_people_search.utils.text_utils import clean


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
