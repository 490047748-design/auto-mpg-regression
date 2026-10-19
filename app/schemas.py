"""定义预测接口接受的参数和返回的数据。"""

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """用户提交的七个车辆参数。"""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    cylinders: int = Field(ge=3, le=12)
    displacement: float = Field(gt=0, le=1000)
    horsepower: float = Field(gt=0, le=600)
    weight: float = Field(gt=0, le=6000)
    acceleration: float = Field(gt=0, le=40)
    model_year: int = Field(ge=1970, le=1982)
    origin: int = Field(ge=1, le=3)


class PredictionResponse(BaseModel):
    """接口返回的预测值及模型环境信息。"""

    mpg: float
    unit: str = "mpg"
    model_version: str
    app_env: str
