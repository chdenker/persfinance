import sqlite3
import argparse
import datetime
import calendar
import sys

def add_entry(db_cursor, date: str, amount: int, category: str, comment: str = None):
    # Try to get the ID of the specified category
    # TODO Fix % appending (considered unsafe)
    sql = "SELECT id FROM categories WHERE categories.name == '%s'" % category
    db_cursor.execute(sql)
    cat_id = db_cursor.fetchone()
    if cat_id == None: # Category does not exist in DB yet, add it
        sql = "INSERT INTO categories VALUES (NULL, '%s')" % category
        db_cursor.execute(sql)
        # Now, get the new category ID
        sql = "SELECT id FROM categories WHERE categories.name == '%s'" % category
        db_cursor.execute(sql)
        cat_id = db_cursor.fetchone()
    cat_id = cat_id[0]  # originally, cat_id is a list - but we only need the first element

    # Insert new entry into DB
    sql = "INSERT INTO entries VALUES(NULL,'" + date + "', " + str(amount) + ", " + str(cat_id) + ", '" + comment + "')"
    db_cursor.execute(sql)

    # Print new entry
    sql = "SELECT MAX(id) FROM entries"
    db_cursor.execute(sql)
    entry_id = db_cursor.fetchone()[0]
    print("\n%d    %s    %8.2f    %15s    %s\n" % ( entry_id, date, float(amount) / 100.0, category, comment), end="")

def delete_entry(db_cursor, entry_id: int):
    sql = "DELETE FROM entries WHERE id == '%s'" % entry_id
    db_cursor.execute(sql)

# Get all category names from the DB as a list of strings
# indexed by the same index (with offset -1) used in the table of categories in the DB
def fetch_category_names(db_cursor) -> list:
    sql = "SELECT * FROM categories"
    db_cursor.execute(sql)
    cat_res = db_cursor.fetchall()
    cat_names = []
    for cat_pair in cat_res:
        cat_names.append(cat_pair[1])
    return cat_names

def print_all_entries(db_cursor):
    cat_names = fetch_category_names(db_cursor)

    # Get all entries from the DB as a list
    # and print them
    sql = "SELECT * FROM entries ORDER BY date(entries.date)"
    db_cursor.execute(sql)
    entries = db_cursor.fetchall()
    for entry in entries:
        entry_id = entry[0]
        date = entry[1]
        amount = float(int(entry[2]) / 100.0)
        category = cat_names[int(entry[3]) - 1]
        comment = entry[4]
        print("%d    %s    %8.2f    %15s    %s\n" % ( entry_id, date, amount, category, comment), end="")

def print_statistics(db_cursor, year: int):
    year_str = str(year)
    print("%-20s %s\n" % ("YEAR: ", year_str))
    for month in range(1, 13):
        if month >= 1 and month <= 9:
            month_str = "0" + str(month)
        else:
            month_str = str(month)
        sql = """SELECT SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS total_month_income,
                        SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) AS total_month_expenses,
                        SUM(amount) AS total_month_sum
                 FROM   entries
                 WHERE  strftime("%%Y-%%m", entries.date) == "%s-%s"
              """ % ( year_str, month_str )
        db_cursor.execute(sql)
        values = db_cursor.fetchone()
        total_month_income = values[0]
        total_month_expenses = values[1]
        total_month_sum = values[2]
        if total_month_income != None or total_month_expenses != None or total_month_sum != None:
            print("%-20s %-10s" % ( "Month: ", calendar.month_name[month] ))
            print("%-20s %8.2f" % ( "Total income: ", float(total_month_income) / 100.0 ))
            print("%-20s %8.2f" % ( "Total expenses: ", float(total_month_expenses) / 100.0 ))
            print("%-20s %8.2f" % ( "Sum: ", float(total_month_sum) / 100.0 ))
            print()

def new_entry_dialog() -> list:
    entry_str_list = []
    datestr = input("Date: ")
    if datestr == "":
        datestr = str(datetime.date.today())
    entry_str_list.append(datestr)
    amountstr = input("Amount: ")
    entry_str_list.append(amountstr)
    categorystr = input("Category: ")
    entry_str_list.append(categorystr)
    commentstr = input("Comment (optional): ")
    entry_str_list.append(commentstr)
    return entry_str_list

