# Benchmarking Results

## Methodology

pyperf.Runner which spawns 1 process, which each run 1 warmup and 60 measurements.
This results in 60 measurements.
Before doing the actual measurements, pyperf spawns 1 calibrating process which also runs 1 warmup + 60 measurements.
So in total, the code is executed 122 times, but only 60 are used for the measurement.


## Mac

### Software Versions

- OS: MacBook Pro, macOS Sequoia 15.5, Chip: Apple M1 Max, OS/Arch: darwin/arm64, 32 GB RAM
- Podman:
    - podman-compose version 1.5.0
    - podman version 5.5.2
    - podman machine ssh crun --version: crun version 1.20
- Docker:
    - Docker version 28.3.2
    - Docker Compose version v2.38.2
    - containerd 1.7.27
    - runc 1.2.5


### start-stack

docker: start-stack: Mean +- std dev: 12.4 sec +- 0.5 sec

podman: start-stack: Mean +- std dev: 13.9 sec +- 0.6 sec 


### xmlupload

docker: Mean +- std dev: 32.0 sec +- 1.1 sec

podman: 




## GitHub CI (Ubuntu)

### Software Versions

- OS: Ubuntu 24.04.2 LTS
- Podman:
    - podman version 5.5.2
    - podman-compose version: 1.5.0
    - crun version 1.14.4
- Docker:
    - docker 28.0.4
    - docker-compose 2.36.2
    - containerd 1.7.27
    - runc 1.2.5

### start-stack

docker: Mean +- std dev: 20.1 sec +- 0.4 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16533152375/job/46762710036)

podman: Mean +- std dev: 19.7 sec +- 0.5 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16533155214/job/46762717192)



### xmlupload

docker: Mean +- std dev: 40.6 sec +- 0.4 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16533492582/job/46763634121)

podman: Mean +- std dev: 42.0 sec +- 0.5 sec
(https://github.com/jnussbaum/dsp-tools-podman/actions/runs/16533494437/job/46763639187)
