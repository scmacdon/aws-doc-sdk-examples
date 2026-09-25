# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the Amazon Kinesis Data Streams basics scenario.
These tests use botocore.stub.Stubber to mock all AWS API calls —
no real AWS credentials or network access required.

Run with:  pytest test_kinesis_basics.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime, timezone

import boto3
import pytest
from botocore.stub import Stubber

from kinesis_wrapper import KinesisStreamWrapper


STREAM_NAME = "unit-test-stream"
STREAM_ARN = "arn:aws:kinesis:us-east-1:123456789012:stream/unit-test-stream"
SHARD_ID_0 = "shardId-000000000000"
SHARD_ID_1 = "shardId-000000000001"
SHARD_ITERATOR = (
    "AAAAAAAAAAETYyAYzd665+8e0X7JTsASDM/Hr2rSwc0X2qz93iuA3udrjTH+ikQvpQk/1ZcMML"
)
NEXT_SHARD_ITERATOR = (
    "AAAAAAAAAT+8e0X7JTsASDM/Hr2rSwc0X2qz93iuA3udrjTH+ikQvpQk/1ZcMMLzRdAesqBBBB"
)
SEQUENCE_NUMBER = "49590338271490256608559692538361571095921575989136588898"


def _describe_stream_response(status="ACTIVE"):
    """Build a valid DescribeStream response with all required fields."""
    return {
        "StreamDescription": {
            "StreamName": STREAM_NAME,
            "StreamARN": STREAM_ARN,
            "StreamStatus": status,
            "StreamModeDetails": {"StreamMode": "PROVISIONED"},
            "Shards": [
                {
                    "ShardId": SHARD_ID_0,
                    "HashKeyRange": {
                        "StartingHashKey": "0",
                        "EndingHashKey": "170141183460469231731687303715884105727",
                    },
                    "SequenceNumberRange": {
                        "StartingSequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    },
                },
                {
                    "ShardId": SHARD_ID_1,
                    "HashKeyRange": {
                        "StartingHashKey": "170141183460469231731687303715884105728",
                        "EndingHashKey": "340282366920938463463374607431768211455",
                    },
                    "SequenceNumberRange": {
                        "StartingSequenceNumber": "49590338271512557353757223161502106818841590619171160066",
                    },
                },
            ],
            "HasMoreShards": False,
            "RetentionPeriodHours": 24,
            "StreamCreationTimestamp": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "EnhancedMonitoring": [
                {"ShardLevelMetrics": ["IncomingBytes", "OutgoingRecords"]}
            ],
            "EncryptionType": "NONE",
        }
    }


class TestKinesisBasicsIntegration:
    """Unit tests for the Kinesis Data Streams basics scenario using Stubber."""

    def test_full_scenario(self):
        """
        Tests the complete Kinesis basics scenario end-to-end using Stubber:
        list, create, describe, put record, put records, get shard iterator,
        get records, describe summary, update shard count, describe (after
        scaling), and delete.
        """
        client = boto3.client("kinesis", region_name="us-east-1")
        stubber = Stubber(client)

        # 1. ListStreams
        stubber.add_response(
            "list_streams",
            {
                "StreamNames": ["existing-stream"],
                "HasMoreStreams": False,
                "StreamSummaries": [
                    {
                        "StreamName": "existing-stream",
                        "StreamARN": "arn:aws:kinesis:us-east-1:123456789012:stream/existing-stream",
                        "StreamStatus": "ACTIVE",
                        "StreamModeDetails": {"StreamMode": "ON_DEMAND"},
                        "StreamCreationTimestamp": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    }
                ],
            },
            {"Limit": 10},
        )

        # 2. CreateStream
        stubber.add_response(
            "create_stream",
            {},
            {
                "StreamName": STREAM_NAME,
                "ShardCount": 2,
                "StreamModeDetails": {"StreamMode": "PROVISIONED"},
            },
        )

        # 3. DescribeStream — wait for ACTIVE
        stubber.add_response(
            "describe_stream",
            _describe_stream_response("ACTIVE"),
            {"StreamName": STREAM_NAME},
        )

        # 4. PutRecord — single record
        sensor_payload = {
            "sensor_id": "sensor-1",
            "temperature": 22.5,
            "test": True,
        }
        stubber.add_response(
            "put_record",
            {
                "ShardId": SHARD_ID_0,
                "SequenceNumber": SEQUENCE_NUMBER,
                "EncryptionType": "NONE",
            },
            {
                "StreamName": STREAM_NAME,
                "Data": json.dumps(sensor_payload),
                "PartitionKey": "sensor-1",
            },
        )

        # 5. PutRecords — batch of 5 records
        # Build the exact records the wrapper will produce
        batch_records_input = list()
        for i in range(5):
            batch_records_input.append(
                {
                    "Data": {"sensor_id": f"sensor-{i}", "value": i * 10},
                    "PartitionKey": f"sensor-{i % 3}",
                }
            )
        expected_put_records_request = list()
        for rec in batch_records_input:
            expected_put_records_request.append(
                {
                    "Data": json.dumps(rec["Data"]),
                    "PartitionKey": rec["PartitionKey"],
                }
            )
        # Note: FailedRecordCount has min value 1 per the API spec, so we
        # OMIT it from the response when all records succeed. The wrapper
        # uses .get("FailedRecordCount", 0) which handles the absent key.
        put_records_response_entries = list()
        for i in range(5):
            put_records_response_entries.append(
                {
                    "SequenceNumber": f"4959033827149025660855969253836157109592157598913{i}",
                    "ShardId": SHARD_ID_0 if i % 2 == 0 else SHARD_ID_1,
                }
            )
        stubber.add_response(
            "put_records",
            {
                "Records": put_records_response_entries,
                "EncryptionType": "NONE",
            },
            {
                "StreamName": STREAM_NAME,
                "Records": expected_put_records_request,
            },
        )

        # 6. GetShardIterator
        stubber.add_response(
            "get_shard_iterator",
            {"ShardIterator": SHARD_ITERATOR},
            {
                "StreamName": STREAM_NAME,
                "ShardId": SHARD_ID_0,
                "ShardIteratorType": "TRIM_HORIZON",
            },
        )

        # 7. GetRecords
        record_data = json.dumps(
            {"sensor_id": "sensor-1", "temperature": 22.5, "test": True}
        ).encode("utf-8")
        stubber.add_response(
            "get_records",
            {
                "Records": [
                    {
                        "SequenceNumber": SEQUENCE_NUMBER,
                        "ApproximateArrivalTimestamp": datetime(
                            2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc
                        ),
                        "Data": record_data,
                        "PartitionKey": "sensor-1",
                    }
                ],
                "NextShardIterator": NEXT_SHARD_ITERATOR,
                "MillisBehindLatest": 0,
            },
            {"ShardIterator": SHARD_ITERATOR, "Limit": 10},
        )

        # 8. DescribeStreamSummary
        stubber.add_response(
            "describe_stream_summary",
            {
                "StreamDescriptionSummary": {
                    "StreamName": STREAM_NAME,
                    "StreamARN": STREAM_ARN,
                    "StreamStatus": "ACTIVE",
                    "StreamModeDetails": {"StreamMode": "PROVISIONED"},
                    "RetentionPeriodHours": 24,
                    "StreamCreationTimestamp": datetime(
                        2024, 1, 1, tzinfo=timezone.utc
                    ),
                    "EnhancedMonitoring": [
                        {"ShardLevelMetrics": ["IncomingBytes", "OutgoingRecords"]}
                    ],
                    "EncryptionType": "NONE",
                    "OpenShardCount": 2,
                }
            },
            {"StreamName": STREAM_NAME},
        )

        # 9. UpdateShardCount
        stubber.add_response(
            "update_shard_count",
            {
                "StreamName": STREAM_NAME,
                "CurrentShardCount": 2,
                "TargetShardCount": 4,
                "StreamARN": STREAM_ARN,
            },
            {
                "StreamName": STREAM_NAME,
                "TargetShardCount": 4,
                "ScalingType": "UNIFORM_SCALING",
            },
        )

        # 10. DescribeStream again — after scaling, wait for ACTIVE
        stubber.add_response(
            "describe_stream",
            _describe_stream_response("ACTIVE"),
            {"StreamName": STREAM_NAME},
        )

        # 11. DeleteStream
        stubber.add_response(
            "delete_stream",
            {},
            {
                "StreamName": STREAM_NAME,
                "EnforceConsumerDeletion": True,
            },
        )

        stubber.activate()

        wrapper = KinesisStreamWrapper(client)

        try:
            # 1. List streams
            response = wrapper.list_streams(limit=10)
            assert "StreamNames" in response
            assert isinstance(response["StreamNames"], list)

            # 2. Create stream
            wrapper.create_stream(STREAM_NAME, shard_count=2)

            # 3. Wait for ACTIVE (one call since stub returns ACTIVE)
            details = wrapper.wait_for_stream_active(STREAM_NAME, max_wait_seconds=90)
            assert details["StreamStatus"] == "ACTIVE"
            assert len(details["Shards"]) >= 2

            # 4. Put a single record
            put_response = wrapper.put_record(
                stream_name=STREAM_NAME,
                data=sensor_payload,
                partition_key="sensor-1",
            )
            assert "ShardId" in put_response
            assert "SequenceNumber" in put_response

            # 5. Put a batch of records
            batch_response = wrapper.put_records(
                stream_name=STREAM_NAME, records=batch_records_input
            )
            assert len(batch_response.get("Records", list())) == 5

            # 6. Get shard iterator
            shard_iterator = wrapper.get_shard_iterator(
                stream_name=STREAM_NAME,
                shard_id=SHARD_ID_0,
                iterator_type="TRIM_HORIZON",
            )
            assert isinstance(shard_iterator, str)
            assert len(shard_iterator) > 0

            # 7. Get records
            get_response = wrapper.get_records(
                shard_iterator=shard_iterator, limit=10
            )
            assert "Records" in get_response
            assert "MillisBehindLatest" in get_response
            all_records = get_response.get("Records", list())
            assert len(all_records) >= 1

            # Verify record data is valid JSON
            for record in all_records:
                data = record.get("Data", b"")
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                parsed = json.loads(data)
                assert isinstance(parsed, dict)

            # 8. Describe stream summary
            summary = wrapper.describe_stream_summary(STREAM_NAME)
            assert summary["StreamName"] == STREAM_NAME
            assert summary["StreamStatus"] == "ACTIVE"
            assert "OpenShardCount" in summary
            assert "RetentionPeriodHours" in summary
            assert "EncryptionType" in summary
            stream_mode = summary.get("StreamModeDetails", dict()).get(
                "StreamMode", ""
            )
            assert stream_mode == "PROVISIONED"

            # 9. Update shard count (2 → 4)
            update_response = wrapper.update_shard_count(
                stream_name=STREAM_NAME,
                target_shard_count=4,
            )
            assert update_response.get("CurrentShardCount") == 2
            assert update_response.get("TargetShardCount") == 4

            # 10. Wait for ACTIVE after scaling
            details_after = wrapper.wait_for_stream_active(
                STREAM_NAME, max_wait_seconds=180
            )
            assert details_after["StreamStatus"] == "ACTIVE"

        finally:
            # 11. Delete stream — always clean up
            wrapper.delete_stream(STREAM_NAME)

        stubber.assert_no_pending_responses()
        stubber.deactivate()

    def test_hello_kinesis(self):
        """Tests the Hello Kinesis flow — just listing streams — using Stubber."""
        client = boto3.client("kinesis", region_name="us-east-1")
        stubber = Stubber(client)

        stubber.add_response(
            "list_streams",
            {
                "StreamNames": ["my-test-stream"],
                "HasMoreStreams": False,
                "StreamSummaries": [
                    {
                        "StreamName": "my-test-stream",
                        "StreamARN": "arn:aws:kinesis:us-east-1:123456789012:stream/my-test-stream",
                        "StreamStatus": "ACTIVE",
                        "StreamModeDetails": {"StreamMode": "ON_DEMAND"},
                        "StreamCreationTimestamp": datetime(
                            2024, 1, 1, tzinfo=timezone.utc
                        ),
                    }
                ],
            },
            {"Limit": 10},
        )

        stubber.activate()

        wrapper = KinesisStreamWrapper(client)
        response = wrapper.list_streams(limit=10)
        assert "StreamNames" in response
        assert isinstance(response["StreamNames"], list)
        assert "HasMoreStreams" in response

        stubber.assert_no_pending_responses()
        stubber.deactivate()
