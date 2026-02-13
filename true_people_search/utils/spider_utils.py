import logging
import time


def log_info(message):
    logging.info(f"{message}")


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
