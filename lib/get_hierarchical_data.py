import  decimal, re 
from typing import Any, List
from enum import Enum
from fastapi import HTTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from sqlalchemy.orm.session import Session
import smtplib
from pydantic import BaseModel, Field

# Class đầu vào đệ quy
class Argument(BaseModel):
    keyAtrrName: str = "id"
    parentAtrrName: str = "parentKey"    
    labelAtrrName: str = "label" 
    pathAtrrName: str = "to"
    iconAtrrName: str = "icon"
    childAtrrName: str = "items"
    class Config():
        orm_mode = True
    def __getitem__(self, item):
        return getattr(self, item)

class ResponseMenuBar(BaseModel):
    id: Any
    parentKey: Any = Field(exclude=True)  
    label: Any
    to: Any
    icon: Any
    items: List['ResponseMenuBar'] = []  

    def __getitem__(self, item):
        return getattr(self, item)
    def filter_empty_items(self):
        self.items = [item for item in self.items if item.items]  # Keep only non-empty items

def hierarchical_data(datalist: List[dict], argument: Argument = Argument()):
    res = []
    for record in datalist:
        res.append(
            ResponseMenuBar(
                id=record[argument.keyAtrrName],
                parentKey=record[argument.parentAtrrName],
                to=record[argument.pathAtrrName],
                label=record[argument.labelAtrrName],
                icon=record[argument.iconAtrrName]
            )
        )
    root = dict(id="ROOT")
    return lib_hierarchical_data(res, root, argument)

#Hàm đệ quy
def lib_hierarchical_data(datalist: List[ResponseMenuBar] 
                        , root: dict, argument: Argument):
    result = [] 
    for item in datalist:
        if (item.parentKey or "ROOT") == root["id"]:
            item.__setattr__(argument.childAtrrName,lib_hierarchical_data(datalist, item, argument))
            result.append(item)
    filtered_data = []
    for item in result:
        if item["id"] not in [3,4]:
            filtered_data.append(item)
        else:
            filtered_data.extend(item["items"])
    #sorted_data = sorted(filtered_data, key=lambda item: (item["id"] != 9, item["id"]))
    return filtered_data 
