# Quarterly loyalty credit batch

`customers.csv` lists this quarter's customers and their credit amount.

Credit one customer with:

    python3 apply_credit.py <customer_id> <amount>

Each call appends one row to `ledger.csv`.
