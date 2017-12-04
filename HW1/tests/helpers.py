import gzip
import random
import string
import unittest
from datetime import datetime
from string import Template
from typing import List
import subprocess
import os


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


class TestBaseClass(unittest.TestCase):

    def write_config_to_file(self):
        with open(self.path_to_config, 'w') as log:
            log.write(str(self.test_config).replace("'", '"'))

    def init_config(self):
        self.test_config = {
            "REPORT_SIZE": 10,
            "REPORT_DIR": self.report_dir,
            "REPORT_TEMPLATE":"{}/template.html".format(self.report_dir),
            "LOG_DIR": "/tmp".format(self.test_dir),
            "LOG_FILE": "{}/assets/analyzer.log".format(self.test_dir)
        }
        self.path_to_config = '{}/assets/local_conf.conf'.format(self.test_dir)
        self.write_config_to_file()

    def remove_file(self, file):
        if os.path.isfile(file):
            os.remove(file)

    def generate_report(self):
        subprocess.check_output("python3 {}/log_analyzer.py --config {}"
                                   .format(self.main_dir, self.path_to_config), shell=True)

    def setUp(self):
        # Initialization
        today = datetime.now().strftime("%Y.%m.%d")
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.main_dir = os.path.dirname(self.test_dir)
        self.report_dir = "{}/assets/reports".format(self.test_dir)
        self.path_to_daily_report = '{}/report-{}.html'.format(self.report_dir, today)
        self.log = None
        self.init_config()

    def tearDown(self):
        # Clear log
        if self.log and os.path.exists(self.log):
            self.remove_file(self.log)
        # Clean report
        if self.path_to_daily_report and os.path.exists(self.path_to_daily_report):
            self.remove_file(self.path_to_daily_report)


