#/usr/bin/env python
import os
from pathlib import Path
import random
import sys

from cryptography.hazmat.primitives.asymmetric import ec
import cryptography.hazmat.primitives.serialization as key_serialization

import pandas as pd

import private_set_intersection.python as psi


is_interactive = hasattr(sys, 'ps1')

print("enter path to file for linkage [agency_a_data.csv]:")
while True:
    input_file_path = input("> ") if not is_interactive else ""
    if input_file_path == "":
        input_file_path = "agency_a_data.csv"
#
    if os.path.isfile(input_file_path):
        break
    print(f"error could not find {input_file_path}")

input_data = pd.read_csv(input_file_path)

def get_fingerprint(x: pd.core.series.Series) -> str:
    result = x.surname[0] if not pd.isna(x.surname) else '  '
    result += str(int(x.age)).rjust(3, '0') if not pd.isna(x.age) else '   '
    soc_sec_id = str(x.soc_sec_id) if not pd.isna(x.soc_sec_id) else '    '
    result += soc_sec_id[0:min(len(soc_sec_id), 4)].rjust(4, '0')
    return result

# This is a deduplication example dataset, and as such it is designed with
# multiple records very similar to each other. In practice, one would
# start with a deduplicated dataset at both agencies and attempt to link
# to each other. As such, we deduplicate our fingerprints before transmitting.
fingerprint_series = input_data.apply(get_fingerprint, 'columns')

fingerprints = fingerprint_series.unique().tolist()
with open('agency_a_fingerprints.txt', 'w') as f:
    for fingerprint in fingerprints:
        ignored = f.write(fingerprint + '\n')

num_server_items = len(fingerprints)

print("enter path to private key or leave blank to generate a new one")
private_key_path = input("> ") if not is_interactive else "" 

if private_key_path == "":
    # SECP256R1 is https://neuromancer.sk/std/x962/prime256v1
    # other curves could be used, but openmined PSI would have to be modified
    private_key = ec.generate_private_key(ec.SECP256R1())
#
    print("saving key to private_key.pem")
    with open('private_key.pem', 'wb') as pem_out:
        ignored = pem_out.write(private_key.private_bytes(
            key_serialization.Encoding.PEM,
            key_serialization.PrivateFormat.PKCS8,
            key_serialization.NoEncryption()
        ))
else:
    with open(private_key_path, 'rb') as pem_in:
        pemlines = pem_in.read()
        private_key = load_pem_private_key(pemlines, None)

private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'little')

server = psi.server.CreateFromKey(private_bytes, True)

assert server.GetPrivateKeyBytes() == private_bytes

print("input path to server [/app/server]:")
server_path = input("> ") if not is_interactive else ""
if server_path == "":
   server_path = "/app/server"

server_path = Path(server_path)



####### START PSI PROTOCOL
print('configuration complete, starting PSI protocol\n\n\n')

####### STEP 1: receive number of agency B items
# read number of items
print('[A<-B] STEP 1: waiting for number of items')
input("Agency A: press [ENTER] once message has been sent")

with open(server_path / 'agency_b_num_items.txt', 'r') as f:
    num_client_items = int(f.read())



####### STEP 2: send agency A data encrypted by agency A 
print('[A->B] STEP 2: sending agency A data encrypted by agency A')
input("Agency A: press [ENTER] to send message")

setup = server.CreateSetupMessage(0.0, num_client_items, fingerprints, psi.DataStructure.RAW)
with open(server_path / 'agency_a_encrypted_by_a.o', 'wb') as f:
   ignored = f.write(setup.SerializeToString())

print('message contents :\n' + '\n'.join(str(setup).split('\n')[0:5]) + '\n  ...')



####### STEP 3: receive agency B data encrypted by agency B
print('[A<-B] STEP 3: waiting to receive agency B data encrypted by agency B')
input("Agency A: press [ENTER] once message has been sent")

request = psi.Request()

with open(server_path / 'agency_b_encrypted_by_b.o', 'rb') as f:
   request.ParseFromString(f.read())



####### STEP 4: send agency B data encrypted by agencies A & B
print('[A->B] STEP 4: sending agency B data encrypted by agencies A and B')
input("Agency A: press [ENTER] to send message")

response = server.ProcessRequest(request)
with open(server_path / 'agency_b_encrypted_by_a_and_b.o', 'wb') as f:
   ignored = f.write(response.SerializeToString())

print('message contents :\n' + '\n'.join(str(response).split('\n')[0:5]) + '\n  ...')



####### STEP 5: receive common elements from agency B
# TODO: this can be replaced by receiving agency A elements encrypted
#       by agencies A and B and then computing the intersection

# waiting to finish
print('[A<-B] STEP 5: waiting to receive agency A and agency B common elements')
input("Agency A: press [ENTER] once message has been sent")

intersection = []
with open(server_path / 'agency_a_and_b_common_elements.txt', 'r') as f:
    for item in f:
       intersection.append(item.rstrip())

print('[A] STEP 5.5: testing that all common elements are actually known')

for fingerprint in intersection:
    assert fingerprint in fingerprints

print('[A]           all elements in data set! PSI success!')
