import re
from copy import deepcopy
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.crawler import CrawlerProcess

from true_people_search.true_people_search.services.proxy_service import build_proxy_url
from true_people_search.true_people_search.utils.file_utils import get_phone_cols, get_csv_rows
from true_people_search.true_people_search.utils.parsing_utils import get_name_parts, get_address_parts
from true_people_search.true_people_search.utils.spider_utils import log_info, retry_invalid_response
from true_people_search.true_people_search.utils.text_utils import clean


class TruePeopleSearchSpider(Spider):
    name = 'true_people_search_spider'
    input_persons_file_path = 'PERSONS.csv'
    base_url = 'https://www.truepeoplesearch.com'
    address_t = '{street address}_{city}_{state}_{zip code}'
    person_url_t = "/results?name={name}&citystatezip={address}"
    search_url_t = '/find/{last name}/{first name}/area/{zip code}/'

    punctuation_re = re.compile(r'[^\w \-]')

    csv_headers = [
        "name", "full name", "aka", "sur names", "age", "owners", "emails",
        "full address", "street address", "city", "state", "zip code", *get_phone_cols(),
    ]

    feeds = {
        '../output/tps_results.json': {
            'format': 'json',
            'encoding': 'utf8',
            'store_empty': False,
            'fields': csv_headers,
            'overwrite': True,
            'indent': 4,
        }
    }

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 5,
        'FEEDS': feeds,
    }

    handle_httpstatus_list = [
        400, 401, 402, 403, 404, 405, 406, 407, 409, 412,
        500, 501, 502, 503, 504, 505, 506, 507, 509,
    ]

    meta = {
        'dont_merge_cookies': True,
        'handle_httpstatus_list': handle_httpstatus_list
    }

    headers = {
        'authority': 'www.truepeoplesearch.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-US,en;q=0.9',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def start(self):
        yield Request("https://quotes.toscrape.com/", dont_filter=True)

    def parse(self, response, **kwargs):
        return self.search_persons(self.input_persons_file_path)

    def search_persons(self, file_path):
        for person in self.get_persons(file_path)[:1]:
            if not person or not clean(person['NAME']):
                continue
            person['name'] = person.pop('NAME').strip()

            meta = deepcopy(self.meta)
            meta['person'] = person

            temp = get_name_parts(person['name'])
            temp['zip code'] = person['ADDRESS']
            url = urljoin(self.base_url, self.search_url_t.format(**temp).lower())
            yield Request(self.get_proxy_url(url), callback=self.parse_listing, meta=meta,
                          headers=self.headers, priority=-100)

    @retry_invalid_response
    def parse_listing(self, response):
        if 'This record is no longer available.' in response.text:
            print(self.get_page_title(response))
            print(f"This record is no longer available. \nSkipping Person: \n{response.meta['person']}")
            return

        for record_sel in response.css('.card.card-body'):
            if self.get_person_details_url(record_sel).rstrip('/') == self.base_url.rstrip('/'):
                continue
            person = deepcopy(response.meta['person'])
            person.update(get_name_parts(self.get_fullname(record_sel)))
            person.update(self.get_phones(record_sel))

            person['age'] = self.get_age(record_sel)
            person['aka'] = ', '.join(self.get_also_know_as(record_sel))
            person['sur names'] = self.get_sur_names(person, record_sel)
            person['addresses'] = self.get_addresses(record_sel)
            person['emails'] = self.get_emails(record_sel)

            if 'This record is no longer available.' in record_sel.get() or 'deceased' in record_sel.get().lower():
                log_info(f"Person has been Deceased. Skipping Person:\n{person}")
                continue

            meta = deepcopy(response.meta)
            meta['person'] = person

            yield Request(self.get_proxy_url(self.get_person_details_url(record_sel)),
                          callback=self.parse_person, meta=meta, headers=self.headers, priority=-100)

    @retry_invalid_response
    def parse_person(self, response):
        person = response.meta['person']
        addresses = self.get_addresses(response)

        if self.get_phones(response):
            person.update(self.get_phones(response))
        if not person['age']:
            person['age'] = self.get_age_from_details_page(response)
        if not person['aka']:
            person['aka'] = self.get_also_seen_as(response)

        person['emails'] = self.get_emails(response)
        person['addresses'] = addresses if addresses else person['addresses']
        return [{**person, **address} for address in person.pop('addresses')]

    def get_proxy_url(self, url):
        return build_proxy_url(url)

    def get_fullname(self, record_sel):
        return clean(record_sel.css('.content-header::text').get())

    def get_phones(self, response):
        phones = [p for p in response.css('[data-link-to-more="phone"] ::text').getall() if clean(p)]
        return {f'phone number {i + 1}': p for i, p in enumerate(phones)}

    def get_age(self, record_sel):
        return clean(record_sel.css('span:contains("Age") + span::text').get())

    def get_also_know_as(self, record_sel):
        return record_sel.css('[data-link-to-more="aka"] span::text').getall()

    def get_sur_names(self, person, record_sel):
        surnames = {get_name_parts(n)['last name'] for n in self.get_also_know_as(record_sel)}
        surnames.add(get_name_parts(person['name'])['last name'])
        return ', '.join(sn for sn in surnames if clean(sn))

    def get_addresses(self, response):
        seen = []
        addresses = []

        for address_sel in response.css('[data-link-to-more="address"]'):
            address_item = get_address_parts(self.get_address(address_sel))
            if self.address_t.format(**address_item).lower() in seen:
                continue
            seen.append(self.address_t.format(**address_item).lower())

            if not all([address_item['street address'], address_item['city'], address_item['state']]):
                continue
            address_item['city, state'] = f'{address_item["city"]}, {address_item["state"]}'
            address_item['full address'] = self.get_full_address(address_item)

            addresses.append(address_item)

        return addresses

    def get_person_details_url(self, selector):
        return urljoin(self.base_url, selector.css('.link-to-more::attr(href)').get())

    def get_address(self, address_sel):
        return ', '.join(address_sel.css('::text').getall())

    def get_full_address(self, address):
        return "{street address}, {city}, {state}, {zip code}".format(**address)

    def get_age_from_details_page(self, response):
        return response.css('#personDetails::attr(data-age)').get('') or self.get_age(response.text)

    def get_also_seen_as(self, response):
        return [aka for e in response.css('.row:contains("Also Seen As") + .row ::text').getall()
                if (aka := clean(e)) and len(aka) > 1]

    def get_emails(self, response):
        emails = response.css('.col div:contains("@")::text').getall()
        return ', '.join([e.strip() for e in emails if clean(e)])

    def get_page_title(self, response):
        return clean(response.css('title::text').get())

    def get_persons(self, file_path):
        return get_csv_rows(file_path)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(TruePeopleSearchSpider)
    process.start()
