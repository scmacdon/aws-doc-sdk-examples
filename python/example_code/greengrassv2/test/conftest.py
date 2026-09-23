# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Contains common test fixtures and configuration used to run the GreengrassV2
unit and integration tests.
"""

import os
import sys

import boto3
import pytest

script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the example directory so tests can import the wrapper module.
sys.path.append(os.path.dirname(script_dir))
# Add the scenarios directory so tests can import the scenario module.
sys.path.append(os.path.join(os.path.dirname(script_dir), "scenarios"))
# Add the repo's `python` folder so demo_tools can be imported.
sys.path.append(os.path.join(script_dir, "..", "..", ".."))

from greengrassv2_wrapper import GreengrassV2Wrapper


def pytest_configure(config):
    """Registers the custom ``integ`` marker to avoid unknown-mark warnings."""
    config.addinivalue_line(
        "markers",
        "integ: integration test that requires and uses AWS resources. "
        "Use of this tag is likely to incur charges on your account.",
    )


@pytest.fixture(scope="module")
def greengrassv2_client():
    """Creates a shared Greengrass V2 client for integration tests."""
    return boto3.client("greengrassv2")


@pytest.fixture(scope="module")
def iot_client():
    """Creates a shared IoT client for thing group management."""
    return boto3.client("iot")


@pytest.fixture(scope="module")
def wrapper(greengrassv2_client):
    """Creates a wrapper instance for integration tests."""
    return GreengrassV2Wrapper(greengrassv2_client)


@pytest.fixture(scope="module")
def unique_suffix():
    """Generates a unique suffix used across a test module."""
    import uuid

    return str(uuid.uuid4())[:8]
