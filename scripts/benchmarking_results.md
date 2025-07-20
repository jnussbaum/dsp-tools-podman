# Benchmarking Results

## Mac

### Modalities

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