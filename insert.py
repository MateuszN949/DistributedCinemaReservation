from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra import ConsistencyLevel
from cassandra.query import BatchStatement

cluster = Cluster(['127.0.0.1', '127.0.0.2'], port=9042)
session = cluster.connect('cinema_reservations')

for i in range(50):
    session.execute("INSERT INTO reservations (screening_id, seat_id, available) VALUES ('MOV1', '{}-{}', true);".format(i // 10 + 1, i % 10 + 1))

for i in range(72):
    session.execute("INSERT INTO reservations (screening_id, seat_id, available) VALUES ('MOV2', '{}-{}', true);".format(i // 12 + 1, i % 12 + 1))

for i in range(72):
    session.execute("INSERT INTO reservations (screening_id, seat_id, available) VALUES ('MOV3', '{}-{}', true);".format(i // 12 + 1, i % 12 + 1))

for i in range(150):
    session.execute("INSERT INTO reservations (screening_id, seat_id, available) VALUES ('MOV4', '{}-{}', true);".format(i // 15 + 1, i % 15 + 1))

batch = BatchStatement()
for i in range(10000):
    batch.add("INSERT INTO reservations (screening_id, seat_id, available) VALUES ('MOV_big', '{}-{}', true);".format(i // 100 + 1, i % 100 + 1))
session.execute(batch)

print("Specify how many times to add 10.000 rows to 'MOV_xyz' screening (max 100 recommended):")
size = int(input())
count = 0

for a in range(size):
    count += 1
    print(count * 10000)
    
    batch = BatchStatement()

    for i in range(1, 101):
        for j in range(1, 101):
            seat_id = f"{a * 100 + i}-{j}"
            query = SimpleStatement(
                """
                INSERT INTO reservations (screening_id, seat_id, available)
                VALUES ('MOV_xyz', %s, true)
                """,
                consistency_level=ConsistencyLevel.QUORUM
            )
            batch.add(query, [seat_id])

    session.execute(batch)