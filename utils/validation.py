#25/7/2023
#Nguyen Sinh Hung
import re 

def is_valid_phone(phone_number):
    pattern = r'^(0|84)(2(0[3-9]|1[0-6|8|9]|2[0-2|5-9]|3[2-9]|4[0-9]|5[1|2|4-9]|6[0-3|9]|7[0-7]|8[0-9]|9[0-4|6|7|9])|3[2-9]|5[5|6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])([0-9]{7})$'
    if re.match(pattern, phone_number):
        return True
    return False
  
regex_mail = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
 
def is_valid_email(email):
    if(re.fullmatch(regex_mail, email)):
        return True
    else:
        return False

def is_valid_username(username):
    # Kiểm tra nếu username không phải là một chuỗi
    if not isinstance(username, str):
        return False

    # Biểu thức regex
    pattern = r'^[a-zA-Z0-9._][a-zA-Z0-9_.]*[a-zA-Z0-9]$'


    # Kiểm tra username với biểu thức regex
    if re.match(pattern, username):
        return True
    return False

def contains_username_fb(username):
    return "fb_" in username
"""
# Test với các đầu vào
print(is_valid_username("john_doe123"))  # Output: True
print(is_valid_username("user_name_"))  # Output: False (Kết thúc bằng dấu gạch dưới)
print(is_valid_username("123user"))     # Output: False (Bắt đầu bằng số)  
print(is_valid_username("user_name"))   # Output: True
"""

def check_pace(pace:float):
    if pace > 1:
        return '1'
    else: 
        return '0'