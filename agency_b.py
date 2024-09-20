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

print("enter path to file for linkage [agency_b_data.csv]:")
while True:
    input_file_path = input("> ") if not is_interactive else ""
    if input_file_path == "":
        input_file_path = "agency_b_data.csv"
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
with open('agency_b_fingerprints.txt', 'w') as f:
    for fingerprint in fingerprints:
        ignored = f.write(fingerprint + '\n')

num_client_items = len(fingerprints)

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

client = psi.client.CreateFromKey(private_bytes, True)

assert client.GetPrivateKeyBytes() == private_bytes

print("input path to server [/app/server]:")
server_path = input("> ") if not is_interactive else ""
if server_path == "":
    server_path = "/app/server"

server_path = Path(server_path)


####### START PSI PROTOCOL
print('configuration complete, starting PSI protocol\n\n\n')

####### STEP 1: send number of agency B items
# write number of items
print('[B->A] STEP 1: sending number of items')
input("Agency B: press [ENTER] to send message")

with open(server_path / 'agency_b_num_items.txt', 'w') as f:
    ignored = f.write(str(num_client_items))



####### STEP 2: receive agency A data encrypted by agency A 
print('[B<-A] STEP 2: waiting to receive agency agency A data encrypted by agency A')
input("Agency B: press [ENTER] once message has been sent")

setup = psi.ServerSetup()
with open(server_path / 'agency_a_encrypted_by_a.o', 'rb') as f:
    setup.ParseFromString(f.read())



####### STEP 3: send agency B data encrypted by agency B
print('[B->A] STEP 3: sending agency B data encrypted by agency B')
input("Agency B: press [ENTER] to send message")

request = client.CreateRequest(fingerprints)
with open(server_path / 'agency_b_encrypted_by_b.o', 'wb') as f:
    ignored = f.write(request.SerializeToString())

print('message contents :\n' + '\n'.join(str(request).split('\n')[0:5]) + '\n  ...')



####### STEP 4: receive agency B data encrypted by agencies A & B
print('[B<-A] STEP 4: waiting to receive agency agency B data encrypted by agencies A and B')
input("Agency B: press [ENTER] once message has been sent")

response = psi.Response()
with open(server_path / 'agency_b_encrypted_by_a_and_b.o', 'rb') as f:
    response.ParseFromString(f.read())



####### STEP 4.5: compute common elements by decrypting response and comparing to initial set 
print('[B] Step 4.5: decrypting agency B data encrypted by agencies A and B')
print('[B]           comparing agency A data encrypted by agency A to agency')
print('[B]           agency B data encrytped by agency A to find common')
print('[B]           elements')
input("Agency B: press [ENTER] to continue")

intersection_indices = client.GetIntersection(setup, response)
intersection = [ fingerprints[i] for i in intersection_indices ]
intersection.sort()

print('[B]         : intersection contains "' + '", "'.join(intersection[0:5]) + '"...')



####### STEP 5: send common elements to agency B
print("[B->A] STEP 5: sending common elements")
input("Agency B: press [ENTER] to send message")

# TODO: encrypt agency A's initial message and send it back instead of sending
#       results in plaintext

with open(server_path / 'agency_a_and_b_common_elements.txt', 'w') as f:
    for item in intersection:
        ignored = f.write(str(item) + '\n')
