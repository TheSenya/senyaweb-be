from typing import Optional
from fastapi import Request, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta

# create a function that tracks the amount of time the password has been entered incorrectly
# if the amount of time was exceeded then block the user via the ip address 

class Blocked(BaseModel):
    ip: str
    user_agent: Optional[str] = None  # Optional since header might be missing
    attempts: int = 0
    block_timeout: Optional[datetime] = None
    first_attempt_time: Optional[datetime] = None
    last_attempt_time: Optional[datetime] = None

BLOCKED = {} # TODO: change to store this in the DB or redis
MAX_FAILURES = 10
BLOCK_LOCKOUT_TIME = 15 * 60 # 15 minutes

async def rate_limit_gaurd(req: Request):

    ip_address = req.client.host
    user_agent = req.headers.get("user-agent")

    # check if the user is in the block dict and has a timeout
    if ip_address in BLOCKED and BLOCKED[ip_address].block_timeout:
        # check if user is currently blocked
        if BLOCKED[ip_address].block_timeout >= datetime.now():
            # calculate remaining wait time
            wait_time = int((BLOCKED[ip_address].block_timeout - datetime.now()).total_seconds())
            # stop this user from being able to access the API
            raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Too many attempts. Blocked for {wait_time}s."
                )
        # if the user is not currently block remove the block
        else:
            BLOCKED[ip_address].block_timeout = None

    # yield to the route
    try:
        yield # this hands the control to the endpoint function
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            _register_failure(ip_address, user_agent)
        raise  # re-raise without 'e' to preserve full traceback


def _register_failure(ip: str, user_agent: str):

    cur_time = datetime.now()
    
    # if the user does not exist in blocked create them
    if ip not in BLOCKED:
        BLOCKED[ip] = Blocked(
            ip=ip,
            user_agent=user_agent,
            attempts=0,
            first_attempt_time=cur_time
        )
    
    BLOCKED[ip].attempts += 1
    
    # if block count >= MAX_FAILURES then block the user
    if BLOCKED[ip].attempts >= MAX_FAILURES:
        BLOCKED[ip].last_attempt_time = cur_time
        BLOCKED[ip].block_timeout = cur_time + timedelta(seconds=BLOCK_LOCKOUT_TIME)
    # if block count is from 1 - 4 then set the last_attempt_time
    else:
        BLOCKED[ip].last_attempt_time = cur_time







            
    


    
    

    


    