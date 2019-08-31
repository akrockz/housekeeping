# core-housekeeping

## What

A repo deployed via deployspec to multiple accounts.

Can deploy various resources, like Lambdas, to perform scheduled "cleanup" related tasks.


## Current Housekeeping Tasks

* Cleans "old" (empty) log groups from AWS accounts. They don't need to be "appspec" log groups (i.e. `DeletionPolicy: Retain` feature), can be any log group.

## How to Deploy

See `core-codecommit/core-codecommit-resources.yaml`, specifically `CoreHousekeepingRepo` and `CoreHousekeepingBuild`.

## Testing locally

I setup my lambda to be able to run locally:

```
AWS_PROFILE=sia-dev1 ./lambdas/clean_log_groups/clean_log_groups.py
```

TODO Could setup a TDD suite with mocked aws endpoints.
