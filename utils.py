import os
import binascii

def get_payment_id():
    random_32_bytes = os.urandom(32)
    payment_id = "".join(map(chr, binascii.hexlify(random_32_bytes)))

    return '5d79873986852300d941bff65287bc7e2fce4dc2abc6bf8064965db1263e7a28'

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d

def get_price(url):
    if len(url) == 1:
        return 500000000
    if len(url) == 2:
        return 40000000
    if len(url) == 3:
        return 30000000
    if len(url) <= 6:
        return 200000
    if len(url) <= 10:
        return 100000
    return 50000