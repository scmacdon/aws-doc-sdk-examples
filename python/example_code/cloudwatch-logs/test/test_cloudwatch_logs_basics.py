# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for the Amazon CloudWatch Logs Basics scenario.

These tests run against real AWS resources. They create, populate, query,
and clean up CloudWatch Logs resources.

Usage:
    pytest test_cloudwatch_logs_basics.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import uuid
from datetime import datetime, timezone

import boto3
import pytest
from botocore.exceptions import ClientError

from cloudwatch_logs_wrapper import CloudWatchLogsWrapper


@pytest.fixture(scope="module")
def logs_client():
    """Creates a shared boto3 CloudWatch Logs client."""
    return boto3.client("logs")


@pytest.fixture(scope="module")
def wrapper(logs_client):
    """Creates a shared CloudWatchLogsWrapper instance."""
    return CloudWatchLogsWrapper(logs_client)


@pytest.fixture(scope="module")
def log_group_name():
    """Generates a unique log group name for the test run."""
    suffix = uuid.uuid4().hex[:8]
    return f"/sdk-examples/integ-test-{suffix}"


@pytest.fixture(scope="module")
def log_stream_name():
    """Returns the log stream name used in tests."""
    return "test-stream-1"


@pytest.mark.integ
class TestCloudWatchLogsBasics:
    """Integration tests for CloudWatch Logs wrapper operations."""

    @pytest.fixture(autouse=True, scope="class")
    def setup_and_teardown(self, wrapper, log_group_name, log_stream_name):
        """
        Creates the log group and log stream before tests, and ensures
        cleanup after all tests complete.
        """
        # Setup
        wrapper.create_log_group(log_group_name)
        wrapper.create_log_stream(log_group_name, log_stream_name)

        yield

        # Teardown — always run cleanup
        try:
            wrapper.delete_log_group(log_group_name)
        except ClientError:
            pass

    def test_create_log_group_already_exists(self, wrapper, log_group_name):
        """Test that creating an existing log group is handled gracefully."""
        # Should not raise — ResourceAlreadyExistsException is handled.
        wrapper.create_log_group(log_group_name)

    def test_create_log_stream_already_exists(
        self, wrapper, log_group_name, log_stream_name
    ):
        """Test that creating an existing log stream is handled gracefully."""
        # Should not raise — ResourceAlreadyExistsException is handled.
        wrapper.create_log_stream(log_group_name, log_stream_name)

    def test_describe_log_groups(self, wrapper, log_group_name):
        """Test describing log groups with a name prefix."""
        log_groups = wrapper.describe_log_groups(
            log_group_name_prefix=log_group_name
        )
        assert len(log_groups) >= 1
        names = [g.get("logGroupName") for g in log_groups]
        assert log_group_name in names

    def test_put_and_get_log_events(
        self, wrapper, log_group_name, log_stream_name
    ):
        """Test putting and then retrieving log events."""
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        log_events = [
            {"timestamp": now_ms, "message": "[INFO] Test event 1"},
            {"timestamp": now_ms + 1000, "message": "[ERROR] Test event 2"},
            {"timestamp": now_ms + 2000, "message": "[WARNING] Test event 3"},
        ]

        response = wrapper.put_log_events(
            log_group_name, log_stream_name, log_events
        )
        assert response is not None

        # Wait for ingestion.
        time.sleep(5)

        events = wrapper.get_log_events(
            log_group_name, log_stream_name, start_from_head=True
        )
        assert len(events) >= 3
        messages = [e.get("message") for e in events]
        assert "[INFO] Test event 1" in messages
        assert "[ERROR] Test event 2" in messages

    def test_describe_log_streams(self, wrapper, log_group_name):
        """Test describing log streams for the log group."""
        streams = wrapper.describe_log_streams(log_group_name)
        assert len(streams) >= 1
        stream_names = [s.get("logStreamName") for s in streams]
        assert "test-stream-1" in stream_names

    def test_filter_log_events(self, wrapper, log_group_name):
        """Test filtering log events with a pattern."""
        # Events were ingested in a prior test; wait may already be sufficient.
        error_events = wrapper.filter_log_events(log_group_name, "ERROR")
        assert isinstance(error_events, list)
        # We should find at least 1 ERROR event from the put_and_get test.
        assert len(error_events) >= 1

    def test_put_and_describe_metric_filter(self, wrapper, log_group_name):
        """Test creating and then describing a metric filter."""
        filter_name = "TestErrorFilter"
        metric_namespace = "SDKExamples/IntegTest"
        metric_name = "TestErrorCount"

        wrapper.put_metric_filter(
            log_group_name=log_group_name,
            filter_name=filter_name,
            filter_pattern="ERROR",
            metric_name=metric_name,
            metric_namespace=metric_namespace,
            metric_value="1",
            default_value=0,
        )

        metric_filters = wrapper.describe_metric_filters(log_group_name)
        assert len(metric_filters) >= 1
        filter_names = [mf.get("filterName") for mf in metric_filters]
        assert filter_name in filter_names

    def test_delete_log_group_not_found(self, wrapper):
        """Test that deleting a nonexistent log group is handled gracefully."""
        # Should not raise — ResourceNotFoundException is handled.
        wrapper.delete_log_group("/sdk-examples/nonexistent-group-xyz123")


@pytest.mark.integ
class TestCloudWatchLogsHello:
    """Integration test for the Hello CloudWatch Logs example."""

    def test_hello_runs(self):
        """Test that the hello function runs without error."""
        from cloudwatch_logs_hello import hello_cloudwatch_logs

        # Should not raise.
        hello_cloudwatch_logs()


@pytest.mark.integ
class TestCloudWatchLogsScenario:
    """Integration test for the full scenario."""

    def test_scenario_runs(self):
        """Test that the full scenario runs end-to-end without error."""
        from scenarios.cloudwatch_logs_basics_scenario import CloudWatchLogsScenario

        wrapper = CloudWatchLogsWrapper.from_client()
        scenario = CloudWatchLogsScenario(wrapper)
        scenario.run_scenario()
