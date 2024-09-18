Demo of private set intersection
-------------------------------

Illustrates running a private set intersection (PSI) protocol between two agencies using a third party as an intermediary.

# Dependencies:

[Docker Desktop](https://www.docker.com/products/docker-desktop/)

# To run:

## Start the contaier

```sh
docker build -t psidemo:latest .
docker run -it --rm --name psidemo -d psidemo:latest
```

## Run PSI

Run each of the following in separate terminal windows.

### Server

```sh
docker exec -it psidemo inotifywait -m /app/server
```

### Agency A

```sh
docker exec -it psidemo bash -c 'cd /app/agency_a && python agency_a.py'
```

### Agency B

```sh
docker exec -it psidemo bash -c 'cd /app/agency_b && python agency_b.py'
```

## Step through the scripts

Press return to step through the scripts, starting with Agency B.

## Stop the container

Ctrl-C out of the server watch process. The python scripts should terminate themselves. Then run:

```sh
docker stop psidemo
```

# Todo

1. Incorporate use of test data
2. Create fingerprints from test data
   * Also determine record linkage from common fingerprints
3. Encrypt final message sending intersection back to Agency A
