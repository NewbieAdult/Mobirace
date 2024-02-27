#25/7/2023
#Nguyen Sinh Hung
from sqlalchemy.orm.session import Session
from fastapi import HTTPException, status
from db.models import User, User_Role, Function, Role_Function
from sqlalchemy.orm import aliased
#funcId front-end
def get_funcId_by_user(user: User, db: Session): 
    try:
        func = db.query(Role_Function.FUNC_ID)\
                .join(User_Role, Role_Function.ROLE_ID == User_Role.ROLE_ID)\
                .join(User, User_Role.USER_ID == User.USER_ID)\
                .filter(User.USER_ID == user.USER_ID)
        result = [api.FUNC_ID for api in func if api.FUNC_ID not in [3, 4]]
        #result.append(3)aa
        return result
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail.')

def get_api_path_hierarchy(func_id: list, roleId: int, db: Session):
    apiPath_hierarchy = db.query(
        Function.FUNC_ID,
        Function.FUNC_PARENT_ID,
        Function.FUNC_NAME,
        Function.API_PATH,
        Function.ICON
    ).filter(Function.FUNC_ID.in_(func_id)).cte(name="apiPath_hierarchy", recursive=True)
    
    parent = aliased(apiPath_hierarchy, name="ap")
    
    query = db.query(
        Function.FUNC_ID,
        Function.FUNC_PARENT_ID,
        Function.FUNC_NAME,
        Function.API_PATH,
        Function.ICON
    ).join(parent, Function.FUNC_PARENT_ID == parent.c.FUNC_ID)
    
    if roleId != 1:
        query = query.outerjoin(Role_Function, Role_Function.FUNC_ID == Function.FUNC_ID) \
                     .filter(Role_Function.FUNC_ID.is_(None))
    
    apiPath_hierarchy = apiPath_hierarchy.union_all(query)
    
    result = db.query(
        apiPath_hierarchy.c.FUNC_ID,
        apiPath_hierarchy.c.FUNC_PARENT_ID,
        apiPath_hierarchy.c.FUNC_NAME,
        apiPath_hierarchy.c.API_PATH,
        apiPath_hierarchy.c.ICON
    ).all()
    
    result_list_of_dicts = [
        {
            'FUNC_ID': row[0],
            'FUNC_PARENT_ID': row[1],
            'FUNC_NAME': row[2],
            'API_PATH': row[3],
            'ICON': row[4]
        }
        for row in result
    ]
    
    return result_list_of_dicts









  


    

