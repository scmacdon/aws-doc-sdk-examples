#  Creating an AWS Lambda function that queries Neptune graph data within the VPC 

## Overview

| Heading      | Description |
| ----------- | ----------- |
| Description | Discusses how to develop an AWS Lambda function that queries Amazon Neptune data within the VPC using the AWS SDK for Java (v2).   |
| Audience   |  Developer (intermediate)        |
| Required skills   | Java, Maven  |

This guide demonstrates how to create and deploy an AWS Lambda function that queries data from an Amazon Neptune graph database using the Neptune Data Client API. 

Amazon Neptune is a fully managed graph database. Since Neptune instances reside in a VPC, any Lambda function that needs to connect to Neptune must be configured to run within the same VPC and be granted necessary network and IAM permissions. External access is not supported.

To create an AWS Lambda function that queries an Amazon Neptune graph database using the Neptune Data API, it's essential to configure your AWS network infrastructure correctly. This includes setting up the necessary VPC, subnets, security groups, and IAM roles to ensure secure and efficient communication between Lambda and Neptune. 

This guide walks you through all the necessary steps to provision and configure the required AWS resources for this solution, including VPC settings, IAM roles, and network connectivity.

**Note**: Lambda is a compute service that you can use to run code without provisioning or managing servers. You can create Lambda functions in various programming languages. For more information about Lambda, see
[What is AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html).

#### Topics
+	Prerequisites
+	Create an AWS Identity and Access Management (IAM) role that is used to execute Lambda functions
+	Create an IntelliJ project
+	Add the POM dependencies to your project
+	Create a Lambda function by using the Lambda runtime API
+	Package the project that contains the Lambda function
+	Deploy the Lambda function

## Prerequisites
To follow along with this tutorial, you need the following:
+ An Amazon Neptune DB instance in a VPC. You can get this by running the Neptune Basics scenario located in AWS Code Library.
+ A security group that allows traffic from Lambda to Neptune (typically on port 8182).
+ An AWS account with proper credentials.
+ AWS CLI configured with permissions for Lambda, IAM, EC2 (VPC), S3, Neptune. For information about setting up AWS CLI, see [Setting up the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)
+ A Java IDE. (For this tutorial, the IntelliJ IDE is used.)
+ Java 21 JDK.
+ Maven 3.6 or higher.
+ An S3 bucket used to drploy the Lambda JAR file.  

### Important

+ The AWS services included in this document are included in the [AWS Free Tier](https://aws.amazon.com/free/?all-free-tier.sort-by=item.additionalFields.SortRank&all-free-tier.sort-order=asc).
+  This code has not been tested in all AWS Regions. Some AWS services are available only in specific Regions. For more information, see [AWS Regional Services](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services). 
+ Running this code might result in charges to your AWS account. 
+ Be sure to delete all of the resources that you create during this tutorial so that you won't be charged.

### Creating the resources

Create an S3 bucket that is used to store the Lambda JAR file which is created in a later step. For more information, see [Creating a bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html).

## Set Up the Amazon Neptune Cluster and VPC

You can use an existing VPC or create a new one. Make sure the VPC has at least two subnets in different Availability Zones (AZs) to support Neptune's high availability and networking requirements.

If you don't know a suitable VPC and subnets, you can get them by running the Amazon Neptune Basics scenario available in the AWS Code Library.

In addition to VPC information, the Amazon Neptune Basics scenario creates an Amazon cluster and database instance you can use in this use case. 

 

## Create the Lambda Execution IAM Role

### Create trust policy JSON file

You need to create the trust polciy used for this IAM role. Name the file **trust-policy-lambda.json**.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}

```

### Create the lambda-execution-role role

You can create the **lambda-execution-role** role by using this CLI command.

```bash
aws iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document file://trust-policy-lambda.json
```
### Attach the required managed policies

Run each of the following AWS CLI commands to attach the necessary managed policies to the Lambda execution role: 

```bash
aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AWSNeptuneFullAccess

aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

