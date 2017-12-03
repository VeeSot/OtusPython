import os
import re
import subprocess
import unittest
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# We make import after add dir to python-path
from HW1.tests.helpers import nginx_log_generator, nginx_log_gz_generator, TestBaseClass


class TestError(TestBaseClass):
    def check_in_log(self, text):
        path_to_log = '{}/assets/{}'.format(self.test_dir, 'analyzer.log')
        with open(path_to_log) as f:
            log_content = f.read()
        return text in log_content

    def test_log_dir(self):
        """Log dir should be exists"""
        false_dir = '/tmp/any'
        self.test_config['LOG_DIR'] = false_dir
        self.write_config_to_file()
        self.log = nginx_log_generator()
        self.generate_report()
        # Check our log
        path_to_log = '{}/assets/{}'.format(self.test_dir, 'analyzer.log')
        with open(path_to_log) as f:
            log_content = f.read()
        self.assertTrue("Sorry, directory {} wasn't found".format(false_dir) in log_content)

    def test_logs(self):
        """Logs should be exist in LOG DIR"""
        # Purge all logs
        log_dir = self.test_config['LOG_DIR']
        pattern = re.compile('^nginx-access-ui.log-(?P<day_of_log>\d{8})(\.gz)?$')
        logs = [f for f in os.listdir(log_dir) if re.search(pattern, f)]
        map(os.remove, logs)

        # Try to make report without logs
        self.generate_report()
        self.assertTrue(self.check_in_log("Not found logs in directory {}".format(self.test_config['LOG_DIR'])))

    def test_broken_config(self):
        """Config is broken"""

        self.test_config = ""
        self.write_config_to_file()

        # Firstly.We have a notification about reson
        process = subprocess.Popen("python3 {}/log_analyzer.py --config {}"
                                   .format(self.main_dir, self.path_to_config),
                                   stderr=subprocess.PIPE, shell=True)
        response = process.communicate()
        errors = response[1].decode()
        self.assertTrue('check your config' in errors)

        # Secondly. We've have exception
        with self.assertRaises(subprocess.CalledProcessError) as context:
            self.generate_report()
            self.assertTrue(False)  # This never will execute
        self.assertTrue(1, context.exception.returncode)  # Script was halted

    def test_uncorrect_record_in_log(self):
        """Check garbage serving"""
        self.log = nginx_log_generator()

        # Add some garbage
        garbage = ["Erm...", "Blah-blah"]
        with open(self.log, 'a') as f:
            for piece in garbage:
                f.writelines([piece, '\n'])

        self.generate_report()
        # Check our log
        for piece in garbage:
            self.assertTrue(self.check_in_log('Row {} is missed'.format(piece)))  # We logged that problem

    def test_suddenly_error(self):
        # If something has been wrong
        self.log = nginx_log_gz_generator()
        old_name = self.log
        new_name = old_name.replace('.gz', '')
        os.rename(old_name, new_name)  # Change file extension
        self.generate_report()
        self.assertTrue(self.check_in_log("'utf-8' codec can't decode byte"))


if __name__ == '__main__':
    unittest.main()
