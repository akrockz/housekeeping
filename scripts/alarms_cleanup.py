#!/usr/bin/python3
"""
Goal: find specific build-level alarms for saa and remove. Do this by using a prefix and a regex filter.
See argparse help for examples.
Reason for this: the alarm thresholds lambda should work at the branch level, not build level for alarms. Database data.

Nonprod:

AWS_PROFILE=abc-nonprod-auto ./scripts/alarms_cleanup.py \
--alarm-prefix "CRITICAL=abcturbo-dev=abc-appls-" \
--alarm-filter "CRITICAL=abcturbo-dev=abc-appls-(.*)-(\\d*)-appls-(Zero|Low)Transaction(.*)Total" \
>> /mnt/c/Users/smac/tmp/alarms_cleanup_abcturbo-dev=abc-appls-nonprod.txt

AWS_PROFILE=abc-nonprod-auto ./scripts/alarms_cleanup.py \
--alarm-prefix "CRITICAL=abcturbo-prod=abc-appls-" \
--alarm-filter "CRITICAL=abcturbo-prod=abc-appls-(.*)-(\\d*)-appls-(Zero|Low)Transaction(.*)Total" \
>> /mnt/c/Users/smac/tmp/alarms_cleanup_abcturbo-prod=abc-appls-nonprod.txt

(Add --delete to delete for real.)

"""

from botocore.config import Config
import argparse
import boto3
import re


def __get_args():
    """Used when running locally via shell."""
    parser = argparse.ArgumentParser(
        description="Find abc build-level alarms we don't want, and clean them.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--alarm-prefix", dest="alarm_prefix", required=True, help="Prefix to find alarms, i.e. CRITICAL=abcturbo-dev=abc-appls-nonprod-. Subset of the filter.")
    parser.add_argument("--alarm-filter", dest="alarm_filter", required=True, help="Regex, i.e. CRITICAL=abcturbo-dev=abc-appls-nonprod-(\\d*)-appls-(Zero|Low)Transaction(.*)Total")
    parser.add_argument("--delete", dest="delete", action="store_true", default=False)
    return vars(parser.parse_args())  # Convert to dictionary to be compatible with lambda handler implementation.


def main(args):
    print('args={}'.format(args))

    config = Config(connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10))
    cloudwatch_client = boto3.client('cloudwatch', config=config)

    paginator = cloudwatch_client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=args['alarm_prefix'])

    candidate_alarms = []

    for page in page_iterator:
        for alarm in page['MetricAlarms']:
            match = re.match(args['alarm_filter'], alarm['AlarmName'])
            if match:
                print('Found alarm {}'.format(alarm['AlarmName']))
                candidate_alarms.append(alarm['AlarmName'])

    print('Found {} total candidate_alarms.'.format(len(candidate_alarms)))

    if args['delete'] and len(candidate_alarms) > 0:
        # Max 100 per API call - https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DeleteAlarms.html
        chunks = [candidate_alarms[x:x + 100] for x in range(0, len(candidate_alarms), 100)]
        for chunk in chunks:
            # print('Chunk={}'.format(chunk))
            response = cloudwatch_client.delete_alarms(AlarmNames=chunk)
            print('Delete response={}'.format(response))

    print('Done.')


if __name__ == '__main__':
    main(__get_args())
