import bcrypt

password = b"pum-secret-123"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed)