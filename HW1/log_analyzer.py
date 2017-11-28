# %load log_analyzer.py
# !/usr/bin/env python3


import argparse
import gzip
import json
import logging
# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import os
import re
import statistics
import time
from datetime import date, datetime
from string import Template

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "TS_FILE": "./ts.ts"
}


def find_files_by_mask(directory: str, file_mask: re):
    files = iter(os.listdir(directory))
    valid_files = filter(file_mask.match, files)
    return valid_files


def get_lats_log_file(log_dir: str, file_mask: re):
    """Return newest log-file in dir"""
    # Try to find last log-file in DIR
    logs = find_files_by_mask(log_dir, file_mask)
    # We know that log have date differnce
    logs = sorted(logs, key=lambda log: log, reverse=True)
    if logs:
        last_log_file = '{}/{}'.format(log_dir, logs[0])
        return last_log_file
    else:
        return None


def conver_to_absolute_path(relative_path: str) -> str:
    if relative_path.startswith('.'):  # We have relative path.
        # transform relative to absolute
        current_dir = os.getcwd()
        absolute_path = current_dir + relative_path[1:]
        return absolute_path
    else:
        return relative_path


def prepare_report(params: dict):

    homework_dir = os.path.dirname(os.path.realpath(__file__))
    path_to_template = '{}/report.html'.format(homework_dir)
    text_tempalte = open(path_to_template).read()
    page = Template(text_tempalte)
    page = page.safe_substitute(params)
    return page


def analyze_log(path_to_log: str, report_size: int):
    url_pattern = re.compile('[A-Z]+\s(?P<url>\S+)\sHTTP/\d\.\d.* (?P<t_execution>\d+(\.\d+)?)')
    requests = []
    total_time = 0
    total_req = 0
    stat = {}
    is_gz_file = path_to_log.endswith(".gz")
    if is_gz_file:
        rows = gzip.open(path_to_log)
    else:
        rows = open(path_to_log)

    for row in rows:
        if is_gz_file:
            # Read bytes
            row = row.decode('utf-8')

        matches = url_pattern.search(row)
        if matches:
            url = matches.group('url')
            # row in logfile have mark about time of execution.
            t_execution = float(matches.group('t_execution'))
            stat.setdefault(url, []).append(t_execution)
            total_time += t_execution
            total_req += 1

    for url, t_executions in stat.items():
        # Calculate avg for serving time
        metrics = {}
        avg_time = round(statistics.mean(t_executions), 3)
        total_req_for_req = len(t_executions)
        total_time_for_req = round(sum(t_executions), 3)
        metrics['time_avg'] = avg_time
        metrics['count'] = total_req_for_req
        metrics['time_sum'] = total_time_for_req
        metrics['time_max'] = max(t_executions)
        metrics['url'] = url
        metrics['time_med'] = round(statistics.median(t_executions), 3)
        metrics['time_perc'] = round(total_time_for_req / total_time * 100, 3)
        metrics['count_perc'] = round(total_req_for_req / total_req * 100, 3)
        requests.append(metrics)

    ordered_requests = sorted(requests, key=lambda request: request['time_sum'], reverse=True)
    most_slow_requests = ordered_requests[:report_size]
    return most_slow_requests


def get_logger(config: dict):
    # Start our logger
    logger = logging.getLogger('log_analyzer')
    logger.setLevel(logging.INFO)
    path_to_log_file = config.get('LOG_FILE')
    if path_to_log_file:
        # Write to file
        path_to_log_file = conver_to_absolute_path(path_to_log_file)
        handler = logging.FileHandler(path_to_log_file)
    else:
        # Write to stdout
        handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s', '%Y.%m.%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def params_unification(exteranal_config=None):
    """Convert path to file"""
    if exteranal_config:
        settings = exteranal_config
    else:
        settings = config.copy()
    checked_params = ["REPORT_DIR", "LOG_DIR"]
    for prop in checked_params:
        value = settings[prop]
        settings[prop] = conver_to_absolute_path(value)

    return settings


def get_path_to_last_nginx_log(path_to_logs, logger):
    # Get path to last log-file
    file_mask = re.compile('^nginx-access-ui.log-\d{8}(\.gz)?$')
    path_to_last_log = get_lats_log_file(path_to_logs, file_mask)
    if not path_to_last_log:
        logger.error("Sorry, we didn't find valid nginx logs in directory {}".format(path_to_logs))
        return None
    return path_to_last_log


def get_path_for_daily_report(date_of_log: date, path_to_reports: str, logger):
    # Check report for that day
    day_of_report = datetime.strftime(date_of_log, '%Y.%m.%d')
    path_for_daily_report = '{0}/report-{1}.html'.format(path_to_reports, day_of_report)
    if os.path.exists(path_for_daily_report):
        logger.error("Daily report already exists.For more information see file {0}".format(path_for_daily_report))
        return None
    return path_for_daily_report


def create_or_update_ts(config):
    ts_file = config.get('TS_FILE')
    if ts_file:
        ts = int(time.time())
        with open(ts_file, "w") as f:
            f.write(str(ts))
        os.utime(ts_file, (ts, ts))
        return True


def main():
    m = argparse.ArgumentParser(description="Log analyzer", epilog="Is made nginx's logs understable",
                                prog="log_analyzer")
    m.add_argument("--config", "-c", type=str, default='', help="Program config")
    options = m.parse_args()

    path_to_exteranal_config = options.config
    if path_to_exteranal_config:
        path_to_exteranal_config = conver_to_absolute_path(path_to_exteranal_config)
        external_config = open(path_to_exteranal_config, 'r')
        exteranal_config = json.load(external_config)
        config = params_unification(exteranal_config=exteranal_config)
    else:
        config = params_unification()

    logger = get_logger(config)
    logger.info("Log analyzer run")
    path_to_last_log = get_path_to_last_nginx_log(config["LOG_DIR"], logger)
    if path_to_last_log:

        date_of_log_str = re.findall('\d{8}', path_to_last_log)[0]
        date_of_log = datetime.strptime(date_of_log_str, '%Y%m%d').date()
        path_to_daily_report = get_path_for_daily_report(date_of_log, config["REPORT_DIR"], logger)

        if path_to_daily_report:
            try:
                # Parsing
                logger.info("Nginx log analyz was started")
                report_size = config['REPORT_SIZE']

                slow_requests = analyze_log(path_to_last_log, report_size)
                logger.info("Nginx log analyze was finished")

                # Report
                logger.info("Make daily report from template")
                page = prepare_report({'table_json': slow_requests})
                logger.info("Daily report was prepared")
                with open(path_to_daily_report, 'w') as f:
                    f.write(page)
                logger.info("Daily report was wrote")

                if create_or_update_ts(config):
                    logger.info("TS-file was updated")

            except Exception as e:
                logger.exception(str(e))
    logger.info("Log analyzer stopped")


if __name__ == "__main__":
    main()
