from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra import ConsistencyLevel
import sys
from copy import deepcopy
import time
import threading
import random

cluster = Cluster(['127.0.0.1', '127.0.0.2'], port=9042)
session = cluster.connect('cinema_reservations')

def view_screening(screening_id, seat_id):
    if seat_id == 'a':
        query = SimpleStatement(
            "SELECT seat_id, available, user_id FROM reservations WHERE screening_id=%s",
            consistency_level=ConsistencyLevel.ONE
        )

        args = [screening_id]
    else:
        query = SimpleStatement(
            "SELECT seat_id, available, user_id FROM reservations WHERE screening_id=%s AND seat_id=%s",
            consistency_level=ConsistencyLevel.ONE
        )

        args = [screening_id, seat_id]
    
    try:
        rows = session.execute(query, args)
        mul = len(rows.all())
        if mul == 0:
            print("No such a seat and or screening")
            return None
        rows = session.execute(query, args)
        
        for row in sorted(rows, key = lambda x: int(x.seat_id.split('-')[0]) * mul + int(x.seat_id.split('-')[1])):
            status = "available" if row.available else f"reserved by {row.user_id}"
            print(f"Seat {row.seat_id}: {status}")
    except Exception as e:
        print(f"Error viewing seat: {e}")

def reserve_seat(screening_id, seat_id, user_id):
    query = SimpleStatement(
        """
        UPDATE reservations
        SET user_id=%s, reserved_at=toTimestamp(now()), available=false
        WHERE screening_id=%s AND seat_id=%s
        IF available=true
        """,
        consistency_level=ConsistencyLevel.QUORUM
    )
    try:
        result = session.execute(query, [user_id, screening_id, seat_id])
        row = result[0]
        applied = row.applied
        if applied:
            print(f"Reservation for seat {seat_id} was successful.")
        else:
            if not hasattr(row, 'available') or row.available is None:
                print(f"Seat {seat_id} does not exist in screening {screening_id}.")
            else:
                print(f"Seat {seat_id} is already reserved.")
    except Exception as e:
        print(f"Error reserving seat: {e}")

def change_reservation(screening_id, seat_id, new_user_id):
    """
    Changes reservation ownership to new_user_id if the seat exists and is currently reserved.
    """
    query = SimpleStatement(
        """
        UPDATE reservations
        SET user_id=%s, reserved_at=toTimestamp(now())
        WHERE screening_id=%s AND seat_id=%s
        IF available=false
        """,
        consistency_level=ConsistencyLevel.QUORUM
    )
    try:
        result = session.execute(query, [new_user_id, screening_id, seat_id])
        row = result[0]
        applied = row.applied
        if applied:
            print(f"Reservation for seat {seat_id} was successfully transferred to user {new_user_id}.")
        else:
            if not hasattr(row, 'available') or row.available is None:
                print(f"Seat {seat_id} does not exist in screening {screening_id}.")
            elif row.available == True:
                print(f"Cannot transfer reservation for seat {seat_id} because it is currently unreserved.")
            else:
                print(f"Failed to change reservation for unknown reasons.")
    except Exception as e:
        print(f"Error changing reservation: {e}")


def cancel_reservation(screening_id, seat_id):
    try:
        check_query = SimpleStatement(
            """
            SELECT available, user_id
            FROM reservations
            WHERE screening_id=%s AND seat_id=%s
            """,
            consistency_level=ConsistencyLevel.ONE
        )
        row = session.execute(check_query, [screening_id, seat_id]).one()
        if row is None:
            print(f"Seat {seat_id} does not exist in screening {screening_id}.")
            return
        if row.available:
            print(f"Seat {seat_id} is already available — nothing to cancel.")
            return
        
        update_query = SimpleStatement(
            """
            UPDATE reservations
            SET user_id=null, available=true
            WHERE screening_id=%s AND seat_id=%s
            """,
            consistency_level=ConsistencyLevel.QUORUM
        )
        session.execute(update_query, [screening_id, seat_id])
        print(f"Seat {seat_id} reservation has been canceled and is now available.")
    
    except Exception as e:
        print(f"Error canceling reservation: {e}")


def stress_test_1(screening_id, seat_id, user_id, repetitions=1000):
    for i in range(repetitions):
        reserve_seat(screening_id, seat_id, user_id)
        time.sleep(0.001)
    print("Stress test 1 completed.")

def random_client(screening_id, user_id, repetitions=1000):
    for _ in range(repetitions):
        action = random.choice(['reserve', 'cancel', 'change'])
        row = random.randint(1,10)
        col = random.randint(1,10)
        seat_id = f"{row}-{col}"
        if action == 'reserve':
            reserve_seat(screening_id, seat_id, user_id)
        elif action == 'cancel':
            cancel_reservation(screening_id, seat_id)
        elif action == 'change':
            new_user_id = f"{user_id}_alt"
            change_reservation(screening_id, seat_id, new_user_id)
        time.sleep(random.uniform(0.001, 0.01))

def stress_test_2(screening_id, repetitions=1000):
    t1 = threading.Thread(target=random_client, args=(screening_id, 'userA', repetitions))
    t2 = threading.Thread(target=random_client, args=(screening_id, 'userB', repetitions))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("Stress test 2 completed.")

def reservation_party(screening_id, user_id, rows=100, cols=100):
    for r in range(1, rows+1):
        for c in range(1, cols+1):
            seat_id = f"{r}-{c}"
            reserve_seat(screening_id, seat_id, user_id)
            time.sleep(0.001)

def stress_test_3(screening_id, rows=100, cols=100):
    t1 = threading.Thread(target=reservation_party, args=(screening_id, 'partyA', rows, cols))
    t2 = threading.Thread(target=reservation_party, args=(screening_id, 'partyB', rows, cols))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("Stress test 3 completed.")


def menu():
    while True:
        print("\nChoose an option:")
        print("1. View reservations for a movie")
        print("2. Reserve a seat")
        print("3. Transfer reservation")
        print("4. Cancel reservation")
        print("q. Quit")
        print("s. Stress test")
        choice = input("> ")
        if choice == "1":
            sid = input("Screening ID: ")
            seat = input("Seat ID (or 'a' for all): ")
            view_screening(sid, seat)
        elif choice == "2":
            sid = input("Screening ID: ")
            seat = input("Seat ID: ")
            uid = input("User ID: ")
            reserve_seat(sid, seat, uid)
        elif choice == "3":
            sid = input("Screening ID: ")
            seat = input("Seat ID: ")
            uid = input("New User ID: ")
            change_reservation(sid, seat, uid)
        elif choice == "4":
            sid = input("Screening ID: ")
            seat = input("Seat ID: ")
            cancel_reservation(sid, seat)
        elif choice == "q":
            break
        elif choice == "s":
            stress_test_1("MOV4", "1-1", "USER_stress1", 1000)
            stress_test_2("MOV4", 1000)
            stress_test_3("MOV_big", 100, 100)
        else:
            print("Invalid option")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nProgram closing...")
        sys.exit(0)
