#25/7/2023
#Nguyen Sinh Hung
# necessary imports
import secrets
import string

# define the alphabet
letters = string.ascii_letters
digits = string.digits
special_chars = string.punctuation

alphabet = letters + digits + special_chars

def random_password():
    # fix password length
    pwd_length = 12
    # generate a password string
    pwd = ''
    for i in range(pwd_length):
        pwd += ''.join(secrets.choice(alphabet))
    return pwd

# tung.nguyenson11 29/09/2023 tạo mật khẩu tự động
def generate_password(length: int):
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


