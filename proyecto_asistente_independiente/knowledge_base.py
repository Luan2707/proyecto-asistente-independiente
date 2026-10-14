import unicodedata
from typing import Any, Dict, List


class KnowledgeBase:
    def __init__(self):
        self.rules = [
            {
                "id": "R1",
                "nombre": "Nivel básico prioriza fundamentos",
                "condicion": "nivel == 'Básico'",
                "accion": "Priorizar recursos introductorios y fundamentos (+15 pts)",
            },
            {
                "id": "R2",
                "nombre": "Horas limitadas prioriza cursos cortos",
                "condicion": "horas_disponibles < 5",
                "accion": "Priorizar recursos con duracion_horas <= 4",
            },
            {
                "id": "R3",
                "nombre": "Modalidad práctica o proyecto",
                "condicion": "modalidad in ['Práctica', 'Proyecto']",
                "accion": "Priorizar talleres, laboratorios y proyectos aplicados (+10 pts)",
            },
            {
                "id": "R4",
                "nombre": "Objetivo de programación",
                "condicion": "objetivo menciona programar, código, desarrollo o software",
                "accion": "Priorizar recursos de Programación y Python",
            },
            {
                "id": "R5",
                "nombre": "Tema de Inteligencia Artificial",
                "condicion": "tema == 'Inteligencia Artificial'",
                "accion": "Añadir temas de búsqueda, reglas y LLMs",
            },
        ]

    @staticmethod
    def _normalize(value: str) -> str:
        text = unicodedata.normalize("NFD", str(value or "")).lower()
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")
        return " ".join(text.replace("-", " ").split())

    @staticmethod
    def _hours(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def evaluate(self, profile: Dict[str, Any], resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        perfil = profile or {}
        objetivo = self._normalize(perfil.get("objetivo", ""))
        nivel = self._normalize(perfil.get("nivel", ""))
        horas = self._hours(perfil.get("horas", 0))
        modalidad = self._normalize(perfil.get("modalidad", ""))
        tema = self._normalize(perfil.get("tema", ""))

        reglas_activadas = []
        for regla in self.rules:
            trigger = False
            if regla["id"] == "R1" and nivel == "basico":
                trigger = True
            elif regla["id"] == "R2" and horas < 5:
                trigger = True
            elif regla["id"] == "R3" and modalidad in {"practica", "proyecto"}:
                trigger = True
            elif regla["id"] == "R4" and any(
                palabra in objetivo
                for palabra in ["programar", "codigo", "desarrollo", "software"]
            ):
                trigger = True
            elif regla["id"] == "R5" and tema == "inteligencia artificial":
                trigger = True

            if trigger:
                reglas_activadas.append({
                    "id": regla["id"],
                    "nombre": regla["nombre"],
                    "condicion": regla["condicion"],
                    "accion": regla["accion"],
                })

        ranking = []
        for recurso in resources:
            score = 0
            titulo = self._normalize(recurso.get("titulo", ""))
            categoria = self._normalize(recurso.get("categoria", ""))
            palabras = self._normalize(" ".join(recurso.get("palabras_clave", [])))

            if nivel == "basico" and (
                "fundamento" in titulo
                or "intro" in titulo
                or "python" in palabras
                or "bases" in titulo
            ):
                score += 15
            if horas < 5 and float(recurso.get("duracion_horas", 0)) <= 4:
                score += 10
            if modalidad in {"practica", "proyecto"} and self._normalize(
                recurso.get("modalidad", "")
            ) in {"practica", "proyecto"}:
                score += 10
            if any(
                palabra in objetivo
                for palabra in ["programar", "codigo", "desarrollo", "software"]
            ) and (
                "python" in palabras
                or "programacion" in categoria
                or "desarrollo" in categoria
            ):
                score += 15
            subcategoria = self._normalize(recurso.get("subcategoria", ""))
            if tema == "inteligencia artificial" and (
                subcategoria in {"busqueda", "reglas", "llms"}
                or any(word in palabras for word in ["search", "busqueda", "reglas", "llm", "ia"])
            ):
                score += 10

            if self._normalize(recurso.get("nivel", "")) == nivel:
                score += 8
            ranking.append({**recurso, "score": score})

        ranked = sorted(ranking, key=lambda item: item["score"], reverse=True)
        if tema == "inteligencia artificial":
            required_subcategories = {"busqueda", "reglas", "llms"}
            required = [
                item for item in ranked
                if self._normalize(item.get("subcategoria", "")) in required_subcategories
            ]
            remaining = [item for item in ranked if item not in required]
            ranked = (required + remaining)[:6]

        return {
            "reglas_activadas": reglas_activadas,
            "recommended_resources": ranked[:6],
            "ranking": ranked,
        }
