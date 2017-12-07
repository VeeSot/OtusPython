# %load log_analyzer.py
# !/usr/bin/env python3

import argparse
import gzip
import json
import logging
import os
import re
import statistics
import time
from collections import namedtuple, defaultdict, Generator
from datetime import datetime
from json import JSONDecodeError
from string import Template
from typing import Union

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
LogInformation = namedtuple('LogInformation', 'date path')


def prepare_report(params: dict, path_to_template):
    with open(path_to_template, "r") as f:
        text_tempalte = f.read()
    page = Template(text_tempalte)
    page = page.safe_substitute(params)
    return page


def read_log(path_to_log):
    is_gz_file = path_to_log.endswith(".gz")
    if is_gz_file:
        log = gzip.open(path_to_log, 'rt', encoding='utf-8')
    else:
        log = open(path_to_log)

    for row in log:
        yield row


def analyze_log(rows: Generator, report_size: int):
    url_pattern = re.compile('[A-Z]+\s(?P<url>\S+)\sHTTP/\d\.\d.* (?P<t_execution>\d+(\.\d+)?)')
    requests = []
    total_time = 0
    total_matched = 0
    bad_rows = 0
    stat = defaultdict(list)
    for row in rows:
        matches = url_pattern.search(row)
        if matches:
            url = matches.group('url')
            # row in logfile has mark about time of execution.
            t_execution = float(matches.group('t_execution'))
            stat[url].append(t_execution)
            total_time += t_execution
            total_matched += 1
        else:
            bad_rows += 1

    if bad_rows:
        logging.info('Were/was skipped {} row(s) from {}'.format(bad_rows,bad_rows+total_matched))

    for url, t_executions in stat.items():
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
        metrics['count_perc'] = round(total_req_for_req / total_matched * 100, 3)
        requests.append(metrics)

    ordered_requests = sorted(requests, key=lambda request: request['time_sum'], reverse=True)
    most_slow_requests = ordered_requests[:report_size]
    return most_slow_requests


def configure_logger(path_to_log_file):
    # Configure our logger
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S', filename=path_to_log_file)


def get_path_to_last_nginx_log(path_to_logs) -> Union[None, LogInformation]:
    """Return newest log-file in dir
    log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
                        '$status $body_bytes_sent "$http_referer" '
                        '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
                        '$request_time';

    """
    if not os.path.exists(path_to_logs):
        logging.error("Sorry, directory {} wasn't found".format(path_to_logs))
        return None

    file_mask = re.compile('^nginx-access-ui.log-(?P<day_of_log>\d{8})(\.gz)?$')
    # Try to find last log-file in DIR
    logs = os.listdir(path_to_logs)
    valid_logs = []
    for log in logs:
        match = file_mask.search(log)
        if match:  # We find valid log
            day_of_log = datetime.strptime(match.group('day_of_log'), '%Y%m%d').date()
            log_file = '{}/{}'.format(path_to_logs, match.string)
            log_info = LogInformation(day_of_log, log_file)
            valid_logs.append(log_info)

    if valid_logs:
        # We know that log have date difference, but find newest
        valid_log = max(valid_logs, key=lambda log: log.date)
        return valid_log
    else:
        logging.info("Not found logs in directory {}".format(path_to_logs))
        return None


def refresh_ts(path_to_ts_file: str):
    """Update timestamp last report creation"""
    ts = int(time.time())
    with open(path_to_ts_file, "w") as f:
        f.write(str(ts))
    os.utime(path_to_ts_file, (ts, ts))
    logging.info("TS-file was updated")


def build_config(path_to_config) -> dict:
    try:
        with open(path_to_config, 'r') as f:
            return json.load(f)
    except JSONDecodeError:
        logging.error("Please, check your config")
        raise Exception("Please, check your config")


def make_report(path_to_new_daily_report: str, path_to_template, slow_requests):
    logging.info("Make daily report from template")
    page = prepare_report({'table_json': slow_requests}, path_to_template)

    with open(path_to_new_daily_report, 'w') as f:
        f.write(page)
    logging.info("Daily report was wrote")
    return page


def main(config: dict):
    logging.info("Log analyzer run")
    about_last_log = get_path_to_last_nginx_log(config["LOG_DIR"])
    if about_last_log:
        day_of_report = datetime.strftime(about_last_log.date, '%Y.%m.%d')
        path_to_daily_report = '{0}/report-{1}.html'.format(config["REPORT_DIR"], day_of_report)
        if not os.path.exists(path_to_daily_report):
            logging.info("Nginx log analysis was started")
            log_rows = read_log(about_last_log.path)
            slow_requests = analyze_log(log_rows, config['REPORT_SIZE'])
            logging.info("Nginx log analysis was finished")

            make_report(path_to_daily_report, config['REPORT_TEMPLATE'], slow_requests)
            refresh_ts(config['TS_FILE'])  # Report

    logging.info("Log analyzer stopped")


if __name__ == "__main__":
    path_to_default_conf = '/path/HW1/local_conf.conf'
    config = build_config(path_to_default_conf)

    m = argparse.ArgumentParser(description="Log analyzer", prog="log_analyzer")
    m.add_argument("--config", "-c", type=str, default=path_to_default_conf, help="Program config")
    options = m.parse_args()
    if options.config != path_to_default_conf:
        # Merge with external config
        external_conf = build_config(options.config)
        config.update(external_conf)

    configure_logger(config.get('LOG_FILE'))
    try:
        main(config)
    except Exception as e:
        # If something going wrong
        logging.exception(e, exc_info=True)
