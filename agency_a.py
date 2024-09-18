#/usr/bin/env python
import os
from pathlib import Path
import random


from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key

import private_set_intersection.python as psi


print("enter path to file for linkage")
#input_file_path = input("> ")

server_items = random.sample(range(50), k = 20)
server_items.sort()
server_items = [ str(item) for item in server_items ]

num_server_items = len(server_items)

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

server = psi.server.CreateFromKey(private_bytes, True)

assert server.GetPrivateKeyBytes() == private_bytes

print("input path to server")
#server_path = input("> ")
server_path = Path('/app/server')

# read number of items
print('STEP 1: waiting for number of items')
input("Agency A: press [ENTER] to continue")

with open(server_path / 'agency_b_num_items.txt', 'r') as f:
    num_client_items = int(f.read())

os.remove(server_path / 'agency_b_num_items.txt')

setup = server.CreateSetupMessage(0.0, num_client_items, server_items, psi.DataStructure(0))
# write startup message
print('STEP 2: writing startup message')
with open(server_path / 'agency_a_startup_message.o', 'wb') as f:
   f.write(setup.SerializeToString())

# wait for request
print('STEP 3: waiting for request')
input("Agency A: press [ENTER] to continue")

request = psi.Request()

with open(server_path / 'agency_b_request.o', 'rb') as f:
   request.ParseFromString(f.read())

os.remove(server_path / 'agency_b_request.o')

# write response
print('STEP 4: writing response')
with open(server_path / 'agency_a_response.o', 'wb') as f:
   f.write(server.ProcessRequest(request).SerializeToString())

# waiting to finish
print('STEP 5: waiting for final response')
input("Agency A: press [ENTER] to continue")

intersection = []
with open(server_path / 'agency_b_final_response.txt', 'r') as f:
    for item in f:
       intersection.append(int(item))

os.remove(server_path / 'agency_b_final_response.txt')

print('intersection contains ' + str(intersection))

