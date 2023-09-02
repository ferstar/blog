---
title: "Try github self-hosted action runner"
date: "2023-09-02T04:23:11+08:00"
tags: ['Linux', 'Git']
comments: true
---

official docs: https://docs.github.com/en/actions/hosting-your-own-runners

simple docker compose file:

```yaml
version: '3.8'
services:
  worker:
    image: myoung34/github-runner:ubuntu-bionic
    environment:
      REPO_URL: ${RUNNER_REPO}
      RUNNER_NAME: ${RUNNER_NAME}
      RUNNER_TOKEN: ${RUNNER_TOKEN}
      RUNNER_WORKDIR: /tmp/runner/work
      ORG_RUNNER: 'false'
      LABELS: linux,x64,home-1
    security_opt:
      # needed on SELinux systems to allow docker container to manage other docker containers
      - label:disable
    volumes:
      - '/var/run/docker.sock:/var/run/docker.sock'
      - '/tmp/runner:/tmp/runner'
      # note: a quirk of docker-in-docker is that this path
      # needs to be the same path on host and inside the container,
      # docker mgmt cmds run outside of docker but expect the paths from within
```

your `.env` file may be like this:

```shell
RUNNER_REPO=https://github.com/user/repo
RUNNER_TOKEN=NOT THE GITHUB ACCESS TOKEN
RUNNER_NAME=foo
```

please note that the `RUNNER_TOKEN` is not your github access token

1. visit https://github.com/user/repo/settings/actions/runners/new
2. get your action's real token

![image](https://github.com/ferstar/blog/assets/2854276/7d6a6fbe-0812-4299-91b3-a2dc2d595167)



```
# NOTE: I am not responsible for any expired content.
create@2023-09-02T04:23:11+08:00
update@2023-09-02T04:23:11+08:00
comment@https://github.com/ferstar/blog/issues/79
```
