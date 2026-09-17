# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Hello Amazon CloudWatch Logs!

This example verifies connectivity to the CloudWatch Logs service
and lists existing log groups in your account.

Usage:
    python cloudwatch_logs_hello.py
"""

import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# snippet-start:[python.example_code.cloudwatch-logs.Hello]
def hello_cloudwatch_logs() -> None:
    """
    Lists up to 5 CloudWatch Logs log groups in the current account and Region.
    Demonstrates basic connectivity to the CloudWatch Logs service.
    """
    logs_client = boto3.client("logs")

    print("Hello, Amazon CloudWatch Logs! Let's list some of your log groups:\n")

    try:
        paginator = logs_client.get_paginator("describe_log_groups")
        page_iterator = paginator.paginate(
            PaginationConfig={"MaxItems": 5, "PageSize": 5}
        )

        log_group_count = 0
        for page in page_iterator:
            for log_group in page.get("logGroups", list()):
                log_group_count += 1
                name = log_group.get("logGroupName", "N/A")
                arn = log_group.get("arn", "N/A")
                retention = log_group.get("retentionInDays", None)
                stored_bytes = log_group.get("storedBytes", 0)

                retention_display = (
                    f"{retention} days" if retention is not None else "Never expire"
                )

                print(f"Log Group: {name}")
                print(f"  ARN: {arn}")
                print(f"  Retention: {retention_display}")
                print(f"  Stored Bytes: {stored_bytes}")
                print()

        if log_group_count == 0:
            print("No log groups found in the current account and Region.")
        else:
            print(f"Found {log_group_count} log group(s) (showing first 5).")

    except ClientError as error:
        logger.error(
            "Couldn't list log groups. Error: %s: %s",
            error.response["Error"]["Code"],
            error.response["Error"]["Message"],
        )
        raise


# snippet-end:[python.example_code.cloudwatch-logs.Hello]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    hello_cloudwatch_logs()
