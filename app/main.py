from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Jalankan FastAPI 🚀"}

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

@app.get("/calculate/power")
def power(a: float, b: float):
    """Menghitung pangkat a ^ b"""
    result = a ** b
    return {"a": a, "b": b, "operation": "power", "result": result}

@app.get("/calculate/modulo")
def modulo(a: float, b: float):
    """Menghitung sisa bagi a % b"""
    if b == 0:
        return {"error": "Tidak bisa membagi dengan 0"}
    result = a % b
    return {"a": a, "b": b, "operation": "modulo", "result": result}

@app.get("/calculate/sqrt")
def sqrt(n: float):
    """Menghitung akar kuadrat dari n"""
    if n < 0:
        return {"error": "Tidak bisa akar dari angka negatif"}
    result = n ** 0.5
    return {"n": n, "operation": "sqrt", "result": result}

@app.get("/calculate/percentage")
def percentage(value: float, percent: float):
    """Menghitung persentase dari nilai"""
    result = (value * percent) / 100
    return {"value": value, "percent": percent, "operation": "percentage", "result": result}

@app.get("/calculate/average")
def average(numbers: str):
    """Menghitung rata-rata dari daftar angka (comma-separated)"""
    try:
        nums = [float(n.strip()) for n in numbers.split(",")]
        if len(nums) == 0:
            return {"error": "Tidak ada angka untuk dihitung"}
        result = sum(nums) / len(nums)
        return {"numbers": nums, "operation": "average", "result": result}
    except ValueError:
        return {"error": "Format tidak valid, gunakan angka dipisahkan koma (contoh: 1,2,3,4,5)"}

