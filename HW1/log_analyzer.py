#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import os
import argparse
import glob
import re
import pandas as pd
import numpy as np

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def log_procesing(log_path, agg_type):
    log_chunk = pd.read_csv(log_path, header=None, sep=r'\s(?=(?:[^"]*"[^"]*")*[^"]*$)(?![^\[]*\])',
                            engine="python", chunksize=100000, usecols=[5, 13], names=["url", "request_time"],
                            converters={"url": parse_string, "request_time": float}, iterator=True)
    log_table = pd.concat(log_chunk, ignore_index=True)
    total_count = float(len(log_table.index))
    total_time = log_table['request_time'].sum()
    aggregation_mean = [('count', 'count'), ('count_perc', lambda x: x.count() / total_count * 100),
                        ('time_avg', 'mean'), ('time_max', 'max'), ('time_med', 'median'),
                        ('time_perc', lambda x: (x.sum() / total_time) * 100), ('time_sum', 'sum')]
    aggregation_perc = [('count', 'count'), ('count_perc', lambda x: x.count() / total_count * 100),
                        ('time_max', 'max'), ('time_p50', 'median'), ('time_p95', lambda x: np.percentile(x, q=0.95)),
                        ('time_p99', lambda x: np.percentile(x, q=0.99)),
                        ('time_perc', lambda x: (x.sum() / total_time) * 100),
                        ('time_sum', 'sum')]
    if agg_type == "agg_perc":
        log_agg = log_table.groupby('url')['request_time'].agg(aggregation_perc).reset_index()
    else:
        log_agg = log_table.groupby('url')['request_time'].agg(aggregation_mean).reset_index()
    log_agg.sort_values('time_sum', ascending=False, inplace=True)
    log_agg.iloc[:, 1:] = log_agg.iloc[:, 1:].apply(lambda x: pd.Series.round(x, 3))
    return log_agg[:1000]


def parse_string(string):
    try:
        return string.split(' ')[1]
    except IndexError:
        pass


def save_html(data, template_path, report_path):
    with open(template_path, "r") as template:
        with open(report_path, "w") as report:
            for line in template:
                if "table_json" in line:
                    report.write(line.replace("$table_json", data[:1000].to_json(orient="records")))
                else:
                    report.write(line)


def save_json(data, report_path):
    data.to_json(report_path, orient="records")


def main(log_path, fmt, agg_type):
    if not os.path.exists(config["REPORT_DIR"]):
        os.makedirs(config["REPORT_DIR"])
    if not log_path:
        log_path = max(glob.iglob(config["LOG_DIR"] + "/*.*"), key=os.path.getctime)
    log_date = re.search('(\d{8})', log_path).group(0)
    report_date = log_date[:4] + "." + log_date[4:6] + "." + log_date[6:]
    report_path = os.path.join(config["REPORT_DIR"], "report-%s.%s" % (report_date, fmt))
    if os.path.exists(report_path):
        print("report already exists")
        return
    log_table = log_procesing(log_path, agg_type)
    if fmt == "json":
        save_json(log_table, report_path)
    else:
        template_path = os.path.join(config["REPORT_DIR"], "report.html")
        save_html(log_table, template_path, report_path)


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_path", help="Specify path to log file", default=None)
    parser.add_argument("--agg_type", help="Specify data aggregation type: agg_mean for "
                                           "mean/median, agg_perc - 0.5, 0.95, 0.99 percentiles", default="agg_mean")
    parser.add_argument("--fmt", help="Specify output file format, html or json", default="html")
    return parser.parse_args()


if __name__ == "__main__":
    args = argument_parser()
    main(args.log_path, args.fmt, args.agg_type)
