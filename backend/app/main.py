from fastapi import FastAPI

app = FastAPI(title="Memo App API")


@app.get("/health")
def health() -> dict[str, str]:
    """ヘルスチェック。"""
    return {"status": "ok"}
