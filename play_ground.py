from itsdangerous import TimestampSigner
from digitavote.utils.security import (
    generate_sign_token,
    validate_sign_token,
    generate_token, 
    generate_secure_filename,
)
from datetime import datetime
import time
import base64

from wtforms import SelectField, Form
from  flask import request

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

text = "MasterDigitaVote411"

key = generate_password_hash(text)
print(key)



"""
b = "17/56EB0/18"

print(b.replace("/","_"))
a = generate_secure_filename("17/56EB018")
print(a)
print(len(a))

help(request.files)
class A:
    pass

class B:
    pass

a = A()
b = B()

print(isinstance(b,A))
class T(Form):
    s = SelectField("Post")


ss = 


key = "DigitaVote_by_RastaXarm"

key = generate_secure_filename(key)
print(key)

secret, m = generate_sign_token(generate_token(key, length=12))

print(secret)
print(m)
print(datetime.fromtimestamp(m))

from time import sleep

x = 5
while x > 0:
    t = datetime.timestamp(datetime.now()) + 20
    k = datetime.fromtimestamp((t - m)).minute
    print("k", k)
    print("tt:", t)
    print("t: ", datetime.fromtimestamp(t), 
            "\nk:", datetime.fromtimestamp(k))

    #if m <= 1:
    #    break
    x -= 1
    time.sleep(60)
test = "rasta"

test = generate_token(test)
gst = generate_sign_token(test)

print(gst)

k = gst.decode()
l = k.encode()

print("gst == l", gst == l, l, k)
sleep(2)
print(validate_sign_token(gst,max_age=5))
"""
