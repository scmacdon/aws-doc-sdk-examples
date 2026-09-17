# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for ecs_wrapper.py
"""

import pytest
import boto3
from botocore.stub import Stubber
from botocore.exceptions import ClientError

from ecs_wrapper import EcsWrapper

CLUSTER_NAME = "test-cluster"

@pytest.fixture()
def ecs_stubber():
    client = boto3.client("ecs", region_name="us-west-2")
    stubber = Stubber(client)
    wrapper = EcsWrapper(client)
    stubber.activate()
    yield wrapper, stubber
    stubber.deactivate()

class TestEcsWrapper:
    def test_create_cluster(self, ecs_stubber):
        wrapper, stubber = ecs_stubber
        expected_params = {
            "clusterName": CLUSTER_NAME,
            "settings": [{"name": "containerInsights", "value": "enabled"}],
        }
        response = {
            "cluster": {
                "clusterArn": f"arn:aws:ecs:us-west-2:123456789012:cluster/{CLUSTER_NAME}",
                "clusterName": CLUSTER_NAME,
                "status": "ACTIVE",
                "registeredContainerInstancesCount": 0,
                "runningTasksCount": 0,
                "pendingTasksCount": 0,
                "activeServicesCount": 0,
                "settings": [{"name": "containerInsights", "value": "enabled"}],
                "capacityProviders": [],
                "defaultCapacityProviderStrategy": [],
                "statistics": [],
                "tags": [],
                "attachments": [],
            }
        }
        stubber.add_response("create_cluster", response, expected_params)
        result = wrapper.create_cluster(CLUSTER_NAME)
        assert result["clusterName"] == CLUSTER_NAME
        assert result["status"] == "ACTIVE"
        stubber.assert_no_pending_responses()
