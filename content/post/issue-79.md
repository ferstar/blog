---
title: "Try github self-hosted action runner"
date: "2023-09-02T04:23:11+08:00"
tags: ['Linux', 'Git']
comments: true
---

Official docs: https://docs.github.com/en/actions/hosting-your-own-runners

Simple docker compose file:

```yaml
version: '3.8'
services:
  worker:
    image: myoung34/github-runner:ubuntu-bionic
    environment:
      REPO_URL: ${RUNNER_REPO}
      RUNNER_NAME: ${RUNNER_NAME}
      RUNNER_TOKEN: ${RUNNER_TOKEN}
      CONFIGURED_ACTIONS_RUNNER_FILES_DIR: ${CONFIGURED_ACTIONS_RUNNER_FILES_DIR}
      DISABLE_AUTOMATIC_DEREGISTRATION: ${DISABLE_AUTOMATIC_DEREGISTRATION}
      RUNNER_WORKDIR: /tmp/runner/work
      ORG_RUNNER: 'false'
      LABELS: linux,x64,home-1
    security_opt:
      # needed on SELinux systems to allow docker container to manage other docker containers
      - label:disable
    volumes:
      - '/var/run/docker.sock:/var/run/docker.sock'
      - '/tmp/runner:/tmp/runner'
      - './data:/data'
      # note: a quirk of docker-in-docker is that this path
      # needs to be the same path on host and inside the container,
      # docker mgmt cmds run outside of docker but expect the paths from within
```

Your `.env` file may be like this:

```shell
RUNNER_REPO=https://github.com/user/repo
RUNNER_TOKEN=NOT THE GITHUB ACCESS TOKEN
RUNNER_NAME=foo
CONFIGURED_ACTIONS_RUNNER_FILES_DIR=/data
DISABLE_AUTOMATIC_DEREGISTRATION=true
```

Please note that the `RUNNER_TOKEN` is not your github access token

1. visit https://github.com/user/repo/settings/actions/runners/new
2. get your action's real token

![image](https://github.com/ferstar/blog/assets/2854276/7d6a6fbe-0812-4299-91b3-a2dc2d595167)

Some normal running logs:

```shell
docker-compose up
Recreating github-actions_worker_1 ... done
Attaching to github-actions_worker_1
worker_1  | Runner reusage is disabled
worker_1  | Configuring
worker_1  |
worker_1  | --------------------------------------------------------------------------------
worker_1  | |        ____ _ _   _   _       _          _        _   _                      |
worker_1  | |       / ___(_) |_| | | |_   _| |__      / \   ___| |_(_) ___  _ __  ___      |
worker_1  | |      | |  _| | __| |_| | | | | '_ \    / _ \ / __| __| |/ _ \| '_ \/ __|     |
worker_1  | |      | |_| | | |_|  _  | |_| | |_) |  / ___ \ (__| |_| | (_) | | | \__ \     |
worker_1  | |       \____|_|\__|_| |_|\__,_|_.__/  /_/   \_\___|\__|_|\___/|_| |_|___/     |
worker_1  | |                                                                              |
worker_1  | |                       Self-hosted runner registration                        |
worker_1  | |                                                                              |
worker_1  | --------------------------------------------------------------------------------
worker_1  |
worker_1  | # Authentication
worker_1  |
worker_1  |
worker_1  | √ Connected to GitHub
worker_1  |
worker_1  | # Runner Registration
worker_1  |
worker_1  |
worker_1  |
worker_1  |
worker_1  | √ Runner successfully added
worker_1  | √ Runner connection is good
worker_1  |
worker_1  | # Runner settings
worker_1  |
worker_1  |
worker_1  | √ Settings Saved.
worker_1  |
worker_1  |
worker_1  | √ Connected to GitHub
worker_1  |
worker_1  | Current runner version: '2.308.0'
worker_1  | 2023-09-02 03:22:29Z: Listening for Jobs
worker_1  | 2023-09-02 03:23:08Z: Running job: build_deb
worker_1  | 2023-09-02 03:26:51Z: Job build_deb completed with result: Succeeded
```



```
# NOTE: I am not responsible for any expired content.
create@2023-09-02T04:23:11+08:00
update@2023-09-02T05:21:40+08:00
comment@https://github.com/ferstar/blog/issues/79
```
