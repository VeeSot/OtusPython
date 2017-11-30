import json
import os
import re
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# We make import after add dir to python-path
from HW1.tests.helpers import nginx_log_generator, nginx_log_gz_generator, TestBaseClass, generate_url_with_time_req


class TestAnalyzer(TestBaseClass):
    pattern = re.compile("var table = (?P<table_json>\[[^\]]*\])")

    def test_analyze_plain_log(self):
        """Base testing.Analyze plain log"""
        self.log = nginx_log_generator(total_url=30000)
        self.generate_report()
        self.assertTrue(os.path.isfile(self.path_to_daily_report), "Report doesn't exist")

        # Checking
        # Truncate to limit
        limit = self.test_config['REPORT_SIZE']

        # Extract JSON from HTML page

        with open(self.path_to_daily_report) as report:
            matches = self.pattern.search(report.read())

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
        with open(self.path_to_daily_report) as report:
            matches = self.pattern.search(report.read())

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


if __name__ == '__main__':
    unittest.main()
