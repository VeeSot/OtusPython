import gzip
import random
import string
from datetime import datetime
from string import Template
from typing import List


def nginx_row_generator(params: dict):
    template = '127.0.0.1 -  - [30/Jun/2017:01:09:02 +0300] "GET $url HTTP/1.1" 200 19415 "-" "User-Agent" "-" ' \
               '"00000000-0000-0000-0000-000000000000" "any_tag" $time\n'
    row = Template(template)
    return row.safe_substitute(params)


def get_part_of_url():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(random.randint(1, 8)))


def generate_url_with_time_req(total_url=2000)->List[dict]:
    total_parts_of_url = 3
    rows = []
    start = 1
    end = 20

    for number in range(total_url):
        url_parts = ['/{}'.format(get_part_of_url()) for _ in range(total_parts_of_url)]
        url = ''.join(url_parts)
        total_requests = range(random.randint(start, end))
        for request in total_requests:
            if request % 10:#Add some interger time
                request_time = random.uniform(start, end)
            else:
                request_time = random.randint(start, end)
            about_request = {'url': url, 'time': request_time}
            rows.append(about_request)

    return rows


def nginx_log_generator(total_url=2000, urls2time=None):
    "Is made simple nginx file using template and "
    today = datetime.strftime(datetime.now(), '%Y%m%d')
    log_name = '/tmp/nginx-access-ui.log-{}'.format(today)

    if not urls2time:
        urls2time = generate_url_with_time_req(total_url=total_url)
    random.shuffle(urls2time)

    with open(log_name, 'w') as log:
        for row in urls2time:
            nginx_row = nginx_row_generator(row)
            log.write(nginx_row)
    return log_name


def nginx_log_gz_generator(total_url=2000):
    log_file = nginx_log_generator(total_url=total_url)
    gz_file = log_file + '.gz'
    with gzip.open(gz_file, 'wb') as gz:
        with open(log_file, 'r') as log:
            gz.write(log.read().encode())
    return gz_file