def create_database(db_cursor):
    sql = '''CREATE TABLE categories (
                id integer,
                name text NOT NULL,
                PRIMARY KEY (id)
             )'''
    db_cursor.execute(sql)
    sql = '''CREATE TABLE entries (
                id integer,
                date text NOT NULL,
                amount integer NOT NULL,
                category integer NOT NULL,
                comment text,
                PRIMARY KEY (id),
                FOREIGN KEY (category) REFERENCES categories(id)
             )'''
    db_cursor.execute(sql)
    sql = '''CREATE TABLE standing_orders (
                id integer,
                amount integer NOT NULL,
                category integer NOT NULL,
                comment text,
                period text NOT NULL,             -- 'daily', 'weekly', 'monthly', 'yearly'
                start_date text NOT NULL,
                end_date text,
                last_executed text,
                PRIMARY KEY (id),
                FOREIGN KEY (category) REFERENCES categories(id)
             )'''
    db_cursor.execute(sql)

# Parses an amount string like "0.29 + 0.70"
# and returns the number of total cents: 99
def parse_amount_str(amountstr: str) -> int:
    total_cents = 0
    current_num_str = ""
    sign = 1  # sign for the number being read
    prev_ch = ""

    for ch in amountstr:
        if ch not in "+-. " and not ch.isdigit():
            return None     # invalid input
        if ch == " ":
            continue

        if ch in "+-":
            if prev_ch == "+" or prev_ch == "-":
                return None     # invalid input

            # finish previous number if there is one
            if current_num_str:
                euros, _, cents = current_num_str.partition(".")
                # normalize cents to exactly 2 digits
                cents = (cents + "00")[:2]
                total_cents += sign * (int(euros) * 100 + int(cents))
                current_num_str = ""

            # start new number with new sign
            sign = -1 if ch == "-" else 1
        else:
            current_num_str += ch

        prev_ch = ch

    # handle the last number
    if current_num_str:
        euros, _, cents = current_num_str.partition(".")
        cents = (cents + "00")[:2]
        total_cents += sign * (int(euros) * 100 + int(cents))

    return total_cents

def get_category_id_create_if_missing(db_cursor, category_name: str) -> int:
    # use parameterized queries where convenient
    sql = "SELECT id FROM categories WHERE name = ?"
    db_cursor.execute(sql, (category_name,))
    res = db_cursor.fetchone()
    if res:
        return res[0]
    sql = "INSERT INTO categories(name) VALUES(?)"
    db_cursor.execute(sql, (category_name,))
    sql = "SELECT id FROM categories WHERE name = ?"
    db_cursor.execute(sql, (category_name,))
    return db_cursor.fetchone()[0]

def add_standing_order(db_cursor, amount: int, category: str, comment: str, period: str, start_date: str, end_date: str = None):
    cat_id = get_category_id_create_if_missing(db_cursor, category)
    sql = "INSERT INTO standing_orders VALUES(NULL, ?, ?, ?, ?, ?, ?, ?)"
    db_cursor.execute(sql, (amount, cat_id, comment, period, start_date, end_date, None))

def change_standing_order(db_cursor, id: int, amount: int, category: str, comment: str, period: str, start_date: str, end_date: str = None):
    print_standing_orders(db_cursor, id)
    cat_id = get_category_id_create_if_missing(db_cursor, category)
    sql = """
            UPDATE standing_orders
            SET amount = ?, category = ?, comment = ?, period = ?, start_date = ?, end_date = ?
            WHERE id = ?
          """
    db_cursor.execute(sql, (amount, cat_id, comment, period, start_date, end_date, id))

def delete_standing_order(db_cursor, id: int):
    sql = """
            DELETE FROM standing_orders
            WHERE id = ?
          """
    db_cursor.execute(sql, (id,))

def new_standing_order_dialog() -> list:
    vals = []
    amountstr = input("Amount: ")
    vals.append(amountstr)
    categorystr = input("Category: ")
    vals.append(categorystr)
    commentstr = input("Comment (optional): ")
    vals.append(commentstr)
    periodstr = input("Period (daily/weekly/monthly/yearly): ")
    vals.append(periodstr)
    datestr = input("Start date (YYYY-MM-DD, empty = today): ")
    if datestr == "":
        datestr = str(datetime.date.today())
    vals.append(datestr)
    enddatestr = input("End date (YYYY-MM-DD, optional): ")
    if enddatestr == "":
        enddatestr = None
    vals.append(enddatestr)
    return vals

