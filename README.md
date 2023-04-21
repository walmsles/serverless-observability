# serverless-observability

This repo is a demo project used to highlight what happens when a Serverless System goes wrong for a talk at Melbourne Serverless on April 20, 2023 entitled **"Unlocking Serverless Observability"**.

The slides for the talk are in the **slides** folder of this repo.

## About the project

This project implements a vanilla event driven architecture pattern as seen [here](https://serverlessland.com/patterns/apigw-lambda-eventbridge-sam-java) on the Serverless Land website.  This architecture link contains a Java implementation, the implementation here is in Python.

### Project Dependencies

This project uses the following open source tools and requires them to be installed and working in your environment:

- Python 3.9+ (including pip)
- SAM Cli
- aws-cli v2.0
- node and npm

All actions for this repo are controlled by the **Makefile** which contains the following commands:

- **dev** - Sets up the development environment by installing poetry, pip and pre-commit.
- **format** - run python formatting tools (isort and black)
- **lint** - run python flake8 linting tool
- **build** - run sam build
- **guided** - run sam deploy --guided (required for initial install)
- **deploy** run sam deploy to deploy to AWS
- **deps** - runs script to generate **requirements.txt** for each service (required by sam deploy python packaging).
- **clean** - removes all generated folders and files

### Project Layout

#### Services

Each sub-folder represents one of the Serverless Services in the SAM template.  Each service folder name matches one of the **poetry** dependency groups which will export the specific service dependencies to **requirements.txt** (see scripts/make-deps.sh for details about this process).  This configuration and use of poetry dependency groups enables efficient packaging of Python lambdas ensuring only the exact requirements are used for each lamdba function which will keep the installations lean.

### First Time Install

1. make dev
2. make guided (refer to sam deploy --guided documentation of help).
3. npm install
4. Once installed manual configuration in SSM Parameter Store and Secrets manager is required

    - Open the [API gateway console](https://ap-southeast-2.console.aws.amazon.com/apigateway/main/apis?region=ap-southeast-2)
    - Select the second **sls-observe** API and ensure it contains the **/slow** route (if it doesn't go select the other one)
    - Click **stages** in the left side menu and **Prod** under stages.
    - Copy the **Invoke URL**
    - Got to Systems Manager Console and [go to Parameter Store](https://ap-southeast-2.console.aws.amazon.com/systems-manager/parameters/?region=ap-southeast-2&tab=Table)
    - Click on **/sls-observe/delivery/endpoint** and edit
    - Copy Invoke URL and save
    - Go back to [API gateway console API Keys](https://ap-southeast-2.console.aws.amazon.com/apigateway/home?region=ap-southeast-2#/api-keys)
    - Click API key starting with **sls-ob-TheAp**
    - Click Show
    - copy the API Key value
    - Go to [Secrets Manager](https://ap-southeast-2.console.aws.amazon.com/secretsmanager/listsecrets?region=ap-southeast-2)
    - Click on **/sls-observe/delivery/api-key**
    - Scroll down and press **Retrieve Secret Value**
    - Click **Edit**
    - Paste in the API Key
    - Configuration is now complete.

### Subsequent Installs

1. make deploy

### Project Features

This project includes a **package.json** file that will install **artillery** as a dev dependency.  Artillery is used to run the performance tests over approx. 33 minutes to drive too much traffic into the service for it to fail as demonstrated in the talk at Melbourne Serverless (slide 18).

Once the stack is deployed and initial manual configuration is completed the performance test can be executed using **npx artillery run notify-perf-test.yml**.

### AWS BILL WARNING !!!

The performance test will run over 33 minutes and may cause your AWS account to accrue charges but is unlikely.  The expected lambda invocation count is approx. 17,000.
