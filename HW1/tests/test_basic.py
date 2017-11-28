import json
import os
import re
import subprocess
import sys
import unittest
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from HW1.tests.helpers import nginx_log_generator, nginx_log_gz_generator, generate_url_with_time_req


class TestAnalyzer(unittest.TestCase):
    def init_config(self):
        self.test_config = {
            "REPORT_SIZE": 10,
            "REPORT_DIR": self.report_dir,
            "LOG_DIR": "/tmp".format(self.test_dir),
            "LOG_FILE": "{}/assets/analyzer.log".format(self.test_dir)
        }
        self.path_to_config = '{}/assets/local_conf.conf'.format(self.test_dir)
        with open(self.path_to_config, 'w') as log:
            log.write(str(self.test_config).replace("'", '"'))

    def remove_file(self, file):
        if os.path.isfile(file):
            os.remove(file)

    def generate_report(self):
        subprocess.call("python3 {}/log_analyzer.py --config {}"
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
        self.remove_file(self.log)
        # Clean report
        self.remove_file(self.path_to_daily_report)

    def test_analyze_plain_log(self):
        """Base testing.Analyze plain log"""
        self.log = nginx_log_generator(total_url=30000)
        self.generate_report()
        self.assertTrue(os.path.isfile(self.path_to_daily_report), "Report doesn't exist")

        # Checking
        # Truncate to limit
        limit = self.test_config['REPORT_SIZE']

        # Extract JSON from HTML page
        pattern = re.compile("var table = (?P<table_json>\[[^\]]*\])")
        with open(self.path_to_daily_report) as report:
            matches = pattern.search(report.read())

        table_json = matches.group('table_json').replace("'", '"')
        table_json = json.loads(table_json)
        # Check size of reports
        self.assertEqual(len(table_json), limit, "Number of row in report not equals expected.{}!={}"
                         .format(len(table_json), limit))

    def test_analyze_gzip_log(self):
        """Analyzer can work with .gz logs"""
        self.log = nginx_log_gz_generator()
        self.generate_report()
        self.assertTrue(os.path.isfile(self.path_to_daily_report), "Report doesn't exist")

        # Checking
        # Truncate to limit
        limit = self.test_config['REPORT_SIZE']

        # Extract JSON from HTML page
        pattern = re.compile("var table = (?P<table_json>\[[^\]]*\])")
        with open(self.path_to_daily_report) as report:
            matches = pattern.search(report.read())

        table_json = matches.group('table_json').replace("'", '"')
        table_json = json.loads(table_json)
        # Check size of reports
        self.assertEqual(len(table_json), limit, "Number of row in report not equals expected.{}!={}"
                         .format(len(table_json), limit))

    def test_total_time_in_report(self):
        """Time in reports should be correct"""
        url2times = generate_url_with_time_req(total_url=20)
        self.log = nginx_log_generator(urls2time=url2times)
        self.generate_report()

        pattern = re.compile("var table = (?P<table_json>\[[^\]]*\])")
        with open(self.path_to_daily_report) as report:
            matches = pattern.search(report.read())

        # Extract JSON from HTML page
        table_json = matches.group('table_json').replace("'", '"')
        table_json = json.loads(table_json)

        # Check counting
        # Group time_requests by url
        groups_request = {}
        for u2t in url2times:
            url = u2t['url']
            time_execution = u2t['time']
            groups_request.setdefault(url, []).append(time_execution)

        # Count summary time request
        for url, time_execution in groups_request.items():
            total_time = sum(time_execution)
            groups_request[url] = total_time

        for request in table_json:
            url = request['url']
            total_time = request['time_sum']
            expected_time = round(groups_request[url], 3)
            self.assertEqual(total_time, expected_time)

    def test_recreate_report(self):
        """Report shouldn't be recreated"""
        path_to_log = '{}/assets/{}'.format(self.test_dir, 'analyzer.log')
        self.remove_file(path_to_log)  # For clean an experiment
        self.log = nginx_log_generator()
        self.generate_report()
        mtime = os.path.getmtime(self.path_to_daily_report)
        self.generate_report()
        new_mtime = os.path.getmtime(self.path_to_daily_report)
        self.assertEqual(mtime, new_mtime, "Report was recreated")
        # Check notification in log-file

        with open(path_to_log) as log_content:
            content = log_content.read()
            self.assertTrue('Daily report already exists' in content)


if __name__ == '__main__':
    unittest.main()
