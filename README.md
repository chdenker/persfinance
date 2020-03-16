# PersFinance
### A command-line program for organizing personal income and expenses

Call the program with the -h parameter to find out how it works.

Example Usage (the file test.db does not exist before):
```
chris@chris-TUXEDO:~/Programming/persfinance$ python3 persfinance.py -c test.db
chris@chris-TUXEDO:~/Programming/persfinance$ python3 persfinance.py -n test.db
Date: 2020-03-01
Amount: 1000
Category: Income
Comment (optional): 
chris@chris-TUXEDO:~/Programming/persfinance$ python3 persfinance.py -n test.db
Date: 
Amount: -13.19
Category: Groceries
Comment (optional): 
chris@chris-TUXEDO:~/Programming/persfinance$ python3 persfinance.py -n test.db
Date: 2020-03-10
Amount: -4
Category: Food
Comment (optional): Döner
chris@chris-TUXEDO:~/Programming/persfinance$ python3 persfinance.py -p test.db
1    2020-03-01     1000.00             Income    
3    2020-03-10       -4.00               Food    Döner
2    2020-03-16      -13.19          Groceries    
chris@chris-TUXEDO:~/Programming/persfinance$ python3 persfinance.py -s test.db
YEAR:                2020

Month:               March     
Total income:         1000.00
Total expenses:        -17.19
Sum:                   982.81

```

Originally written in 2017 as a C++ program using a single CSV file
serving as a database. Rewritten in 2020 as a Python program using SQLite.
