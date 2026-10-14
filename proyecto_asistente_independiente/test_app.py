import json
import os
import unittest
from pathlib import Path

os.environ.pop("COHERE_API_KEY", None)
os.environ.pop("OPENROUTER_API_KEY", None)

from app import RESOURCES, app, search_engine


class AssistantTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_database_count_and_schema(self):
        expected = {
            "codigo", "titulo", "categoria", "subcategoria", "nivel",
            "modalidad", "duracion_horas", "palabras_clave", "descripcion",
        }
        self.assertGreaterEqual(len(RESOURCES), 20)
        self.assertTrue(all(set(resource) == expected for resource in RESOURCES))

    def test_five_algorithms_return_trace_and_metrics(self):
        for algorithm in ("Lineal", "Binaria", "DFS", "BFS", "Heuristica"):
            response = self.client.post(
                "/api/buscar",
                json={
                    "algoritmo": algorithm,
                    "consulta": "búsqueda en IA",
                    "perfil": {
                        "tema": "Inteligencia Artificial",
                        "nivel": "Intermedio",
                        "horas": 6,
                        "modalidad": "Práctica",
                        "objetivo": "programar con Python",
                    },
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn("tiempo_ms", data)
            self.assertIn("elementos_revisados", data)
            self.assertIn("traza", data)

    def test_bfs_is_level_order(self):
        result = search_engine.bfs_tree_search("búsqueda")
        types = [item["tipo"] for item in result["traza"]]
        first_subcategory = types.index("subcategoria")
        first_resource = types.index("recurso")
        self.assertTrue(all(item == "categoria" for item in types[:first_subcategory]))
        self.assertTrue(all(item == "subcategoria" for item in types[first_subcategory:first_resource]))

    def test_all_rules_and_local_fallback(self):
        response = self.client.post(
            "/api/recomendar",
            json={
                "tema": "Inteligencia Artificial",
                "nivel": "Básico",
                "horas": "no-numérico",
                "modalidad": "Práctica",
                "objetivo": "programar código y desarrollo",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(
            [rule["id"] for rule in data["reglas_activadas"]],
            ["R1", "R2", "R3", "R4", "R5"],
        )
        self.assertEqual(data["origen_semantica"], "Modo Fallback Local")
        self.assertEqual(data["origen_plan"], "Modo Fallback Local")

    def test_compare_runs_five_algorithms(self):
        response = self.client.post("/api/comparar", json={"consulta": "python"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["algoritmos"]), 5)


if __name__ == "__main__":
    unittest.main()
