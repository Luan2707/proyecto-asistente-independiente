import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from ai_services import generate_learning_plan, rerank_resources_with_cohere
from knowledge_base import KnowledgeBase
from search_engine import SearchEngine

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "recursos_educativos.json"

app = Flask(__name__, template_folder="templates", static_folder="static")


with DATA_PATH.open("r", encoding="utf-8") as file:
    RESOURCES = json.load(file)

search_engine = SearchEngine(RESOURCES)
knowledge_base = KnowledgeBase()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/recursos")
def get_recursos():
    return jsonify({"recursos": RESOURCES})


@app.post("/api/buscar")
def buscar_recurso():
    datos = request.get_json(silent=True) or {}
    algoritmo = datos.get("algoritmo", "Lineal")
    consulta = datos.get("consulta", "")
    perfil = datos.get("perfil", {})
    if not isinstance(perfil, dict):
        perfil = {}
    resultado = search_engine.execute_algorithm(algoritmo, consulta, perfil)
    return jsonify(resultado)


@app.post("/api/comparar")
def comparar_algoritmos():
    datos = request.get_json(silent=True) or {}
    consulta = datos.get("consulta", "inteligencia artificial")
    perfil = datos.get("perfil", {})
    if not isinstance(perfil, dict):
        perfil = {}
    resultado = search_engine.compare_algorithms(consulta, perfil)
    return jsonify(resultado)


@app.post("/api/recomendar")
def recomendar_recursos():
    datos = request.get_json(silent=True) or {}
    perfil = {
        "nombre": datos.get("nombre", "Estudiante"),
        "tema": datos.get("tema", "Inteligencia Artificial"),
        "nivel": datos.get("nivel", "Básico"),
        "horas": datos.get("horas", 5),
        "modalidad": datos.get("modalidad", "Práctica"),
        "objetivo": datos.get("objetivo", "Aprender sobre IA y desarrollo de software"),
    }

    regla_result = knowledge_base.evaluate(perfil, RESOURCES)
    recommended = regla_result.get("recommended_resources", [])

    query = f"{perfil.get('tema', '')} {perfil.get('objetivo', '')}"
    rerank = rerank_resources_with_cohere(query, recommended if recommended else RESOURCES)
    ranked_resources = rerank.get("results", [])

    plan_data = generate_learning_plan(perfil, ranked_resources)

    return jsonify({
        "perfil": perfil,
        "reglas_activadas": regla_result.get("reglas_activadas", []),
        "ranking_final": ranked_resources[:6],
        "origen_semantica": rerank.get("source", "Modo Fallback Local"),
        "mensaje_semantica": rerank.get("message", ""),
        "plan": plan_data.get("plan", ""),
        "origen_plan": plan_data.get("source", "Modo Fallback Local"),
        "mensaje_plan": plan_data.get("message", ""),
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
