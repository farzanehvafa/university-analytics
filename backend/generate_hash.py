import bcrypt
import sys

password = sys.argv[1].encode()
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())