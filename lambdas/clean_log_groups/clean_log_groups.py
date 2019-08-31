#!/usr/bin/python3
"""
Goal: Find empty log groups that have stayed empty for more than a week, and delete them.

Cleanup algorithm:
Get yaml data file from s3
For each (and all) log groups in the account,
    Find out if it's empty
        Find out if it's in the hash already
            Check the time is older than 1 week
                Delete the log group
            Else
                Record the current time (UTC) into a hash for this log group
Put yaml data file into s3

Example:
AWS_PROFILE=abc-nonprod-auto ./bin/clean-cloudwatch-log-groups.py --delete
"""

import argparse
import boto3
import json
from botocore.config import Config
from datetime import datetime, timedelta
from os import environ
from botocore.exceptions import ClientError

config = Config(connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10))
logs_client = boto3.client("logs", config=config)
cloudformation_client = boto3.client("cloudformation", config=config)
s3_client = boto3.client("s3")


def __log_group_is_old_enough(last_recorded_utc, days=7):
    timestamp_threshold = int((datetime.utcnow() - timedelta(days=int(days))).timestamp())
    # print("last_recorded_utc={}, timestamp_threshold={}".format(last_recorded_utc, timestamp_threshold))
    return last_recorded_utc < timestamp_threshold


def __now_utc():
    return int(datetime.utcnow().timestamp())


def __get_args():
    """Used when running locally via shell."""
    parser = argparse.ArgumentParser(
        description="Find CloudWatch Log Groups that have been left behind after teardown, AND all log streams have expired.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--automation-bucket", dest="automation_bucket", default=environ.get("AUTOMATION_BUCKET", "abc-core-automation-ap-southeast-1"))
    parser.add_argument("--data-file-suffix", dest="data_file_suffix", default=environ.get("AWS_PROFILE"))
    parser.add_argument("--days", dest="days", default=7)
    parser.add_argument("--delete", dest="delete", action="store_true", default=False)
    parser.add_argument("--s3-prefix", dest="s3_prefix", default=environ.get("AUTOMATION_BRANCH_S3_PREFIX", "files/branch/core/housekeeping/master"))
    return vars(parser.parse_args())  # Convert to dictionary to be compatible with lambda handler implementation.


def __has_log_streams(log_group_name):
    response = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        limit=1
    )
    return len(response["logStreams"]) > 0


def __get_state(args, s3_key):
    """Fetch state data for this account from s3."""
    state = {}
    try:
        s3_response = s3_client.get_object(Bucket=args["automation_bucket"], Key=s3_key)
        state = json.loads(s3_response["Body"].read().decode())
        print("Loaded {} previous candidate log groups from datastore.".format(len(state)))
    except ClientError as ex:
        if ex.response["Error"]["Code"] == "NoSuchKey":
            print("No s3 state file found for {}, creating new.".format(s3_key))
        else:
            raise ex
    return state


def __put_state(args, s3_key, state):
    print("Uploading state file to S3 ({}/{})".format(args["automation_bucket"], s3_key))
    s3_client.put_object(
        ACL="authenticated-read",
        Body=json.dumps(state),
        Bucket=args["automation_bucket"],
        Key=s3_key,
        ServerSideEncryption="AES256"
    )


def main(args):

    print("args={}".format(args))
    s3_key = "{}/{}.json".format(args["s3_prefix"], args["data_file_suffix"])

    candidate_log_groups = __get_state(args, s3_key)
    log_groups_to_delete = []

    paginator = logs_client.get_paginator("describe_log_groups")
    page_iterator = paginator.paginate(
        PaginationConfig={
            "MaxItems": 10000,
            "PageSize": 50
        }
    )

    for log_groups_page in page_iterator:
        for log_group in log_groups_page["logGroups"]:

            log_group_name = log_group["logGroupName"]
            # print("Checking log_group={}".format(log_group_name))

            if log_group_name.startswith("core-"):
                print("Log group {} is core-*, skipping.".format(log_group_name))
                if log_group_name in candidate_log_groups:
                    print("Log group '{}' previously tracked, removing because core-*.".format(log_group_name))
                    del candidate_log_groups[log_group_name]
                continue

            # Check if this log group has log streams
            if __has_log_streams(log_group_name):

                # log streams are (now?) present, if we were watching this log group, stop now.
                if log_group_name in candidate_log_groups:
                    print("Log group {} previously tracked, now has log streams".format(log_group_name))
                    del candidate_log_groups[log_group_name]

            else:

                # Check if this log group is already being watched.
                last_recorded_utc = candidate_log_groups.get(log_group_name, None)
                if last_recorded_utc is None:
                    # Start watching this log group for the first time.
                    candidate_log_groups[log_group_name] = __now_utc()
                    print("Log group {} added with timestamp {}".format(log_group_name, candidate_log_groups[log_group_name]))
                else:
                    if __log_group_is_old_enough(last_recorded_utc, args["days"]):
                        print("Log group {} is candidate AND old enough".format(log_group_name))
                        log_groups_to_delete.append(log_group_name)
                    else:
                        # Stay the watch list, basically.
                        print("Log group {} is candidate, NOT old enough".format(log_group_name))

    print("Finished scanning log groups.")
    print("candidate_log_groups={}".format(json.dumps(candidate_log_groups)))
    print("{} log groups scheduled for deletion: {}".format(len(log_groups_to_delete), json.dumps(log_groups_to_delete)))

    __put_state(args, s3_key, candidate_log_groups)

    if args["delete"]:
        for log_group_name in log_groups_to_delete:
            try:
                print("Deleting {}".format(log_group_name))
                response = logs_client.delete_log_group(logGroupName=log_group_name)
                print("Deleted {}, response={}".format(log_group_name, response))
            except ClientError as ex:
                print("Failed to delete {}, may have been deleted previously. ex={}".format(log_group_name, ex))
                # Swallow exception and push on.
            print("Removing {} from candidate_log_groups".format(log_group_name))
            del candidate_log_groups[log_group_name]

        print("Update state after all deletes are complete.")
        __put_state(args, s3_key, candidate_log_groups)
    else:
        print("Dry run mode is enabled, skipping delete step.")

    # What should be returned after an invoke?
    output = {
        "candidate_log_groups_size": len(candidate_log_groups),
        "delete": args["delete"],
        "log_groups_to_delete": log_groups_to_delete,
        "s3_key": s3_key
    }
    print("Summary output={}".format(json.dumps(output)))
    return output


def handler(event, context):
    """Lambda handler function."""
    print('handler event={}'.format(json.dumps(event)))
    return main({
        "automation_bucket": environ.get("AUTOMATION_BUCKET"),
        "data_file_suffix": environ.get("ACCOUNT_ID"),
        "delete": environ.get("DELETE_LOG_GROUPS", "False").lower() == "true",
        "s3_prefix": environ.get("AUTOMATION_BRANCH_S3_PREFIX"),
        "days": environ.get("DAYS", "7")
    })


if __name__ == "__main__":
    args = __get_args()
    main(args)
