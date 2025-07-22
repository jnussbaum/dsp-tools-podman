# Benchmarking Results

## Methodology

pyperf.Runner which spawns 4 processes, which each run 1 warmup and 3 measurements.
This results in 12 measurements.
Before doing the actual measurements, pyperf spawns 1 calibrating process which also runs 1 warmup + 3 measurements.
So in total, the code is executed 20 times, but only 12 are used for the measurement.


## Mac

### Software Versions

MacBook Pro, macOS Sequoia 15.5, Chip: Apple M1 Max, OS/Arch: darwin/arm64, 32 GB RAM

podman-compose version 1.5.0
podman version 5.5.2
podman machine ssh crun --version: crun version 1.20

Docker version 28.3.2
Docker Compose version v2.38.2
containerd 1.7.27
runc 1.2.5


### start-stack

docker
run start-stack: Mean +- std dev: 12.2 sec +- 0.5 sec

docker (with cache resetting)
run start-stack: Mean +- std dev: 12.8 sec +- 0.5 sec

podman
run start-stack: Mean +- std dev: 15.2 sec +- 0.3 sec


### xmlupload

docker
xmlupload: Mean +- std dev: 44.8 sec +- 0.6 sec

podman
xmlupload: Mean +- std dev: 43.5 sec +- 1.5 sec




## GitHub CI (Ubuntu)

## Software Versions

Ubuntu 24.04.2 LTS

podman version 5.5.2
podman-compose version: 1.5.0
crun version 1.14.4

docker 28.0.4
docker-compose 2.36.2
containerd 1.7.27
runc 1.2.5

### start-stack

docker:
start-stack: Mean +- std dev: 21.6 sec +- 0.5 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16401669907/job/46341996845)
start-stack: Mean +- std dev: 21.1 sec +- 0.5 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16410107631/job/46363080376)
start-stack: Mean +- std dev: 22.2 sec +- 0.1 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16444970781/job/46474407098)

podman:
start-stack: Mean +- std dev: 22.5 sec +- 0.6 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16403464117/job/46346085822)
start-stack: Mean +- std dev: 22.5 sec +- 0.5 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16444993154/job/46474483226)


### xmlupload

docker:
xmlupload: Mean +- std dev: 66.1 sec +- 1.6 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16444997558/job/46474498479)


podman:
<!-- xmlupload: Mean +- std dev: 64.7 sec +- 1.2 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16403513137/job/46346196853) -->
xmlupload: Mean +- std dev: 63.2 sec +- 0.6 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16445006761/job/46474529533)
