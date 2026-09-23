# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the AWS IoT Greengrass V2 wrapper (``GreengrassV2Wrapper``).

These tests use the botocore ``Stubber`` to queue canned service responses so
each wrapper method is exercised without making any real AWS calls or incurring
charges. Both success paths and representative error paths are covered.

Run with:  python -m pytest test/test_greengrassv2_unit.py -v
"""

import boto3
import pytest
from botocore.stub import Stubber
from botocore.exceptions import ClientError
from datetime import datetime

from greengrassv2_wrapper import GreengrassV2Wrapper

COMPONENT_NAME = "com.example.GreengrassBasics"
COMPONENT_ARN = "arn:aws:greengrass:us-east-1:123456789012:components:" + COMPONENT_NAME
COMPONENT_V1_ARN = COMPONENT_ARN + ":versions:1.0.0"
COMPONENT_V2_ARN = COMPONENT_ARN + ":versions:2.0.0"


@pytest.fixture
def stub_wrapper():
    """
    Yields a (wrapper, stubber) pair backed by a stubbed Greengrass V2 client.

    The stubber is activated for the duration of the test and asserts on exit
    that every queued response was consumed, so tests verify that the expected
    calls were actually made.
    """
    client = boto3.client("greengrassv2", region_name="us-east-1")
    stubber = Stubber(client)
    stubber.activate()
    wrapper = GreengrassV2Wrapper(client)
    yield wrapper, stubber
    stubber.assert_no_pending_responses()
    stubber.deactivate()


# ---------------------------------------------------------------------------
# Helpers that don't touch AWS
# ---------------------------------------------------------------------------


def test_component_arn_from_version_arn_strips_version():
    assert (
        GreengrassV2Wrapper.component_arn_from_version_arn(COMPONENT_V1_ARN)
        == COMPONENT_ARN
    )


def test_component_arn_from_version_arn_without_version_is_unchanged():
    # A version-less ARN (no ":versions:") is returned as-is.
    assert (
        GreengrassV2Wrapper.component_arn_from_version_arn(COMPONENT_ARN)
        == COMPONENT_ARN
    )


# ---------------------------------------------------------------------------
# list_core_devices
# ---------------------------------------------------------------------------


def test_list_core_devices(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "list_core_devices",
        {
            "coreDevices": [
                {"coreDeviceThingName": "device-1", "status": "HEALTHY"},
                {"coreDeviceThingName": "device-2", "status": "UNHEALTHY"},
            ]
        },
    )
    devices = wrapper.list_core_devices()
    assert len(devices) == 2
    assert devices[0]["coreDeviceThingName"] == "device-1"


def test_list_core_devices_with_status_filter(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "list_core_devices",
        {"coreDevices": [{"coreDeviceThingName": "device-1", "status": "HEALTHY"}]},
        {"status": "HEALTHY"},
    )
    devices = wrapper.list_core_devices(status="HEALTHY")
    assert len(devices) == 1


def test_list_core_devices_validation_error(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_client_error(
        "list_core_devices",
        service_error_code="ValidationException",
        service_message="Invalid status filter.",
    )
    with pytest.raises(ClientError) as exc:
        wrapper.list_core_devices(status="BOGUS")
    assert exc.value.response["Error"]["Code"] == "ValidationException"


# ---------------------------------------------------------------------------
# create_component_version
# ---------------------------------------------------------------------------


def _sample_recipe(version="1.0.0"):
    return {
        "RecipeFormatVersion": "2020-01-25",
        "ComponentName": COMPONENT_NAME,
        "ComponentVersion": version,
        "ComponentPublisher": "AWS Code Examples",
        "Manifests": [{"Platform": {"os": "linux"}}],
    }


def test_create_component_version(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "create_component_version",
        {
            "arn": COMPONENT_V1_ARN,
            "componentName": COMPONENT_NAME,
            "componentVersion": "1.0.0",
            "creationTimestamp": datetime(2026, 1, 1),
            "status": {"componentState": "REQUESTED"},
        },
    )
    response = wrapper.create_component_version(_sample_recipe())
    assert response["arn"] == COMPONENT_V1_ARN
    assert response["componentVersion"] == "1.0.0"


def test_create_component_version_conflict_error(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_client_error(
        "create_component_version",
        service_error_code="ConflictException",
        service_message="Component version already exists.",
    )
    with pytest.raises(ClientError) as exc:
        wrapper.create_component_version(_sample_recipe())
    assert exc.value.response["Error"]["Code"] == "ConflictException"


# ---------------------------------------------------------------------------
# list_component_versions
# ---------------------------------------------------------------------------


def test_list_component_versions(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "list_component_versions",
        {
            "componentVersions": [
                {"componentName": COMPONENT_NAME, "componentVersion": "2.0.0"},
                {"componentName": COMPONENT_NAME, "componentVersion": "1.0.0"},
            ]
        },
        {"arn": COMPONENT_ARN},
    )
    versions = wrapper.list_component_versions(COMPONENT_ARN)
    assert [v["componentVersion"] for v in versions] == ["2.0.0", "1.0.0"]


def test_list_component_versions_not_found(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_client_error(
        "list_component_versions",
        service_error_code="ResourceNotFoundException",
        service_message="Component not found.",
    )
    with pytest.raises(ClientError) as exc:
        wrapper.list_component_versions(COMPONENT_ARN)
    assert exc.value.response["Error"]["Code"] == "ResourceNotFoundException"


# ---------------------------------------------------------------------------
# get_component
# ---------------------------------------------------------------------------


def test_get_component(stub_wrapper):
    wrapper, stubber = stub_wrapper
    recipe_bytes = b'{"ComponentName": "com.example.GreengrassBasics"}'
    stubber.add_response(
        "get_component",
        {"recipeOutputFormat": "JSON", "recipe": recipe_bytes},
        {"arn": COMPONENT_V2_ARN, "recipeOutputFormat": "JSON"},
    )
    response = wrapper.get_component(COMPONENT_V2_ARN)
    assert response["recipeOutputFormat"] == "JSON"
    assert response["recipe"] == recipe_bytes


# ---------------------------------------------------------------------------
# describe_component
# ---------------------------------------------------------------------------


def test_describe_component(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "describe_component",
        {
            "arn": COMPONENT_V2_ARN,
            "componentName": COMPONENT_NAME,
            "componentVersion": "2.0.0",
            "status": {"componentState": "DEPLOYABLE"},
        },
        {"arn": COMPONENT_V2_ARN},
    )
    response = wrapper.describe_component(COMPONENT_V2_ARN)
    assert response["status"]["componentState"] == "DEPLOYABLE"


# ---------------------------------------------------------------------------
# wait_for_component_deployable (polling)
# ---------------------------------------------------------------------------


def test_wait_for_component_deployable_success(stub_wrapper):
    wrapper, stubber = stub_wrapper
    # First poll returns non-deployable, second returns DEPLOYABLE.
    stubber.add_response(
        "describe_component",
        {"status": {"componentState": "REQUESTED"}},
        {"arn": COMPONENT_V1_ARN},
    )
    stubber.add_response(
        "describe_component",
        {"status": {"componentState": "DEPLOYABLE"}},
        {"arn": COMPONENT_V1_ARN},
    )
    result = wrapper.wait_for_component_deployable(
        COMPONENT_V1_ARN, max_attempts=3, delay_seconds=0
    )
    assert result is True


def test_wait_for_component_deployable_terminal_state(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "describe_component",
        {"status": {"componentState": "FAILED"}},
        {"arn": COMPONENT_V1_ARN},
    )
    result = wrapper.wait_for_component_deployable(
        COMPONENT_V1_ARN, max_attempts=3, delay_seconds=0
    )
    assert result is False


# ---------------------------------------------------------------------------
# create_deployment
# ---------------------------------------------------------------------------


def test_create_deployment(stub_wrapper):
    wrapper, stubber = stub_wrapper
    target_arn = "arn:aws:iot:us-east-1:123456789012:thinggroup/MyGroup"
    components = {COMPONENT_NAME: {"componentVersion": "2.0.0"}}
    stubber.add_response(
        "create_deployment",
        {"deploymentId": "dep-123", "iotJobId": "job-123"},
        {
            "targetArn": target_arn,
            "deploymentName": "MyDeployment",
            "components": components,
        },
    )
    response = wrapper.create_deployment(target_arn, "MyDeployment", components)
    assert response["deploymentId"] == "dep-123"


def test_create_deployment_validation_error(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_client_error(
        "create_deployment",
        service_error_code="ValidationException",
        service_message="Invalid target ARN.",
    )
    with pytest.raises(ClientError) as exc:
        wrapper.create_deployment("bad-arn", "MyDeployment", {})
    assert exc.value.response["Error"]["Code"] == "ValidationException"


# ---------------------------------------------------------------------------
# get_deployment
# ---------------------------------------------------------------------------


def test_get_deployment(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "get_deployment",
        {"deploymentId": "dep-123", "deploymentStatus": "ACTIVE"},
        {"deploymentId": "dep-123"},
    )
    response = wrapper.get_deployment("dep-123")
    assert response["deploymentStatus"] == "ACTIVE"


# ---------------------------------------------------------------------------
# list_deployments
# ---------------------------------------------------------------------------


def test_list_deployments(stub_wrapper):
    wrapper, stubber = stub_wrapper
    target_arn = "arn:aws:iot:us-east-1:123456789012:thinggroup/MyGroup"
    stubber.add_response(
        "list_deployments",
        {"deployments": [{"deploymentId": "dep-123", "deploymentStatus": "ACTIVE"}]},
        {"targetArn": target_arn, "historyFilter": "ALL"},
    )
    deployments = wrapper.list_deployments(target_arn=target_arn, history_filter="ALL")
    assert len(deployments) == 1
    assert deployments[0]["deploymentId"] == "dep-123"


# ---------------------------------------------------------------------------
# cancel_deployment
# ---------------------------------------------------------------------------


def test_cancel_deployment(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response(
        "cancel_deployment",
        {"message": "Deployment canceled."},
        {"deploymentId": "dep-123"},
    )
    response = wrapper.cancel_deployment("dep-123")
    assert "message" in response


def test_cancel_deployment_conflict_error(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_client_error(
        "cancel_deployment",
        service_error_code="ConflictException",
        service_message="Deployment already completed.",
    )
    with pytest.raises(ClientError) as exc:
        wrapper.cancel_deployment("dep-123")
    assert exc.value.response["Error"]["Code"] == "ConflictException"


# ---------------------------------------------------------------------------
# delete_component
# ---------------------------------------------------------------------------


def test_delete_component(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_response("delete_component", {}, {"arn": COMPONENT_V1_ARN})
    # Returns None on success and consumes the queued response.
    assert wrapper.delete_component(COMPONENT_V1_ARN) is None


def test_delete_component_conflict_error(stub_wrapper):
    wrapper, stubber = stub_wrapper
    stubber.add_client_error(
        "delete_component",
        service_error_code="ConflictException",
        service_message="Component is in use by a deployment.",
    )
    with pytest.raises(ClientError) as exc:
        wrapper.delete_component(COMPONENT_V1_ARN)
    assert exc.value.response["Error"]["Code"] == "ConflictException"
