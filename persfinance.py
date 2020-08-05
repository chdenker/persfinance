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

def print_statistics(db_cursor):
    year_str = "2020"
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

def main():
    prog_description = "PersFinance | (2017 - 2020) written by Christopher Denker"
    argparser = argparse.ArgumentParser(description=prog_description)
    argparser.add_argument("database_path")
    mut_ex_args_group = argparser.add_mutually_exclusive_group()
    mut_ex_args_group.add_argument("-c", "--create", help="create a new database (specified database_path will be used)", action="store_true")
    mut_ex_args_group.add_argument("-n", "--new", help="enter new entry", action="store_true")
    mut_ex_args_group.add_argument("-p", "--print", help="print all entries", action="store_true")
    mut_ex_args_group.add_argument("-d", "--delete", metavar="ID", help="delete the entry with the given ID (if it exists)", type=int)
    mut_ex_args_group.add_argument("-s", "--statistics", help="print statistics", action="store_true")
    args = argparser.parse_args()

    db_con = sqlite3.connect(args.database_path)
    db_cursor = db_con.cursor()

    if args.new:
        entry_str_list = new_entry_dialog()
        date = entry_str_list[0]
        amount = int(float(entry_str_list[1]) * 100)
        category = entry_str_list[2]
        comment = entry_str_list[3]
        add_entry(db_cursor, date, amount, category, comment)
    elif args.create:
        create_database(db_cursor)
    elif args.print:
        print_all_entries(db_cursor)
    elif args.delete: # args.delete is an integer (the given argument).. only >= 1 is a valid ID
        entry_id = args.delete
        if entry_id <= 0:
            print("Invalid ID (must be >= 1)")
            db_con.close()
            sys.exit(-1)
        delete_entry(db_cursor, entry_id)
    elif args.statistics:
        print_statistics(db_cursor)

    db_con.commit()
    db_con.close()

if __name__ == "__main__":
    main()
