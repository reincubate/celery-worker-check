celery-worker-check
===================

Check for missing, unexpected or malfunctioning `Celery` workers or servers through `django-celery`.

## Rationale

`Celery` works well as a distributed task queue, but when backed against `redis` rather than a proper
message bus, it had can be hard to identify how well it is running when under heavy load. Many of the
default `Celery` monitoring or reporting tools fail to work under certain error conditions.

The script is a very basic way to perform a crude inventory of running workers and servers against
a known list. It can easily be extended to do cleverer things.

The script was built at [Reincubate](https://www.reincubate.com/) where its primary use has
been to identify malfunctioning workers.

## Design principles

 * The script is an example of simplicity over configurability. It deliberately avoids any `Celery`-specific
 functionality, such as the `ping` request, having found that they cannot be trusted under load. Hack it if
 you need something different, or enhance it and submit a pull request.

## Installation & usage

Deploy it to a server which has `django-celery` installed and which is able to run `./manage.py celery status`.

It can be run like so:

```bash
./manage.py celery status -t 10 | ./celery-worker-check.py specialworker-4@serverA otherworker-5@serverB workername-2@serverC
```

In this example, the script will look for 4 instances of a worker named `specialworker` running on `serverA`. It will look for 5 instances of `otherworker` running on `serverB`, and it will look for 2 instances of `workername` running on `serverC`.

> Note the `-t 10` argument, so that we'll wait 10 seconds to get a full set of responses from loaded workers.

Output could look like this:

```
Server serverC was missing, accounts for 2 missing workers...
Worker specialworker@serverA was missing, accounts for 4 missing workers...
Worker newspecialworker@serverA was unexpectedly present, accounts for 4 workers...
Worker otherworker-4@serverB was missing...
```

Configure it to be run by `cron` so that it will automatically email reports on missing or unexpected servers or workers.

## See also

Before building this script we sought to find a pre-existing solution. Most notably, `Celery` fires an event when a worker dies, but this is not reliable under heavy load.