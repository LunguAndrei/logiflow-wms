from fastapi import FastAPI

app = FastAPI(title="LogiFlow WMS")


@app.get("/health")
def health_check():
	return {"status": "ok"}
