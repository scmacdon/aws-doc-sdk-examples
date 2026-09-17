# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Wrapper class for Amazon CloudWatch Logs operations.

This module encapsulates CloudWatch Logs API calls for creating, configuring,
populating, querying, and managing log groups.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# snippet-start:[python.example_code.cloudwatch-logs.CloudWatchLogsWrapper.class]
# snippet-start:[python.example_code.cloudwatch-logs.CloudWatchLogsWrapper.decl]
class CloudWatchLogsWrapper:
    """Encapsulates Amazon CloudWatch Logs operations."""

    def __init__(self, logs_client: boto3.client) -> None:
        """
        Initializes the CloudWatchLogsWrapper with a boto3 CloudWatch Logs client.

        :param logs_client: A boto3 CloudWatch Logs client.
        """
        self.logs_client = logs_client

    @classmethod
    def from_client(cls) -> "CloudWatchLogsWrapper":
        """
        Creates a CloudWatchLogsWrapper instance using a default boto3 client.

        :return: A new CloudWatchLogsWrapper instance.
        """
        logs_client = boto3.client("logs")
        return cls(logs_client)

    # snippet-end:[python.example_code.cloudwatch-logs.CloudWatchLogsWrapper.decl]

    # snippet-start:[python.example_code.cloudwatch-logs.CreateLogGroup]
    def create_log_group(self, log_group_name: str) -> None:
        """
        Creates a CloudWatch Logs log group.

        :param log_group_name: The name of the log group to create.
        :raises ClientError: If the API call fails (other than ResourceAlreadyExistsException).
        """
        try:
            self.logs_client.create_log_group(logGroupName=log_group_name)
            logger.info("Created log group '%s'.", log_group_name)
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceAlreadyExistsException":
                logger.info(
                    "Log group '%s' already exists. Proceeding with existing group.",
                    log_group_name,
                )
            else:
                logger.error(
                    "Couldn't create log group '%s'. Error: %s: %s",
                    log_group_name,
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
                raise

    # snippet-end:[python.example_code.cloudwatch-logs.CreateLogGroup]

    # snippet-start:[python.example_code.cloudwatch-logs.CreateLogStream]
    def create_log_stream(self, log_group_name: str, log_stream_name: str) -> None:
        """
        Creates a log stream within a log group.

        :param log_group_name: The name of the log group.
        :param log_stream_name: The name of the log stream to create.
        :raises ClientError: If the API call fails (other than ResourceAlreadyExistsException).
        """
        try:
            self.logs_client.create_log_stream(
                logGroupName=log_group_name, logStreamName=log_stream_name
            )
            logger.info(
                "Created log stream '%s' in log group '%s'.",
                log_stream_name,
                log_group_name,
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceAlreadyExistsException":
                logger.info(
                    "Log stream '%s' already exists in log group '%s'. Proceeding.",
                    log_stream_name,
                    log_group_name,
                )
            else:
                logger.error(
                    "Couldn't create log stream '%s' in log group '%s'. Error: %s: %s",
                    log_stream_name,
                    log_group_name,
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
                raise

    # snippet-end:[python.example_code.cloudwatch-logs.CreateLogStream]

    # snippet-start:[python.example_code.cloudwatch-logs.PutLogEvents]
    def put_log_events(
        self,
        log_group_name: str,
        log_stream_name: str,
        log_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Uploads a batch of log events to a log stream.

        :param log_group_name: The name of the log group.
        :param log_stream_name: The name of the log stream.
        :param log_events: A list of log event dicts, each with 'timestamp' (int, ms)
                           and 'message' (str) keys.
        :return: The response from PutLogEvents.
        :raises ClientError: If the log group or stream does not exist.
        """
        try:
            response = self.logs_client.put_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                logEvents=log_events,
            )
            logger.info(
                "Put %d log events to stream '%s' in group '%s'.",
                len(log_events),
                log_stream_name,
                log_group_name,
            )
            return response
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(
                    "Log group '%s' or stream '%s' does not exist. "
                    "Verify they were created before putting log events.",
                    log_group_name,
                    log_stream_name,
                )
            else:
                logger.error(
                    "Couldn't put log events. Error: %s: %s",
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
            raise

    # snippet-end:[python.example_code.cloudwatch-logs.PutLogEvents]

    # snippet-start:[python.example_code.cloudwatch-logs.DescribeLogGroups]
    def describe_log_groups(
        self, log_group_name_prefix: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Describes log groups, optionally filtered by a name prefix.
        Uses a paginator to retrieve all matching log groups.

        :param log_group_name_prefix: Filter to log groups matching this prefix.
        :param limit: Maximum number of log groups to return. None returns all.
        :return: A list of log group description dicts.
        :raises ClientError: If an invalid parameter is provided.
        """
        try:
            log_groups = list()
            params = dict()
            if log_group_name_prefix is not None:
                params["logGroupNamePrefix"] = log_group_name_prefix
            if limit is not None:
                params["PaginationConfig"] = {"MaxItems": limit}

            paginator = self.logs_client.get_paginator("describe_log_groups")
            for page in paginator.paginate(**params):
                log_groups.extend(page.get("logGroups", list()))

            logger.info("Described %d log groups.", len(log_groups))
            return log_groups
        except ClientError as error:
            if error.response["Error"]["Code"] == "InvalidParameterException":
                logger.error(
                    "Invalid parameter for DescribeLogGroups. "
                    "Check the log group name prefix or other parameters."
                )
            else:
                logger.error(
                    "Couldn't describe log groups. Error: %s: %s",
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
            raise

    # snippet-end:[python.example_code.cloudwatch-logs.DescribeLogGroups]

    # snippet-start:[python.example_code.cloudwatch-logs.DescribeLogStreams]
    def describe_log_streams(
        self, log_group_name: str
    ) -> List[Dict[str, Any]]:
        """
        Describes log streams for a log group.
        Uses a paginator to retrieve all log streams.

        :param log_group_name: The name of the log group.
        :return: A list of log stream description dicts.
        :raises ClientError: If the log group does not exist.
        """
        try:
            log_streams = list()
            paginator = self.logs_client.get_paginator("describe_log_streams")
            for page in paginator.paginate(logGroupName=log_group_name):
                log_streams.extend(page.get("logStreams", list()))

            logger.info(
                "Described %d log streams for group '%s'.",
                len(log_streams),
                log_group_name,
            )
            return log_streams
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(
                    "Log group '%s' does not exist. Verify the log group name.",
                    log_group_name,
                )
            else:
                logger.error(
                    "Couldn't describe log streams. Error: %s: %s",
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
            raise

    # snippet-end:[python.example_code.cloudwatch-logs.DescribeLogStreams]

    # snippet-start:[python.example_code.cloudwatch-logs.GetLogEvents]
    def get_log_events(
        self,
        log_group_name: str,
        log_stream_name: str,
        start_from_head: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves log events from a specific log stream.

        :param log_group_name: The name of the log group.
        :param log_stream_name: The name of the log stream.
        :param start_from_head: If True, retrieve from oldest to newest.
        :param limit: Maximum number of events to retrieve per API call.
        :return: A list of log event dicts.
        :raises ClientError: If the log group or stream does not exist.
        """
        try:
            events = list()
            params = dict()
            params["logGroupName"] = log_group_name
            params["logStreamName"] = log_stream_name
            params["startFromHead"] = start_from_head
            if limit is not None:
                params["limit"] = limit

            # GetLogEvents uses forward/backward token pagination.
            # We iterate until the nextForwardToken stops changing.
            prev_token = None
            while True:
                response = self.logs_client.get_log_events(**params)
                events.extend(response.get("events", list()))
                next_token = response.get("nextForwardToken", None)
                if next_token == prev_token:
                    break
                prev_token = next_token
                params["nextToken"] = next_token

            logger.info(
                "Retrieved %d log events from stream '%s' in group '%s'.",
                len(events),
                log_stream_name,
                log_group_name,
            )
            return events
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(
                    "Log group '%s' or stream '%s' does not exist.",
                    log_group_name,
                    log_stream_name,
                )
            else:
                logger.error(
                    "Couldn't get log events. Error: %s: %s",
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
            raise

    # snippet-end:[python.example_code.cloudwatch-logs.GetLogEvents]

    # snippet-start:[python.example_code.cloudwatch-logs.FilterLogEvents]
    def filter_log_events(
        self,
        log_group_name: str,
        filter_pattern: str,
    ) -> List[Dict[str, Any]]:
        """
        Searches and filters log events across all streams in a log group.
        Uses a paginator to retrieve all matching events.

        :param log_group_name: The name of the log group to search.
        :param filter_pattern: The filter pattern to match.
        :return: A list of matching log event dicts.
        :raises ClientError: If the log group does not exist.
        """
        try:
            events = list()
            paginator = self.logs_client.get_paginator("filter_log_events")
            for page in paginator.paginate(
                logGroupName=log_group_name, filterPattern=filter_pattern
            ):
                events.extend(page.get("events", list()))

            logger.info(
                "Filtered %d events matching pattern '%s' in group '%s'.",
                len(events),
                filter_pattern,
                log_group_name,
            )
            return events
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(
                    "Log group '%s' does not exist. Verify the log group name.",
                    log_group_name,
                )
            else:
                logger.error(
                    "Couldn't filter log events. Error: %s: %s",
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
            raise

    # snippet-end:[python.example_code.cloudwatch-logs.FilterLogEvents]

    # snippet-start:[python.example_code.cloudwatch-logs.PutMetricFilter]
    def put_metric_filter(
        self,
        log_group_name: str,
        filter_name: str,
        filter_pattern: str,
        metric_name: str,
        metric_namespace: str,
        metric_value: str,
        default_value: float = 0,
    ) -> None:
        """
        Creates or updates a metric filter on a log group.

        :param log_group_name: The name of the log group.
        :param filter_name: The name of the metric filter.
        :param filter_pattern: The pattern to match in log events.
        :param metric_name: The name of the CloudWatch metric.
        :param metric_namespace: The namespace for the metric.
        :param metric_value: The value to publish when the pattern matches.
        :param default_value: The default value when no match occurs.
        :raises ClientError: If the max number of metric filters is reached.
        """
        try:
            self.logs_client.put_metric_filter(
                logGroupName=log_group_name,
                filterName=filter_name,
                filterPattern=filter_pattern,
                metricTransformations=[
                    {
                        "metricName": metric_name,
                        "metricNamespace": metric_namespace,
                        "metricValue": metric_value,
                        "defaultValue": default_value,
                    }
                ],
            )
            logger.info(
                "Created metric filter '%s' on log group '%s'.",
                filter_name,
                log_group_name,
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "LimitExceededException":
                logger.error(
                    "Maximum number of metric filters (100) reached for log group '%s'. "
                    "Delete unused metric filters before creating new ones.",
                    log_group_name,
                )
            else:
                logger.error(
                    "Couldn't create metric filter '%s'. Error: %s: %s",
                    filter_name,
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
            raise

    # snippet-end:[python.example_code.cloudwatch-logs.PutMetricFilter]

    # snippet-start:[python.example_code.cloudwatch-logs.DescribeMetricFilters]
    def describe_metric_filters(
        self, log_group_name: str
    ) -> List[Dict[str, Any]]:
        """
        Lists metric filters for a log group.
        Uses a paginator to retrieve all metric filters.

        :param log_group_name: The name of the log group.
        :return: A list of metric filter description dicts.
        :raises ClientError: If the log group does not exist.
        """
        try:
            metric_filters = list()
            paginator = self.logs_client.get_paginator("describe_metric_filters")
            for page in paginator.paginate(logGroupName=log_group_name):
                metric_filters.extend(page.get("metricFilters", list()))

            logger.info(
                "Described %d metric filters for group '%s'.",
                len(metric_filters),
                log_group_name,
            )
            return metric_filters
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(
                    "Log group '%s' does not exist. Verify the log group name.",
                    log_group_name,
                )
            else:
                logger.error(
                    "Couldn't describe metric filters. Error: %s: %s",
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
            raise

    # snippet-end:[python.example_code.cloudwatch-logs.DescribeMetricFilters]

    # snippet-start:[python.example_code.cloudwatch-logs.DeleteLogGroup]
    def delete_log_group(self, log_group_name: str) -> None:
        """
        Deletes a log group and all associated log streams, events, and metric filters.

        :param log_group_name: The name of the log group to delete.
        :raises ClientError: If the API call fails (other than ResourceNotFoundException).
        """
        try:
            self.logs_client.delete_log_group(logGroupName=log_group_name)
            logger.info(
                "Deleted log group '%s' and all associated resources.",
                log_group_name,
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.info(
                    "Log group '%s' not found — it may have already been deleted.",
                    log_group_name,
                )
            else:
                logger.error(
                    "Couldn't delete log group '%s'. Error: %s: %s",
                    log_group_name,
                    error.response["Error"]["Code"],
                    error.response["Error"]["Message"],
                )
                raise

    # snippet-end:[python.example_code.cloudwatch-logs.DeleteLogGroup]


# snippet-end:[python.example_code.cloudwatch-logs.CloudWatchLogsWrapper.class]
