import sqlite3
import argparse

def add_entry(db_cursor, date: str, amount: int, category: str, comment: str = None):
	# Try to get the ID of the specified category
	# TODO Fix % appending (considered unsafe)
	sql = "SELECT id FROM categories WHERE categories.name == '%s'" % category
	db_cursor.execute(sql)
	cat_id = db_cursor.fetchone()
	if cat_id == None: # Category does not exist in DB yet, add it
		sql = "INSERT INTO categories VALUES (NULL, '%s')" % category
		# Now, get the new category ID
		sql = "SELECT id FROM categories WHERE categories.name == '%s'" % category
		db_cursor.execute(sql)
		cat_id = db_cursor.fetchone()
	cat_id = cat_id[0]	# originally, cat_id is a list - but we only need the first element

	# Insert new entry into DB
	sql = "INSERT INTO entries VALUES(NULL,'" + date + "', " + str(amount) + ", " + str(cat_id) + ", '" + comment + "')"
	db_cursor.execute(sql)

def print_all_entries(db_cursor):
	# Get all category names from the DB as a list
	sql = "SELECT * FROM categories"
	db_cursor.execute(sql)
	cat_res = db_cursor.fetchall()
	cat_names = []
	for cat_pair in cat_res:
		cat_names.append(cat_pair[1])
	
	# Get all entries from the DB as a list
	sql = "SELECT * FROM entries"
	db_cursor.execute(sql)
	entries = db_cursor.fetchall()
	for entry in entries:
		entry_id = entry[0]
		date = entry[1]
		amount = float(int(entry[2]) / 100.0)
		category = cat_names[int(entry[3]) - 1]
		comment = entry[4]
		print("%d    %s    %8.2f    %15s    %s" % ( entry_id, date, amount, category, comment), end="")
	print()

def print_statistics(db_cursor):
	pass

def new_entry_dialog() -> list:
	entry_str_list = []
	datestr = input("Date: ")
	entry_str_list.append(datestr)
	amountstr = input("Amount: ")
	entry_str_list.append(amountstr)
	categorystr = input("Category: ")
	entry_str_list.append(categorystr)
	commentstr = input("Comment (optional): ")
	entry_str_list.append(commentstr)
	return entry_str_list

def main():
	prog_description = "PersFinance | (2017 - 2020) written by Christopher Denker"
	argparser = argparse.ArgumentParser(description=prog_description)
	argparser.add_argument("database_path")
	mut_ex_args_group = argparser.add_mutually_exclusive_group()
	mut_ex_args_group.add_argument("-n", "--new", help="enter new entry", action="store_true")
	mut_ex_args_group.add_argument("-p", "--print", help="print all entries", action="store_true")
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
	elif args.print:
		print_all_entries(db_cursor)
	elif args.statistics:
		print_statistics(db_cursor)

	db_con.commit()
	db_con.close()

if __name__ == "__main__":
	main()
