from sqlite3 import connect


def create_leaderboard():
    """create a leaderboard"""
    con = connect("Bubbles.db")
    print("Database opened successfully.")
    cur = con.cursor()

    cur.execute("CREATE TABLE leaderboard (rank INTEGER PRIMARY KEY, score INTEGER)")
    leaderboard = [
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),
        (5, 0),
        (6, 0),
    ]
    cur.executemany("INSERT INTO leaderboard VALUES (?, ?)", leaderboard)
    con.commit()
    con.close()
    print("Database closed")

def init_leaderboard():
    """initialize leaderboard."""
    answer = input("Warning: This operation will clean up all the records, continue? [y/n]")
    if answer == "Y" or answer == "y":
        con = connect("Bubbles.db")
        print("Database opened successfully.")
        cur = con.cursor()
        cur.execute("UPDATE leaderboard SET score = 0")
        con.commit()
        con.close()
        print("Database closed")
    else:
        print("Mission canceled.")

def get_data():
    """fetch data.
        Return:
          data: list, first 6 places of leading scores.
    """
    con = connect("Bubbles.db")
    print("Database opened successfully.")
    cur = con.cursor()
    data = []
    for row in cur.execute("SELECT score FROM leaderboard"):
        data.append(row[0])
    con.close()
    print("Database closed")
    return data

def set_data(data):
    """upload data.
        Args:
          data: list, first 6 places of leading scores.
    """
    con = connect("Bubbles.db")
    print("Database opened successfully.")
    cur = con.cursor()
    for i, score in enumerate(data):
        cur.execute("UPDATE leaderboard SET score = ? WHERE rank = ?", (score, i + 1))
    con.commit()
    con.close()
    print("Database closed")

if __name__ == "__main__":
    init_leaderboard()


    