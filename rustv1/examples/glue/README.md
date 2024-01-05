# AWS Glue code examples for the SDK for Rust

## Overview

Shows how to use the AWS SDK for Rust to work with AWS Glue.

<!--custom.overview.start-->
<!--custom.overview.end-->

_AWS Glue is a scalable, serverless data integration service that makes it easy to discover, prepare, and combine data for analytics, machine learning, and application development._

## ⚠ Important

* Running this code might result in charges to your AWS account. For more details, see [AWS Pricing](https://aws.amazon.com/pricing/) and [Free Tier](https://aws.amazon.com/free/).
* Running the tests might result in charges to your AWS account.
* We recommend that you grant your code least privilege. At most, grant only the minimum permissions required to perform the task. For more information, see [Grant least privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege).
* This code is not tested in every AWS Region. For more information, see [AWS Regional Services](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services).

<!--custom.important.start-->
<!--custom.important.end-->

## Code examples

### Prerequisites

For prerequisites, see the [README](../../README.md#Prerequisites) in the `rustv1` folder.


<!--custom.prerequisites.start-->
<!--custom.prerequisites.end-->

### Get started

- [Hello AWS Glue](src/run.rs#L15) (`ListJobs`)


### Single actions

Code excerpts that show you how to call individual service functions.

- [Create a crawler](src/prepare.rs#L50) (`CreateCrawler`)
- [Create a job definition](src/prepare.rs#L253) (`CreateJob`)
- [Delete a crawler](src/cleanup.rs#L82) (`DeleteCrawler`)
- [Delete a database from the Data Catalog](src/cleanup.rs#L73) (`DeleteDatabase`)
- [Delete a job definition](src/cleanup.rs#L15) (`DeleteJob`)
- [Delete a table from a database](src/cleanup.rs#L23) (`DeleteTable`)
- [Get a crawler](src/prepare.rs#L118) (`GetCrawler`)
- [Get a database from the Data Catalog](src/prepare.rs#L148) (`GetDatabase`)
- [Get a job run](src/run.rs#L70) (`GetJobRun`)
- [Get tables from a database](src/prepare.rs#L163) (`GetTables`)
- [List job definitions](src/run.rs#L15) (`ListJobs`)
- [Start a crawler](src/prepare.rs#L79) (`StartCrawler`)
- [Start a job run](src/run.rs#L39) (`StartJobRun`)

### Scenarios

Code examples that show you how to accomplish a specific task by calling multiple
functions within the same service.

- [Get started with crawlers and jobs](src/prepare.rs)


<!--custom.examples.start-->
<!--custom.examples.end-->

## Run the examples

### Instructions


<!--custom.instructions.start-->
<!--custom.instructions.end-->

#### Hello AWS Glue

This example shows you how to get started using AWS Glue.



#### Get started with crawlers and jobs

This example shows you how to do the following:

- Create a crawler that crawls a public Amazon S3 bucket and generates a database of CSV-formatted metadata.
- List information about databases and tables in your AWS Glue Data Catalog.
- Create a job to extract CSV data from the S3 bucket, transform the data, and load JSON-formatted output into another S3 bucket.
- List information about job runs, view transformed data, and clean up resources.

<!--custom.scenario_prereqs.glue_Scenario_GetStartedCrawlersJobs.start-->
<!--custom.scenario_prereqs.glue_Scenario_GetStartedCrawlersJobs.end-->


<!--custom.scenarios.glue_Scenario_GetStartedCrawlersJobs.start-->
<!--custom.scenarios.glue_Scenario_GetStartedCrawlersJobs.end-->

### Tests

⚠ Running tests might result in charges to your AWS account.


To find instructions for running these tests, see the [README](../../README.md#Tests)
in the `rustv1` folder.



<!--custom.tests.start-->
<!--custom.tests.end-->

## Additional resources

- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/latest/dg/what-is-glue.html)
- [AWS Glue API Reference](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api.html)
- [SDK for Rust AWS Glue reference](https://docs.rs/aws-sdk-glue/latest/aws_sdk_glue/)

<!--custom.resources.start-->
<!--custom.resources.end-->

---

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

SPDX-License-Identifier: Apache-2.0