#/usr/bin/env python
import os
from pathlib import Path
import random

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key

import private_set_intersection.python as psi


print("enter path to file for linkage")
#input_file_path = input("> ")

client_items = random.sample(range(50), k = 10)
client_items.sort()
client_items = [ str(item) for item in client_items ]

num_client_items = len(client_items)

print("enter path to private key or leave blank to generate a new one")
#private_key_path = input("> ")
private_key_path = ""

if private_key_path == "":
    # SECP256R1 is https://neuromancer.sk/std/x962/prime256v1
    # other curves could be used, but openmined PSI would have to be modified
    private_key = ec.generate_private_key(ec.SECP256R1())
#
    # potentially serialize here
else:
    with open(private_key_path, 'rb') as pem_in:
        pemlines = pem_in.read()
        private_key = load_pem_private_key(pemlines, None, default_backend())

private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'little')

client = psi.client.CreateFromKey(private_bytes, True)

assert client.GetPrivateKeyBytes() == private_bytes

print("input path to server")
#server_path = input("> ")
server_path = Path('/app/server')

# write number of items
print('STEP 1: writing number of items')
with open(server_path / 'agency_b_num_items.txt', 'w') as f:
    f.write(str(num_client_items))

# wait for startup, that is agency A's encrypted items
print('STEP 2: waiting for startup message')
input("Agency B: press [ENTER] to continue")

setup = psi.ServerSetup()
with open(server_path / 'agency_a_startup_message.o', 'rb') as f:
    setup.ParseFromString(f.read())

os.remove(server_path / 'agency_a_startup_message.o')

# write request, that is agency B's encrypted items
print('STEP 3: writing request')
with open(server_path / 'agency_b_request.o', 'wb') as f:
    f.write(client.CreateRequest(client_items).SerializeToString())

# wait for response, this is Agency B's doubly encrypted items
print('STEP 4: waiting for response')
input("Agency B: press [ENTER] to continue")

response = psi.Response()
with open(server_path / 'agency_a_response.o', 'rb') as f:
    response.ParseFromString(f.read())

os.remove(server_path / 'agency_a_response.o')

# compute intersection by decrypting response and comparing to initial set 
intersection_indices = client.GetIntersection(setup, response)
intersection = [ int(client_items[i]) for i in intersection_indices ]
intersection.sort()

print('intersection contains ' + str(intersection))

# TODO: encrypt agency A's initial message and send it back
with open(server_path / 'agency_b_final_response.txt', 'w') as f:
    for item in intersection:
        f.write(str(item) + '\n')

