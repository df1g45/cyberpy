from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FastAPI is running 🚀"}

@app.get("/calculate/add")
def add(a: float, b: float):
    """Menghitung penjumlahan a + b"""
    result = a + b
    return {"a": a, "b": b, "operation": "add", "result": result}

@app.get("/calculate/subtract")
def subtract(a: float, b: float):
    """Menghitung pengurangan a - b"""
    result = a - b
    return {"a": a, "b": b, "operation": "subtract", "result": result}

@app.get("/calculate/multiply")
def multiply(a: float, b: float):
    """Menghitung perkalian a * b"""
    result = a * b
    return {"a": a, "b": b, "operation": "multiply", "result": result}

@app.get("/calculate/divide")
def divide(a: float, b: float):
    """Menghitung pembagian a / b"""
    if b == 0:
        return {"error": "Tidak bisa membagi dengan 0"}
    result = a / b
    return {"a": a, "b": b, "operation": "divide", "result": result}
