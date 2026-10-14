import json
import os
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()


def _token_set(text: str) -> set:
    return set(str(text or "").lower().replace("-", " ").split())


def jaccard_similarity(query: str, resource: Dict[str, Any]) -> float:
    consulta_tokens = _token_set(query)
    recurso_tokens = set()
    recurso_tokens.update(_token_set(resource.get("titulo", "")))
    recurso_tokens.update(_token_set(" ".join(resource.get("palabras_clave", []))))
    recurso_tokens.update(_token_set(resource.get("categoria", "")))
    if not consulta_tokens or not recurso_tokens:
        return 0.0
    union = consulta_tokens.union(recurso_tokens)
    inter = consulta_tokens.intersection(recurso_tokens)
    if not union:
        return 0.0
    return round(len(inter) / len(union), 4)


def rerank_resources_with_cohere(query: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    clave_api = os.getenv("COHERE_API_KEY")
    if not clave_api:
        ranked = sorted(resources, key=lambda item: jaccard_similarity(query, item), reverse=True)
        return {
            "source": "Modo Fallback Local",
            "results": ranked,
            "message": "No se encontró API key de Cohere; se aplicó similitud local con Jaccard.",
        }

    try:
        payload = {
            "model": "rerank-v3.5",
            "query": query,
            "documents": [
                {
                    "id": item.get("codigo"),
                    "text": f"{item.get('titulo', '')} {item.get('descripcion', '')} {' '.join(item.get('palabras_clave', []))}",
                }
                for item in resources
            ],
            "top_n": len(resources),
        }
        headers = {
            "Authorization": f"Bearer {clave_api}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://api.cohere.ai/v1/rerank",
            headers=headers,
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        ranked = []
        items_by_id = {item.get("codigo"): item for item in resources}
        for result in data.get("results", []):
            resource_id = result.get("document", {}).get("id")
            if resource_id in items_by_id:
                recurso = items_by_id[resource_id].copy()
                recurso["cohere_score"] = result.get("relevance_score", 0)
                ranked.append(recurso)

        if not ranked:
            raise ValueError("La respuesta de Cohere no devolvió documentos válidos.")

        return {
            "source": "API Externa (Cohere)",
            "results": ranked,
            "message": "Los recursos fueron ordenados con la API de Cohere.",
        }
    except (requests.RequestException, KeyError, TypeError, ValueError, AttributeError):
        ranked = sorted(resources, key=lambda item: jaccard_similarity(query, item), reverse=True)
        return {
            "source": "Modo Fallback Local",
            "results": ranked,
            "message": "La llamada a Cohere falló; se activó el fallback local por Jaccard.",
        }


def generate_learning_plan(profile: Dict[str, Any], resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    clave_api = os.getenv("OPENROUTER_API_KEY")
    modelo = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
    if not clave_api:
        plan = f"""
# Plan de estudio: {profile.get('tema', 'General')}

## 1. Diagnóstico inicial
- Estudiante: {profile.get('nombre', 'Estudiante')}
- Nivel: {profile.get('nivel', 'No especificado')}
- Horas semanales: {profile.get('horas', 0)}
- Modalidad preferida: {profile.get('modalidad', 'No especificada')}
- Objetivo: {profile.get('objetivo', 'Aprender de forma progresiva')}

## 2. Ruta recomendada
1. Inicia con fundamentos básicos y vocabulario clave del tema.
2. Estudia los recursos más relevantes y de menor duración disponible.
3. Aplica ejercicios prácticos o mini proyectos con los recursos sugeridos.
4. Revisa conceptos avanzados con recursos de profundización.
5. Evalúa tu progreso con una mini tarea final y repite los conceptos más complejos.

## 3. Recursos sugeridos
{chr(10).join(f'- {item.get("titulo", "")}: {item.get("descripcion", "")}' for item in resources[:5])}

## 4. Recomendaciones pedagógicas
- Divide el estudio en sesiones cortas y repetidas.
- Usa un cuaderno de ejercicios para anotar dudas.
- Prioriza la práctica antes que la lectura pasiva.
- Revisa al menos un recurso de cada nivel para consolidar progresión.
"""
        return {
            "source": "Modo Fallback Local",
            "plan": plan.strip(),
            "message": "No hay API key de OpenRouter; se generó una plantilla local de plan de estudio.",
        }

    try:
        headers = {
            "Authorization": f"Bearer {clave_api}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": modelo,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un tutor pedagógico experto. Genera un plan de estudio claro, ordenado y práctico. Usa markdown. Incluye objetivos, secuencia, recomendaciones y evaluaciones.",
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "perfil": profile,
                        "recursos": resources[:5],
                    }, ensure_ascii=False),
                },
            ],
            "temperature": 0.5,
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        respuesta = response.json()
        contenido = respuesta["choices"][0]["message"]["content"]
        return {
            "source": "API Externa (OpenRouter)",
            "plan": contenido,
            "message": "La ruta pedagógica fue generada por OpenRouter.",
        }
    except (requests.RequestException, KeyError, TypeError, ValueError, AttributeError):
        plan = f"""
# Plan de estudio local: {profile.get('tema', 'General')}

## 1. Objetivo
{profile.get('objetivo', 'Fortalecer el aprendizaje continuo')}

## 2. Ruta sugerida
1. Estudia primero los conceptos clave del tema.
2. Revisa los recursos más relevantes en tu nivel.
3. Completa prácticas cortas y breves ejercicios.
4. Profundiza con recursos avanzados si tienes tiempo.
5. Reafirma el aprendizaje con una tarea final.

## 3. Recursos recomendados
{chr(10).join(f'- {item.get("titulo", "")} ({item.get("modalidad", "")})' for item in resources[:5])}

## 4. Recomendaciones
- Organiza tu semana con bloques de 30 a 60 minutos.
- Haz al menos un ejercicio por recurso.
- Anota dudas y repite conceptos complejos.
"""
        return {
            "source": "Modo Fallback Local",
            "plan": plan.strip(),
            "message": "La llamada a OpenRouter falló; se usó la plantilla local.",
        }
