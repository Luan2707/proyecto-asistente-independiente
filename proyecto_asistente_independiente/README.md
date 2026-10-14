# Asistente de recursos educativos

Aplicación Flask para buscar recursos, comparar algoritmos, activar reglas de inferencia y generar rutas de estudio.

## Requisitos previos

- Python 3.10+
- pip
- Navegador web

## 1. Crear entorno virtual

### Windows

```powershell
cd C:\proyecto_asistente_independiente
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
cd /ruta/al/proyecto/proyecto_asistente
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 3. Configurar variables de entorno

Copia el archivo de ejemplo:

```bash
copy .env.example .env
```

En Linux/macOS:

```bash
cp .env.example .env
```

Edita `.env` y añade tus claves reales si las tienes. Si no existen, la aplicación seguirá funcionando usando fallback local.

`OPENROUTER_MODEL` permite seleccionar el modelo. Su valor por defecto es `openrouter/auto`.

## 4. Ejecutar la aplicación

```bash
python app.py
```

Luego abre en el navegador:

```text
http://127.0.0.1:5000
```

## 5. Fallback local

Si faltan las claves, falla la conexión o una API devuelve un error, la aplicación usa similitud de Jaccard y genera una plantilla local de plan de estudio.

## 6. Casos de prueba para la demostración

### Caso 1: búsqueda lineal

Entrada: algoritmo `Lineal`, consulta `búsqueda en IA`.

Salida: traza, recursos revisados, tiempo en milisegundos y coincidencias.

### Caso 2: comparación

Entrada: consulta `programación con python` y botón `Comparar 5 algoritmos`.

Salida: tabla con Lineal, Binaria, DFS, BFS y Heurística; incluye tiempo, pasos, revisados, coincidencias y complejidad.

### Caso 3: recomendación personalizada

Entrada: Ana, Inteligencia Artificial, Intermedio, 6 horas, modalidad Práctica y objetivo `Quiero aprender a programar con Python y desarrollar sistemas inteligentes con IA.`

Salida: reglas activadas, recursos recomendados, plan pedagógico y origen de cada servicio.

## 7. Estructura de archivos

```text
proyecto_asistente/
├── app.py
├── ai_services.py
├── knowledge_base.py
├── search_engine.py
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   └── recursos_educativos.json
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html
└── .venv/   (opcional, generado localmente)
```

## 8. Importante

No se incluye ninguna clave real en el repositorio. Las credenciales deben mantenerse en un `.env` local y no se debe subir al ZIP ni al control de versiones.

## 9. Pruebas automatizadas

Con el entorno virtual activado, ejecuta:

```powershell
python -m unittest -v test_app.py
```

Las pruebas verifican la cantidad y el esquema de recursos, los cinco algoritmos, el orden por niveles de BFS, las cinco reglas, el fallback local y el comparador.