```


## Create an IntelliJ project

1. In the IntelliJ IDE, choose **File**, **New**, **Project**.

2. In the **New Project** dialog box, choose **Maven**, and then choose **Next**.

3. For **GroupId**, enter **org.example**.

4. For **ArtifactId**, enter **NeptuneLambda**.

5. Choose **Next**.

6. Choose **Finish**.

## Add the POM dependencies to your project

At this point, you have a new project named **NeptuneLambda**. Make sure that your project's **pom.xml** file looks like the POM file in this Github repository.
    
## Create a Lambda function by using the Lambda runtime Java API

Use the Lambda runtime Java API to create the Java class that defines the Lamdba function. In this example, there is one Java class for the Lambda function named **NeptuneLambdaHandler**. 


### NeptuneLambdaHandler class

This Java code represents the **NeptuneLambdaHandler** class. The class use the Neptune Data Client API to query data from the Neptune graph database.

```java
package org.example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.LambdaLogger;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.core.client.config.ClientOverrideConfiguration;
import software.amazon.awssdk.http.apache.ApacheHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.neptunedata.NeptunedataClient;
import software.amazon.awssdk.services.neptunedata.model.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public class NeptuneLambdaHandler implements RequestHandler<Map<String, String>, String> {

    @Override
    public String handleRequest(Map<String, String> event, Context context) {
        LambdaLogger logger = context.getLogger();

        String NEPTUNE_ENDPOINT = "https://neptunecluster65.cluster-ro-csf1if1wwrox.us-east-1.neptune.amazonaws.com:8182";

        NeptunedataClient neptunedataClient = NeptunedataClient.builder()
                .region(Region.US_EAST_1)
                .endpointOverride(URI.create(NEPTUNE_ENDPOINT))
                .httpClientBuilder(ApacheHttpClient.builder()
                        .connectionTimeout(Duration.ofSeconds(10))
                        .socketTimeout(Duration.ofSeconds(30)))
                .overrideConfiguration(ClientOverrideConfiguration.builder()
                        .apiCallAttemptTimeout(Duration.ofSeconds(30))
                        .build())
                .build();

        // Execute Gremlin Query
        logger.log("Executing Gremlin PROFILE query...\n");

        ExecuteGremlinQueryRequest queryRequest = ExecuteGremlinQueryRequest.builder()
                .gremlinQuery("g.V().hasLabel('person').values('name')")
                .build();

        ExecuteGremlinQueryResponse response = neptunedataClient.executeGremlinQuery(queryRequest);

        System.out.println("Full Response:");
        System.out.println(response);

        // Retrieve and print the result
        if (response.result() != null) {
            System.out.println("Query Result:");
            System.out.println(response.result().toString());
        } else {
            System.out.println("No result returned from the query.");
        }

        return "Done";
    }
}

```

**Note**: Make sure that you assign your **NEPTUNE_ENDPOINT** with the Neptune endpoint. You can get this value by running the Neptune Basics scenario located in the code lib.  

## Package the project that contains the Lambda functions

Package up the project into a .jar (JAR) file by using the following Maven command.

    mvn clean package shade:shade

This creates a shaded JAR file that is located in the **target** folder (which is a child folder of the project folder). 

**Note**: The **maven-shade-plugin** is used in the project’s POM file. This plugin is responsible for creating a .jar file that contains the required dependencies. If you attempt to package up the project without this plugin, the required dependences are not included in the .jar file and you will encounter a **ClassNotFoundException**. 

## Deploy the Lambda function

You can deploy the Lambda function using the AWS CLI. Be sure to specify the correct VPC subnets and security group associated with your Neptune database. These values can be retrieved by running the Neptune Basics Scenario located in the AWS Code Library.

The following command creates a Lambda function configured to run inside your VPC:
 

```bash
aws lambda create-function \
  --function-name NeptuneLoader \
  --runtime java21 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler org.example.NeptuneLambdaHandler::handleRequest \
  --timeout 900 \
  --memory-size 1024 \
  --zip-file fileb://target/my-lambda-jar-with-dependencies.jar \
  --vpc-config SubnetIds=subnet-abcdxxxx,subnet-xyz9xxxx,SecurityGroupIds=sg-abc1xxxx

```
 
### View CloudWatch Logs

After invoking your Lambda function, you can view the logs generated by the function in Amazon CloudWatch. Use the AWS CLI commands below to inspect the log groups, streams, and log events for your NeptuneLoader function:

Find the Log Group

```bash
aws logs describe-log-groups | grep NeptuneLoader
```

List Log Streams in the Log Group

```bash
aws logs describe-log-streams \
  --log-group-name /aws/lambda/NeptuneLoader \
  --order-by LastEventTime \
  --descending
```

This lists the available log streams sorted by the most recent activity.

 View Log Events from a Specific Stream
Once you identify a logStreamName from the previous step, use the following command to fetch log events:

```bash
aws logs get-log-events \
  --log-group-name /aws/lambda/NeptuneLoader \
  --log-stream-name <your-log-stream-name>
```

Replace <your-log-stream-name> with the actual stream name returned in the previous command.




aws logs describe-log-groups | grep NeptuneLoader
aws logs describe-log-streams --log-group-name /aws/lambda/NeptuneLoader
aws logs get-log-events --log-group-name /aws/lambda/NeptuneLoader --

Choose the **Invoke** button. After the Lambda function is invoked, you see a successful message. 

![AWS Tracking Application](images/pic8.png)

### Next steps
Congratulations, you have created a Lambda function that automatically applies tags to digital assets located in an S3 bucket. As stated at the beginning of this tutorial, be sure to delete all of the resources that you created during this tutorial so that you won't be charged.

For more AWS multiservice examples, see
[usecases](https://github.com/awsdocs/aws-doc-sdk-examples/tree/master/javav2/usecases).


