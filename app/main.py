"""Auto MPG 预测服务。"""

from pathlib import Path
from fastapi.responses import FileResponse
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.features import FEATURE_COLUMNS, payload_to_features, to_frame
from app.model import load_model
from app.schemas import PredictionRequest, PredictionResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时加载模型，成功后才开始接受请求。"""
    app.state.model = load_model()
    app.state.model_version = os.getenv("MODEL_VERSION", "6")
    app.state.app_env = os.getenv("APP_ENV", "development")
    yield
    del app.state.model


app = FastAPI(
    title="Auto MPG Prediction API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    """检查服务是否已成功启动。"""
    return {"status": "ok"}


@app.get("/model-info")
def model_info(request: Request):
    """返回当前服务的模型信息。"""
    return {
        "model_version": request.app.state.model_version,
        "app_env": request.app.state.app_env,
        "feature_columns": FEATURE_COLUMNS,
        "unit": "mpg",
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, request: Request):
    """校验输入、转换特征，然后调用模型预测。"""
    features = payload_to_features(payload.model_dump())
    frame = to_frame(features)
    prediction = request.app.state.model.predict(frame)

    return PredictionResponse(
        mpg=float(prediction[0]),
        model_version=request.app.state.model_version,
        app_env=request.app.state.app_env,
    )


@app.get("/", include_in_schema=False)
def index():
    """返回预测表单页面。"""
    page_path = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(page_path)
