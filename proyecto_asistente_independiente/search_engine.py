import re
import time
import unicodedata
from collections import deque
from typing import Any, Dict, List


class SearchEngine:
    def __init__(self, resources: List[Dict[str, Any]]):
        self.resources = resources
        self.tree = self.build_hierarchy(resources)

    @staticmethod
    def _remove_accents(value: str) -> str:
        text = unicodedata.normalize("NFD", str(value))
        return "".join(
            char for char in text
            if unicodedata.category(char) != "Mn"
        )

    def build_hierarchy(
        self,
        resources: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        tree: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for recurso in resources:
            categoria = recurso.get("categoria", "General")
            subcategoria = recurso.get("subcategoria", "General")
            tree.setdefault(categoria, {})
            tree[categoria].setdefault(subcategoria, [])
            tree[categoria][subcategoria].append(recurso)
        return tree

    @staticmethod
    def _normalize(value: str) -> str:
        text = SearchEngine._remove_accents(value).lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return " ".join(text.split())

    @staticmethod
    def _to_text(resource: Dict[str, Any]) -> str:
        return SearchEngine._normalize(" ".join([
            str(resource.get("titulo", "")),
            str(resource.get("categoria", "")),
            str(resource.get("subcategoria", "")),
            " ".join(resource.get("palabras_clave", [])),
            str(resource.get("descripcion", "")),
        ]))

    def _matches_query(self, resource: Dict[str, Any], query: str) -> bool:
        query_tokens = self._normalize(query).split()
        if not query_tokens:
            return True
        resource_tokens = set(self._to_text(resource).split())
        return all(token in resource_tokens for token in query_tokens)

    def linear_search(self, query: str) -> Dict[str, Any]:
        start = time.perf_counter()
        traza = []
        revisados = []
        coincidencias = []
        for indice, recurso in enumerate(self.resources):
            coincide = self._matches_query(recurso, query)
            traza.append({
                "paso": indice + 1,
                "titulo": recurso.get("titulo"),
                "comparacion": f"Buscar '{query}' en titulo/categoria/keywords",
                "resultado": "coincide" if coincide else "no coincide",
            })
            revisados.append(recurso.get("codigo"))
            if coincide:
                coincidencias.append(recurso)
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "algoritmo": "Lineal",
            "tiempo_ms": round(elapsed, 3),
            "pasos": len(traza),
            "elementos_revisados": revisados,
            "coincidencias": coincidencias,
            "traza": traza,
            "complejidad": "O(n)",
        }

    def binary_search(self, query: str) -> Dict[str, Any]:
        ordered = sorted(self.resources, key=lambda r: self._normalize(r.get("titulo", "")))
        inicio, fin = 0, len(ordered) - 1
        traza = []
        revisados = []
        coincidencias = []
        start = time.perf_counter()
        query_normalizada = self._normalize(query)

        while inicio <= fin:
            medio = (inicio + fin) // 2
            pivote = ordered[medio]
            revisados.append(pivote.get("codigo"))
            rango = f"[{inicio}..{fin}]"
            valor = self._normalize(pivote.get("titulo", ""))
            traza.append({
                "rango": rango,
                "indice_medio": medio,
                "pivot": valor,
                "comparacion": f"Comparar '{query}' con '{valor}'",
            })

            if query_normalizada in valor:
                coincidencias.append(pivote)
                break
            if query_normalizada < valor:
                fin = medio - 1
            else:
                inicio = medio + 1

        elapsed = (time.perf_counter() - start) * 1000
        return {
            "algoritmo": "Binaria",
            "tiempo_ms": round(elapsed, 3),
            "pasos": len(traza),
            "elementos_revisados": revisados,
            "coincidencias": coincidencias,
            "traza": traza,
            "complejidad": "O(log n)",
        }

    def dfs_tree_search(self, query: str) -> Dict[str, Any]:
        start = time.perf_counter()
        traza = []
        coincidencias = []

        def recorrer(node: Dict[str, Any], path: str = ""):
            for key, value in node.items():
                if isinstance(value, list):
                    traza.append({"nodo": f"{path}/{key}", "tipo": "recurso", "valor": key})
                    for item in value:
                        if self._matches_query(item, query):
                            coincidencias.append(item)
                        traza.append({
                            "nodo": f"{path}/{key}/{item.get('codigo', '')}",
                            "tipo": "recurso_inspeccionado",
                            "titulo": item.get("titulo", ""),
                        })
                elif isinstance(value, dict):
                    node_type = "categoria" if not path else "subcategoria"
                    traza.append({"nodo": f"{path}/{key}", "tipo": node_type, "valor": key})
                    recorrer(value, f"{path}/{key}")

        recorrer(self.tree)
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "algoritmo": "DFS",
            "tiempo_ms": round(elapsed, 3),
            "pasos": len(traza),
            "elementos_revisados": [item.get("nodo") for item in traza if item.get("tipo") == "recurso_inspeccionado"],
            "coincidencias": coincidencias,
            "traza": traza,
            "complejidad": "O(n)",
        }

    def bfs_tree_search(self, query: str) -> Dict[str, Any]:
        start = time.perf_counter()
        cola = deque(
            (categoria, "categoria", subcategorias)
            for categoria, subcategorias in self.tree.items()
        )
        traza = []
        coincidencias = []

        while cola:
            node, node_type, content = cola.popleft()
            trace_item = {"nodo": node, "tipo": node_type, "valor": node}
            traza.append(trace_item)

            if node_type == "categoria":
                for subcategoria, recursos in content.items():
                    cola.append((f"{node}/{subcategoria}", "subcategoria", recursos))
            elif node_type == "subcategoria":
                for recurso in content:
                    cola.append((f"{node}/{recurso.get('codigo', '')}", "recurso", recurso))
            else:
                recurso = content
                trace_item["titulo"] = recurso.get("titulo", "")
                if self._matches_query(recurso, query):
                    coincidencias.append(recurso)

        elapsed = (time.perf_counter() - start) * 1000
        return {
            "algoritmo": "BFS",
            "tiempo_ms": round(elapsed, 3),
            "pasos": len(traza),
            "elementos_revisados": [item.get("nodo") for item in traza if item.get("tipo") == "recurso"],
            "coincidencias": coincidencias,
            "traza": traza,
            "complejidad": "O(n)",
        }

    def heuristic_search(self, profile: Dict[str, Any], query: str) -> Dict[str, Any]:
        start = time.perf_counter()
        resultado = []
        for recurso in self.resources:
            score = 0
            tema = self._normalize(profile.get("tema", ""))
            objetivo = self._normalize(profile.get("objetivo", ""))
            nivel = profile.get("nivel", "")
            modalidad = profile.get("modalidad", "")
            try:
                horas = float(profile.get("horas", 0) or 0)
            except (TypeError, ValueError):
                horas = 0

            if tema and tema in self._normalize(recurso.get("categoria", "")):
                score += 35
            if nivel and recurso.get("nivel") == nivel:
                score += 20
            if modalidad and recurso.get("modalidad") == modalidad:
                score += 15
            if recurso.get("duracion_horas", 0) <= horas:
                score += 15

            palabras_objetivo = set(self._normalize(f"{query} {objetivo}").split())
            palabras_recurso = set(self._normalize(" ".join(recurso.get("palabras_clave", []))).split())
            overlap = len(palabras_objetivo.intersection(palabras_recurso))
            score += min(15, overlap * 15)

            resultado.append({**recurso, "score": score})

        ranking = sorted(resultado, key=lambda r: r["score"], reverse=True)
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "algoritmo": "Heurística",
            "tiempo_ms": round(elapsed, 3),
            "pasos": len(ranking),
            "elementos_revisados": [r.get("codigo") for r in ranking],
            "coincidencias": ranking[:10],
            "traza": [{"recurso": r.get("codigo"), "score": r.get("score")} for r in ranking[:10]],
            "complejidad": "O(n)",
        }

    def execute_algorithm(self, algorithm: str, query: str, profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
        algo = self._remove_accents((algorithm or "Lineal").strip()).lower().replace(" ", "")
        if algo in {"lineal", "linear"}:
            return self.linear_search(query)
        if algo in {"binaria", "binary"}:
            return self.binary_search(query)
        if algo in {"dfs", "depthfirst", "profundidad"}:
            return self.dfs_tree_search(query)
        if algo in {"bfs", "breadthfirst", "anchura"}:
            return self.bfs_tree_search(query)
        if algo in {"heuristica", "heuristic"}:
            return self.heuristic_search(profile or {}, query)
        return self.linear_search(query)

    def compare_algorithms(self, query: str, profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
        algorithms = ["Lineal", "Binaria", "DFS", "BFS", "Heurística"]
        resultados = []
        for nombre in algorithms:
            resultado = self.execute_algorithm(nombre, query, profile or {})
            resultados.append({
                "Algoritmo": resultado["algoritmo"],
                "Tiempo (ms)": resultado["tiempo_ms"],
                "Pasos ejecutados": resultado["pasos"],
                "Elementos revisados": len(resultado["elementos_revisados"]),
                "Coincidencias encontradas": len(resultado["coincidencias"]),
                "Complejidad temporal": resultado["complejidad"],
            })
        return {"algoritmos": resultados, "consulta": query}