def inc_date(date_obj: datetime.date, period: str) -> datetime.date:
    if period == "daily":
        return date_obj + datetime.timedelta(days=1)
    if period == "weekly":
        return date_obj + datetime.timedelta(weeks=1)
    if period == "monthly":
        # add one month, cap day to last day of new month
        month = date_obj.month + 1
        year = date_obj.year
        if month > 12:
            month = 1
            year += 1
        day = min(date_obj.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)
    if period == "yearly":
        year = date_obj.year + 1
        month = date_obj.month
        day = min(date_obj.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)
    raise ValueError("Unsupported period: %s" % period)

def execute_standing_orders(db_cursor):
    # Fetch all standing orders
    sql = "SELECT id, amount, category, comment, period, start_date, end_date, last_executed FROM standing_orders"
    db_cursor.execute(sql)
    orders = db_cursor.fetchall()
    today = datetime.date.today()
    for order in orders:
        so_id, amount, cat_id, comment, period, start_date_str, end_date_str, last_executed_str = order
        try:
            start_date = datetime.date.fromisoformat(start_date_str)
        except Exception:
            continue
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.date.fromisoformat(end_date_str)
            except Exception:
                end_date = None

        # determine next occurrence to execute
        if last_executed_str:
            try:
                last_executed = datetime.date.fromisoformat(last_executed_str)
            except Exception:
                last_executed = None
        else:
            last_executed = None

        if last_executed is None:
            next_occ = start_date
        else:
            next_occ = inc_date(last_executed, period)

        latest_executed = last_executed
        # get category name
        db_cursor.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
        cat_row = db_cursor.fetchone()
        if not cat_row:
            continue
        cat_name = cat_row[0]

        while next_occ <= today and (end_date is None or next_occ <= end_date):
            # create an entry for next_occ
            add_entry(db_cursor, next_occ.isoformat(), amount, cat_name, comment)
            latest_executed = next_occ
            next_occ = inc_date(next_occ, period)

        if latest_executed:
            db_cursor.execute("UPDATE standing_orders SET last_executed = ? WHERE id = ?", (latest_executed.isoformat(), so_id))

def print_standing_orders(db_cursor, id = None):
    if id != None:
        sql = """SELECT so.id, so.amount, c.name, so.comment, so.period, so.start_date, so.end_date, so.last_executed
                 FROM standing_orders so
                 LEFT JOIN categories c ON so.category = c.id
                 WHERE so.id == ?"""
        db_cursor.execute(sql, (id,))
    else:
        sql = """SELECT so.id, so.amount, c.name, so.comment, so.period, so.start_date, so.end_date, so.last_executed
                 FROM standing_orders so
                 LEFT JOIN categories c ON so.category = c.id
                 ORDER BY so.id"""
        db_cursor.execute(sql)
    rows = db_cursor.fetchall()
    if not rows:
        print("No standing orders.")
        return
    for r in rows:
        so_id, amount, cat_name, comment, period, start_date, end_date, last_exec = r
        amt = float(int(amount) / 100.0)
        LABEL_W = 12
        print(
            f"{'ID:':<{LABEL_W}}{so_id}\n"
            f"{'Amount:':<{LABEL_W}}{amt}\n"
            f"{'Category:':<{LABEL_W}}{cat_name}\n"
            f"{'Comment:':<{LABEL_W}}{comment}\n"
            f"{'Period:':<{LABEL_W}}{period}\n"
            f"{'Start:':<{LABEL_W}}{start_date}\n"
            f"{'End:':<{LABEL_W}}{end_date}\n"
            f"{'Last:':<{LABEL_W}}{last_exec}\n"
        )

