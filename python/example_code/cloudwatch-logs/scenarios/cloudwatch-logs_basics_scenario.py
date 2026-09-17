# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Amazon CloudWatch Logs Basics Scenario

This scenario demonstrates the complete lifecycle of CloudWatch Logs management:
  1. Create and configure a CloudWatch Logs log group
  2. Ingest structured application log data
  3. Retrieve and browse log events
  4. Search and filter logs by patterns
  5. Create metric filters to generate CloudWatch metrics
  6. Clean up all resources

Usage:
    python scenario_cloudwatch_logs_basics.py
"""

import logging
import sys
import os
import time
import uuid
from datetime import datetime, timezone

import boto3

# Add parent directory to path to import wrapper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cloudwatch_logs_wrapper import CloudWatchLogsWrapper

logger = logging.getLogger(__name__)

DASHES = "-" * 80


# snippet-start:[python.example_code.cloudwatch-logs.CloudWatchLogsScenario]
class CloudWatchLogsScenario:
    """Runs the Amazon CloudWatch Logs Basics interactive scenario."""

    def __init__(self, wrapper: CloudWatchLogsWrapper) -> None:
        """
        Initializes the scenario.

        :param wrapper: An instance of CloudWatchLogsWrapper.
        """
        self.wrapper = wrapper
        self.log_group_name = ""
        self.log_stream_name = "application-stream-1"

    def run_scenario(self) -> None:
        """Runs the full CloudWatch Logs Basics scenario."""
        print(DASHES)
        print("Welcome to the Amazon CloudWatch Logs Basics Scenario!")
        print(DASHES)
        print(
            "This scenario demonstrates how to:\n"
            "  1. Create and configure a CloudWatch Logs log group\n"
            "  2. Ingest structured application log data\n"
            "  3. Retrieve and browse log events\n"
            "  4. Search and filter logs by patterns\n"
            "  5. Create metric filters to generate CloudWatch metrics\n"
            "  6. Clean up all resources\n"
        )
        print("Let's get started!")
        print(DASHES)

        # Setup — generate a unique log group name.
        suffix = uuid.uuid4().hex[:6]
        self.log_group_name = f"/sdk-examples/cloudwatch-logs-basics-{suffix}"

        print(f"\nCreating log group: {self.log_group_name}")
        self.wrapper.create_log_group(self.log_group_name)
        print("Successfully created log group.")

        print(f"\nCreating log stream: {self.log_stream_name}")
        self.wrapper.create_log_stream(self.log_group_name, self.log_stream_name)
        print("Successfully created log stream.")

        try:
            self._step1_describe_log_group()
            self._step2_ingest_log_events()
            self._step3_describe_log_streams()
            self._step4_retrieve_log_events()
            self._step5_filter_log_events()
            self._step6_create_metric_filter()
            self._step7_verify_metric_filter()
        finally:
            self._cleanup()

    def _step1_describe_log_group(self) -> None:
        """Step 1: Describe the log group to verify creation."""
        print(f"\n{DASHES}")
        print("Step 1: Describing the log group")
        print(DASHES)

        log_groups = self.wrapper.describe_log_groups(
            log_group_name_prefix=self.log_group_name
        )

        target_group = None
        for group in log_groups:
            if group.get("logGroupName") == self.log_group_name:
                target_group = group
                break

        if target_group is None:
            print("Could not find the log group. Exiting.")
            return

        creation_time_ms = target_group.get("creationTime", 0)
        creation_dt = datetime.fromtimestamp(
            creation_time_ms / 1000, tz=timezone.utc
        )
        retention = target_group.get("retentionInDays", None)
        retention_display = (
            f"{retention} days" if retention is not None else "Never expire"
        )
        log_group_class = target_group.get("logGroupClass", "STANDARD")

        print("Log Group Details:")
        print(f"  Name: {target_group.get('logGroupName', 'N/A')}")
        print(f"  ARN: {target_group.get('arn', 'N/A')}")
        print(f"  Created: {creation_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  Class: {log_group_class}")
        print(f"  Retention: {retention_display}")
        print(f"  Metric Filters: {target_group.get('metricFilterCount', 0)}")
        print(f"  Stored Bytes: {target_group.get('storedBytes', 0)}")

    def _step2_ingest_log_events(self) -> None:
        """Step 2: Ingest sample log events into the log stream."""
        print(f"\n{DASHES}")
        print("Step 2: Ingesting log events")
        print(DASHES)

        print("Preparing 15 sample log events simulating a web application...")

        # Build log events with chronological timestamps.
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        log_messages = [
            ("[INFO] RequestId: req-001 - Application started successfully", 0),
            ("[INFO] RequestId: req-002 - Received GET /api/orders", 1000),
            ("[INFO] RequestId: req-002 - Processing order lookup", 2000),
            ("[WARNING] RequestId: req-002 - Slow database query detected, latency: 2500ms", 3000),
            ("[INFO] RequestId: req-002 - Request completed in 2847ms", 4000),
            ("[INFO] RequestId: req-003 - Received POST /api/orders", 5000),
            ("[INFO] RequestId: req-003 - Order created successfully", 6000),
            ("[INFO] RequestId: req-004 - Received GET /api/health", 7000),
            ("[ERROR] RequestId: req-005 - Failed to connect to payment service", 8000),
            ("[INFO] RequestId: req-006 - Received GET /api/products", 9000),
            ("[WARNING] RequestId: req-006 - Cache miss for product catalog", 10000),
            ("[INFO] RequestId: req-007 - Received DELETE /api/orders/123", 11000),
            ("[ERROR] RequestId: req-008 - Null pointer in order handler", 12000),
            ("[WARNING] RequestId: req-009 - High memory usage detected: 85%", 13000),
            ("[INFO] RequestId: req-010 - Batch processing completed", 14000),
        ]

        log_events = list()
        info_count = 0
        warning_count = 0
        error_count = 0
        for message, offset in log_messages:
            log_events.append(
                {"timestamp": now_ms + offset, "message": message}
            )
            if "[INFO]" in message:
                info_count += 1
            elif "[WARNING]" in message:
                warning_count += 1
            elif "[ERROR]" in message:
                error_count += 1

        print(f"  - {info_count} INFO events")
        print(f"  - {warning_count} WARNING events")
        print(f"  - {error_count} ERROR events")

        print(f"\nUploading log events to stream '{self.log_stream_name}'...")
        response = self.wrapper.put_log_events(
            self.log_group_name, self.log_stream_name, log_events
        )

        print(f"Successfully uploaded {len(log_events)} log events.")

        rejected_info = response.get("rejectedLogEventsInfo", None)
        if rejected_info is not None:
            print(f"Some events were rejected: {rejected_info}")
        else:
            print("No rejected events.")

        print("Waiting for log ingestion to complete...")
        time.sleep(3)

    def _step3_describe_log_streams(self) -> None:
        """Step 3: Describe log streams to verify data ingestion."""
        print(f"\n{DASHES}")
        print("Step 3: Describing log streams")
        print(DASHES)

        print(f"Log streams for '{self.log_group_name}':\n")

        streams = self.wrapper.describe_log_streams(self.log_group_name)

        for stream in streams:
            name = stream.get("logStreamName", "N/A")
            created_ms = stream.get("creationTime", 0)
            created_dt = datetime.fromtimestamp(
                created_ms / 1000, tz=timezone.utc
            )
            first_event_ms = stream.get("firstEventTimestamp", None)
            last_event_ms = stream.get("lastEventTimestamp", None)
            last_ingestion_ms = stream.get("lastIngestionTime", None)
            stored_bytes = stream.get("storedBytes", 0)

            print(f"  Stream: {name}")
            print(
                f"    Created: {created_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            if first_event_ms is not None:
                first_dt = datetime.fromtimestamp(
                    first_event_ms / 1000, tz=timezone.utc
                )
                print(
                    f"    First Event: {first_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
            if last_event_ms is not None:
                last_dt = datetime.fromtimestamp(
                    last_event_ms / 1000, tz=timezone.utc
                )
                print(
                    f"    Last Event: {last_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
            if last_ingestion_ms is not None:
                ingestion_dt = datetime.fromtimestamp(
                    last_ingestion_ms / 1000, tz=timezone.utc
                )
                print(
                    f"    Last Ingestion: {ingestion_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
            print(f"    Stored Bytes: {stored_bytes}")

    def _step4_retrieve_log_events(self) -> None:
        """Step 4: Retrieve log events from the log stream."""
        print(f"\n{DASHES}")
        print("Step 4: Retrieving log events with GetLogEvents")
        print(DASHES)

        print(
            f"Retrieving log events from stream '{self.log_stream_name}' (oldest first)...\n"
        )

        events = self.wrapper.get_log_events(
            self.log_group_name,
            self.log_stream_name,
            start_from_head=True,
        )

        for event in events:
            timestamp_ms = event.get("timestamp", 0)
            event_dt = datetime.fromtimestamp(
                timestamp_ms / 1000, tz=timezone.utc
            )
            message = event.get("message", "")
            print(f"[{event_dt.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

        print(f"\nRetrieved {len(events)} log events from the stream.")

    def _step5_filter_log_events(self) -> None:
        """Step 5: Filter log events with pattern matching."""
        print(f"\n{DASHES}")
        print("Step 5: Filtering log events with pattern matching")
        print(DASHES)

        # Filter for ERROR events.
        print("\nSearching for ERROR events across all streams...\n")
        error_events = self.wrapper.filter_log_events(
            self.log_group_name, "ERROR"
        )

        for event in error_events:
            stream_name = event.get("logStreamName", "N/A")
            timestamp_ms = event.get("timestamp", 0)
            event_dt = datetime.fromtimestamp(
                timestamp_ms / 1000, tz=timezone.utc
            )
            message = event.get("message", "")
            print(f"[{stream_name}] [{event_dt.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

        print(f"\nFound {len(error_events)} ERROR events.")

        # Filter for WARNING events.
        print("\nSearching for WARNING events across all streams...")
        warning_events = self.wrapper.filter_log_events(
            self.log_group_name, "WARNING"
        )
        print(f"Found {len(warning_events)} WARNING events.")

        print(
            "\nNote: FilterLogEvents searches across ALL log streams in the log group and\n"
            "supports powerful filter patterns. GetLogEvents retrieves events from a\n"
            "single specific stream."
        )

    def _step6_create_metric_filter(self) -> None:
        """Step 6: Create a metric filter on the log group."""
        print(f"\n{DASHES}")
        print("Step 6: Creating a metric filter")
        print(DASHES)

        filter_name = "ErrorCountFilter"
        metric_namespace = "SDKExamples/CloudWatchLogsBasics"
        metric_name = "ApplicationErrorCount"

        print(f"Creating metric filter '{filter_name}' on log group...\n")
        print("Filter Configuration:")
        print(f"  Filter Name: {filter_name}")
        print("  Pattern: ERROR")
        print(f"  Metric Namespace: {metric_namespace}")
        print(f"  Metric Name: {metric_name}")
        print("  Metric Value: 1 (per matching event)")

        self.wrapper.put_metric_filter(
            log_group_name=self.log_group_name,
            filter_name=filter_name,
            filter_pattern="ERROR",
            metric_name=metric_name,
            metric_namespace=metric_namespace,
            metric_value="1",
            default_value=0,
        )

        print("\nSuccessfully created metric filter.")
        print(
            "\nThis metric filter will automatically publish a CloudWatch metric every time\n"
            "a log event containing 'ERROR' is ingested into this log group. You can use\n"
            "this metric to create alarms and dashboards for monitoring application errors."
        )

    def _step7_verify_metric_filter(self) -> None:
        """Step 7: Verify the metric filter by describing metric filters."""
        print(f"\n{DASHES}")
        print("Step 7: Verifying metric filters with DescribeMetricFilters")
        print(DASHES)

        print("Listing metric filters for the log group...\n")

        metric_filters = self.wrapper.describe_metric_filters(self.log_group_name)

        for i, mf in enumerate(metric_filters, start=1):
            print(f"Metric Filter #{i}:")
            print(f"  Name: {mf.get('filterName', 'N/A')}")
            print(f"  Pattern: {mf.get('filterPattern', 'N/A')}")

            transformations = mf.get("metricTransformations", list())
            for transformation in transformations:
                print("  Metric Transformation:")
                print(f"    Namespace: {transformation.get('metricNamespace', 'N/A')}")
                print(f"    Metric Name: {transformation.get('metricName', 'N/A')}")
                print(f"    Metric Value: {transformation.get('metricValue', 'N/A')}")
                print(f"    Default Value: {transformation.get('defaultValue', 'N/A')}")

        print(f"\nTotal metric filters found: {len(metric_filters)}")
        print("Metric filter configuration verified successfully.")

    def _cleanup(self) -> None:
        """Clean up all resources created during the scenario."""
        print(f"\n{DASHES}")
        print("Cleanup")
        print(DASHES)

        print(f"Deleting log group '{self.log_group_name}'...")
        print("  This also deletes all log streams, events, and metric filters.\n")

        self.wrapper.delete_log_group(self.log_group_name)

        print("Successfully deleted log group and all associated resources.")
        print(f"\nCleanup Summary:")
        print(f"  - Log group deleted: {self.log_group_name}")
        print(f"  - Log stream deleted: {self.log_stream_name}")
        print("  - Metric filter deleted: ErrorCountFilter")
        print("  - All log events permanently removed")
        print(f"\n{DASHES}")
        print("CloudWatch Logs Basics scenario completed successfully!")
        print(DASHES)


# snippet-end:[python.example_code.cloudwatch-logs.CloudWatchLogsScenario]


def main() -> None:
    """Entry point for the CloudWatch Logs Basics scenario."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    wrapper = CloudWatchLogsWrapper.from_client()
    scenario = CloudWatchLogsScenario(wrapper)
    scenario.run_scenario()


if __name__ == "__main__":
    main()
