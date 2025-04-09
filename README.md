Demo of private set intersection
-------------------------------

Illustrates running a private set intersection (PSI) protocol between two agencies using a third party as an intermediary.

By default it runs a private set intersection cardinality algorithm, only revealing the size of the intersection. To reveal the actual elements, set `reveal_intersection` to `True` in both `agency_a.py` and `agency_b.py` on line 19.

# Dependencies:

[Docker Desktop](https://www.docker.com/products/docker-desktop/)

# To run:

## Start the container

From the root directory of the repository, execute:

```sh
docker build \
  --label org.opencontainers.image.revision=$(git rev-parse HEAD) \
  --label org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
  -t psi_demo:latest .
docker run -it --rm --name psi_demo -d psi_demo
```

## Run PSI

Run each of the following in separate terminal windows.

### Server

```sh
docker exec -it psi_demo inotifywait -m /app/server -e create
```

### Agency A

```sh
docker exec -it psi_demo bash -c 'cd /app/agency_a && python agency_a.py'
```

### Agency B

```sh
docker exec -it psi_demo bash -c 'cd /app/agency_b && python agency_b.py'
```

## Step through the scripts

Press return to step through the scripts, starting with Agency B.

# Checking result

## Private Set Intersection Cardinality

The scripts for Agencies A and B write out their fingerprints, which can be compared to the file that gets written to the server `agency_a_and_b_common_elements_size.txt` as part of the PSI protocol. To check that the intersection set size is calculated correctly, first run:

```sh
docker exec -it psi_demo python
```

Then run:

```python
def read_file_to_set(file: str) -> set:
    result = set()
    with open(file, 'r') as f:
       for fingerprint in f:
            result.add(fingerprint.rstrip())
    return result

agency_a_data = read_file_to_set('/app/agency_a/agency_a_fingerprints.txt')
agency_b_data = read_file_to_set('/app/agency_b/agency_b_fingerprints.txt')

with open('/app/server/agency_a_and_b_common_elements_size.txt', 'r') as f:
    psi_result = int(f.read())

assert psi_result == len(agency_a_data.intersection(agency_b_data))
```

## Private Set Intersection

Instead of the above, the protocol writes out `agency_a_and_b_common_elements.txt` which contains the elements in the intersection. To check the validity of that file, run:

```sh
docker exec -it psi_demo python
python
```

Then:

```python
def read_file_to_set(file: str) -> set:
    result = set()
    with open(file, 'r') as f:
       for fingerprint in f:
            result.add(fingerprint.rstrip())
    return result

agency_a_data = read_file_to_set('/app/agency_a/agency_a_fingerprints.txt')
agency_b_data = read_file_to_set('/app/agency_b/agency_b_fingerprints.txt')
psi_result = read_file_to_set('/app/server/agency_a_and_b_common_elements.txt')

assert psi_result == agency_a_data.intersection(agency_b_data)
```


## Private Set Intersection

# Stopping the container

Ctrl-C out of the server notify process. The python scripts should terminate themselves. Then run:

```sh
docker stop psi_demo
```

# Reclaim space

When completely done with demo, execute to reclaim disk space:

```sh
docker image rm psi_demo
docker builder prune
```

# Todo

1. Create more than fingerprint from test data
2. Use multiple fingerprints to determine probabilistic record linkage
3. Decrypt intermediate messages for illustration
4. Encrypt final message sending intersection back to Agency A

# Sources

The implementation of PSI is from [OpenMined](https://github.com/OpenMined/PSI). The example data comes from the [Febrl](https://users.cecs.anu.edu.au/~Peter.Christen/Febrl/febrl-0.3/febrldoc-0.3/front.html) - Freely extensible biomedical record linkage.

# Codespaces

If you do not have Docker desktop, you can run the demo in a Github [Codespace](https://github.com/codespaces).

1. Create a new Codespace
   1. Select `vdorie/psi_demo` as the repository
   2. Leave other options at the default
2. Wait while the Codespace builds
3. Create multiple terminals and arrange them within your Codespace windows
   1. Navigate to the `TERMINAL` tab in the console area on the bottom of the screen
   2. Push the `+` over the side bar on the right to create a new `bash` session; repeat as necessary
   3. Right click on each process and move the terminal to its own area
4. Run the above processes without first calling Docker:
   1. One terminal for `inotifywait -m /app/server -e create`
   2. One terminal for `cd /app/agency_a && python agency_a.py`
   3. One terminal for `cd /app/agency_b && python agency_b.py`
   4. If desired, create a fourth terminal for examining the filesystem - no commands needed
5. When finished, terminate the Codespace by clicking on the lower-left of the window and selecting "Stop Current Codespace"
6. If desired, delete the Codespace entirely from the [dashboard](https://github.com/codespaces)