def main():
    prog_description = "PersFinance | (2017 - 2026) written by Christopher Denker"
    argparser = argparse.ArgumentParser(description=prog_description)
    argparser.add_argument("database_path")
    mut_ex_args_group = argparser.add_mutually_exclusive_group()
    mut_ex_args_group.add_argument("--add-order", help="add a standing order", action="store_true")
    mut_ex_args_group.add_argument("--change-order", help="change an existing standing order with the given ID (if it exists)", type=int)
    mut_ex_args_group.add_argument("--delete-order", help="delete an existing standing order with the given ID (if it exists)", type=int)
    mut_ex_args_group.add_argument("-c", "--create", help="create a new database (specified database_path will be used)", action="store_true")
    mut_ex_args_group.add_argument("-d", "--delete", metavar="ID", help="delete the entry with the given ID (if it exists)", type=int)
    mut_ex_args_group.add_argument("-n", "--new", help="enter new entry", action="store_true")
    mut_ex_args_group.add_argument("-o", "--orders", help="show all standing orders", action="store_true")
    mut_ex_args_group.add_argument("-p", "--print", help="print all entries", action="store_true")
    mut_ex_args_group.add_argument("-s", "--statistics", metavar="YEAR", default=None, help="print statistics of the given year", type=int)
    args = argparser.parse_args()

    db_con = sqlite3.connect(args.database_path)
    db_cursor = db_con.cursor()

    # Execute standing orders unless we are creating the DB
    if not args.create:
        try:
            execute_standing_orders(db_cursor)
        except Exception:
            # don't prevent normal operation on unexpected errors
            pass

    if args.new:
        entry_str_list = new_entry_dialog()
        date = entry_str_list[0]
        amount = parse_amount_str(entry_str_list[1])
        if amount == None:
            print("Invalid amount!")
            db_con.close()
            sys.exit(-1)
        category = entry_str_list[2]
        if category == None or category == "":
            print("Category must not be empty")
            db_con.close()
            sys.exit(-1)
        comment = entry_str_list[3]
        add_entry(db_cursor, date, amount, category, comment)
    elif args.create:
        create_database(db_cursor)
    elif args.add_order:
        values = new_standing_order_dialog()
        amount = parse_amount_str(values[0])
        if amount == None:
            print("Invalid amount")
            db_con.close()
            sys.exit(-1)
        category = values[1]
        if category == None or category == "":
            print("Category must not be empty")
            db_con.close()
            sys.exit(-1)
        comment = values[2]
        period = values[3]
        if period not in ("daily", "weekly", "monthly", "yearly"):
            print("Invalid period (use daily/weekly/monthly/yearly)")
            db_con.close()
            sys.exit(-1)
        start_date = values[4]
        end_date = values[5]
        add_standing_order(db_cursor, amount, category, comment, period, start_date, end_date)
    elif args.change_order: # args.change_order is an integer (the given argument).. only >= 1 is a valid ID
        entry_id = args.change_order
        if entry_id <= 0:
            print("Invalid ID (must be >= 1)")
            db_con.close()
            sys.exit(-1)
        print("Changing standing order ID " + str(entry_id))
        values = new_standing_order_dialog()
        amount = parse_amount_str(values[0])
        if amount == None:
            print("Invalid amount")
            db_con.close()
            sys.exit(-1)
        category = values[1]
        comment = values[2]
        period = values[3]
        if period not in ("daily", "weekly", "monthly", "yearly"):
            print("Invalid period (use daily/weekly/monthly/yearly)")
            db_con.close()
            sys.exit(-1)
        start_date = values[4]
        end_date = values[5]
        change_standing_order(db_cursor, entry_id, amount, category, comment, period, start_date, end_date)
    elif args.delete_order: # args.delete_order is an integer (the given argument).. only >= 1 is a valid ID
        entry_id = args.delete_order
        if entry_id <= 0:
            print("Invalid ID (must be >= 1)")
            db_con.close()
            sys.exit(-1)
        delete_standing_order(db_cursor, entry_id)
    elif args.print:
        print_all_entries(db_cursor)
    elif args.delete: # args.delete is an integer (the given argument).. only >= 1 is a valid ID
        entry_id = args.delete
        if entry_id <= 0:
            print("Invalid ID (must be >= 1)")
            db_con.close()
            sys.exit(-1)
        delete_entry(db_cursor, entry_id)
    elif args.statistics != None:
        year = args.statistics
        if year < 0:
            print("Invalid YEAR (must be > 0)")
            db_con.close()
            sys.exit(-1)
        print_statistics(db_cursor, year)
    elif args.orders:
        print("Existing standing orders:\n")
        print_standing_orders(db_cursor)

    db_con.commit()
    db_con.close()

if __name__ == "__main__":
    main()
