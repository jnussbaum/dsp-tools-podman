# Benchmarking Results

## Macbook

### Modalities

pyperf.Runner which spawns 4 processes, which each run 1 warmup and 3 measurements.
This results in 12 measurements.
Before doing the actual measurements, pyperf spawns 1 calibrating process which also runs 1 warmup + 3 measurements.
So in total, the code is executed 20 times, but only 12 are used for the measurement.

podman
run start-stack: Mean +- std dev: 15.2 sec +- 0.3 sec

docker:
run start-stack: Mean +- std dev: 12.2 sec +- 0.5 sec