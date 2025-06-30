# DistributedCinemaReservation
The project lets you simulate a distrubuted database of cinema reservations in cassandra, with a terminal app that lets you control the reservations and run stress tests on the database.

## Requirements
- **python** (3.11) with **cassandra-driver** (3.29.2) library installed
- **docker** (project was created and tested in Windows' Docker Desktop)

## Running the project
- Setup the docker containers (bash):
```
docker run --name cas1 --network cassandraNet -d -e MAX_HEAP_SIZE=1G -e HEAP_NEWSIZE=200M -p 127.0.0.1:9042:9042 cassandra

docker run --name cas2 --network cassandraNet -d -e CASSANDRA_SEEDS=cas1 -e MAX_HEAP_SIZE=1G -e HEAP_NEWSIZE=200M -p 127.0.0.2:9042:9042 cassandra
```
- check if everything is running:
```
docker exec -it cas1 nodetool status
```
- start the container and create the database:
```
docker exec -it cas1 cqlsh

CREATE KEYSPACE IF NOT EXISTS cinema_reservations WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2};

USE cinema_reservations;

CREATE TABLE IF NOT EXISTS reservations ( screening_id text, seat_id text, user_id text, reserved_at timestamp, available boolean, PRIMARY KEY (screening_id, seat_id) );
```
- Run the programs with python, for example:
```
python.exe .\insert.py

python.exe .\app.py
```
Please begin with running the *insert.py* program to populate the database with screenings with empty seats.

- To refer to existing screenings in the app use names: MOV1, MOV2, MOV3, MOV4, MOV_big and MOV_xyz and seats in convention [row number]-[column number] (ex.: 1-1, 10-5).

## Stress tests
After choosing the stress test the app runs the following tests:
- A single user tries to book the same place 1000 times.
- Two users make random actions on MOV4 screening.
- Two users try to book everything in MOV_big at the same time.
If the tests end without an error and not all seats in MOV_big are reserved by the same user, the tests conclude successfuly.

# Report
## This project implements a distributed cinema seat reservation system using Apache Cassandra. It supports:

- making seat reservations

- cancelling reservations

- transferring reservations to another user

- viewing available/reserved seats

- running on a two-node Cassandra cluster in Docker

- handling concurrency and collisions using lightweight transactions (LWT)

The system uses a Python console interface to issue commands and interact with the database.

Stress tests were developed to validate concurrency and data integrity under high load.

## Database:

- Partition key: screening_id

- Clustering key: seat_id

The table supports efficient lookups for all seats of a given screening, or a specific seat.

## Problems encountered:
| Problem | Explanation | Solution |
| --- | --- | --- |
| Docker containers crashing | Out of memory errors | Reduced Cassandra heap with MAX_HEAP_SIZE=1G and HEAP_NEWSIZE=200M |
| SELECT COUNT(*) timeouts | Cassandra cannot efficiently count rows in large tables | Use of other ways to count the rows, not big problem because of efficient lookups |