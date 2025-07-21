# Benchmarking Results

## Mac

### Modalities

MacBook Pro, macOS Sequoia 15.5, Chip: Apple M1 Max, OS/Arch: darwin/arm64, 32 GB RAM

podman-compose version 1.5.0
podman version 5.5.2
podman machine ssh crun --version: crun version 1.20

Docker version 28.3.2
Docker Compose version v2.38.2
containerd 1.7.27
runc 1.2.5

pyperf.Runner which spawns 4 processes, which each run 1 warmup and 3 measurements.
This results in 12 measurements.
Before doing the actual measurements, pyperf spawns 1 calibrating process which also runs 1 warmup + 3 measurements.
So in total, the code is executed 20 times, but only 12 are used for the measurement.

### start-stack

podman
run start-stack: Mean +- std dev: 15.2 sec +- 0.3 sec

docker
run start-stack: Mean +- std dev: 12.2 sec +- 0.5 sec

docker (with cache resetting)
run start-stack: Mean +- std dev: 12.8 sec +- 0.5 sec

### xmlupload

docker
xmlupload: Mean +- std dev: 44.8 sec +- 0.6 sec

podman
xmlupload: Mean +- std dev: 43.5 sec +- 1.5 sec




## Linux

## Modalities

podman version 5.5.2
podman-compose version: 1.5.0
crun version 1.14.4

docker 28.0.4
docker-compose ???
containerd 1.7.27
runc 1.2.5

### start-stack

docker:
start-stack: Mean +- std dev: 21.6 sec +- 0.5 sec !!! UNVERIFIED DOCKER VERSION
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16401669907/job/46341996845)

podman:
start-stack: Mean +- std dev: 22.5 sec +- 0.6 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16403464117/job/46346085822)


### xmlupload

docker:

()

podman:
xmlupload: Mean +- std dev: 64.7 sec +- 1.2 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16403513137/job/46346196853)
