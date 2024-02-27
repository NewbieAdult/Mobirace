# thien.tranthi get_base_url 08/09/2023
from fastapi import Depends, FastAPI, Request
from urllib.parse import urlparse

def get_base_url(request: Request):
    full_url = str(request.url)
    parsed_url = urlparse(full_url)
    base_path = parsed_url.path.split('/')[1]  
    desired_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{base_path}"
    return desired_url