import sqlite3
import requests
import json
from pprint import pprint
conn = sqlite3.connect("trtlme.db")
c = conn.cursor()

CURRENT_ID = 0
RPC_URL = "http://127.0.0.1:8070/json_rpc"
HEADERS = {'content-type': 'application/json'}

def mark_transfer(conn, payment):
    sql = '''REPLACE INTO Payment(payment_id,paid) VALUES(?,?)'''
    x = c.execute(sql, payment)
    print(x)
    return c.lastrowid

def get_status():
    rpc_input = {  
        'params':{},
        'jsonrpc':'2.0',
        'id':'test',
        'method':'getStatus'
    }

    response = requests.post(
         RPC_URL,
         data=json.dumps(rpc_input),
         headers=HEADERS) 
    return response.json()
def process_transaction_status(payment_id,price):
    transactions = []
    print(payment_id)
    bc = int(get_status()['result']['blockCount'])
    unlocktime = -1
    amount = -1
    rpc_input = {
        'params':{  
            'blockCount':1000000,
            'firstBlockIndex':130000,
            'paymentId':payment_id
        },
        'jsonrpc':'2.0',
        'id':'test',
        'method':'getTransactions'
    }

    # execute the rpc request
    response = requests.post(
         RPC_URL,
         data=json.dumps(rpc_input),
         headers=HEADERS)  
    pprint(response.json())
    for i in response.json()['result']['items']:
        for x in i['transactions']:
            transactions.append(x)
    for t in transactions:
        unlocktime+=int(t['unlockTime'])
        amount+=int(t['amount'])
    if ((unlocktime) == 0 or (unlocktime <= (bc  - 40))) and amount>=price:
        p = (payment_id,1)
    else:
        p = (payment_id,0)
    pprint(p)
    print("Transactions: ", len(transactions))
    x = mark_transfer(conn,p)
    print(x)


def run():
    while True:
        c.execute("SELECT * FROM User")
        rows = c.fetchall()
        for row in rows:
            process_transaction_status(row[2],row[6])



if __name__ == '__main__': 
    run()