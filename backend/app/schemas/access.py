from typing import Literal

from pydantic import BaseModel

from app.core.roles import RoleName


class AdminAccessResponse(BaseModel):
    authenticated: Literal[True] = True
    role: Literal[RoleName.ADMIN] = RoleName.ADMIN

