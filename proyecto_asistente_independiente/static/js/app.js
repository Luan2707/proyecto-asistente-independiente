const API_BASE = '/api';

function setStatus(message, type = 'muted') {
  const status = document.getElementById('search-status');
  status.className = `status ${type}`;
  status.textContent = message;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Error HTTP ${response.status}`);
  }
  return data;
}

function renderTrace(data) {
  const box = document.getElementById('search-trace');
  box.replaceChildren();
  if (!data || !Array.isArray(data.traza) || data.traza.length === 0) {
    const empty = document.createElement('p');
    empty.textContent = 'No se generó una traza para esta búsqueda.';
    box.appendChild(empty);
    return;
  }

  const heading = document.createElement('h3');
  heading.textContent = `Traza de ${data.algoritmo}`;
  box.appendChild(heading);

  const summary = document.createElement('p');
  summary.textContent = `Tiempo: ${data.tiempo_ms} ms | Pasos: ${data.pasos} | Revisados: ${data.elementos_revisados?.length ?? 0}`;
  box.appendChild(summary);

  const matchesHeading = document.createElement('h4');
  matchesHeading.textContent = `Coincidencias encontradas (${data.coincidencias?.length ?? 0})`;
  box.appendChild(matchesHeading);

  const matchesList = document.createElement('ul');
  (data.coincidencias || []).forEach((resource) => {
    const item = document.createElement('li');
    item.textContent = `${resource.codigo}: ${resource.titulo}`;
    matchesList.appendChild(item);
  });
  if (!matchesList.children.length) {
    const item = document.createElement('li');
    item.textContent = 'No se encontraron recursos.';
    matchesList.appendChild(item);
  }
  box.appendChild(matchesList);

  const traceHeading = document.createElement('h4');
  traceHeading.textContent = 'Pasos ejecutados';
  box.appendChild(traceHeading);

  const traceList = document.createElement('ol');
  data.traza.forEach((trace) => {
    const item = document.createElement('li');
    item.textContent = formatTraceItem(trace);
    traceList.appendChild(item);
  });
  box.appendChild(traceList);
}

function formatTraceItem(item) {
    if (item.paso) {
      return `Paso ${item.paso}: ${item.titulo} | resultado: ${item.resultado}`;
    }
    if (item.rango) {
      return `Intervalo ${item.rango} | centro: ${item.indice_medio} | elemento central: ${item.pivot}`;
    }
    if (item.nodo) {
      return `Nodo: ${item.nodo} | tipo: ${item.tipo} | ${item.titulo || item.valor || ''}`;
    }
    return `Recurso: ${item.recurso || item.titulo || item.valor || ''} | puntuación: ${item.score ?? ''}`;
}

function renderComparison(rows) {
  const tbody = document.querySelector('#comparacion-table tbody');
  tbody.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    [
      row['Algoritmo'],
      row['Tiempo (ms)'],
      row['Pasos ejecutados'],
      row['Elementos revisados'],
      row['Coincidencias encontradas'],
      row['Complejidad temporal'],
    ].forEach((value) => {
      const cell = document.createElement('td');
      cell.textContent = value;
      tr.appendChild(cell);
    });
    tbody.appendChild(tr);
  });
}

function renderRules(rules) {
  const panel = document.getElementById('rules-panel');
  panel.innerHTML = '';
  if (!rules || !rules.length) {
    panel.innerHTML = '<span class="badge">Sin reglas activadas.</span>';
    return;
  }

  rules.forEach((rule) => {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = `${rule.id}: ${rule.nombre}`;
    panel.appendChild(badge);
  });
}

function renderResources(resources) {
  const container = document.getElementById('resource-cards');
  container.innerHTML = '';
  if (!resources || !resources.length) {
    container.innerHTML = '<p>No se encontraron recursos.</p>';
    return;
  }

  resources.forEach((resource) => {
    const card = document.createElement('article');
    card.className = 'resource-card';

    const title = document.createElement('h4');
    title.textContent = resource.titulo;
    card.appendChild(title);

    const description = document.createElement('p');
    description.textContent = resource.descripcion;
    card.appendChild(description);

    const metadata = document.createElement('div');
    metadata.className = 'meta';
    [
      resource.categoria,
      resource.subcategoria,
      resource.nivel,
      resource.modalidad,
      `${resource.duracion_horas}h`,
    ].forEach((value) => {
      const tag = document.createElement('span');
      tag.textContent = value;
      metadata.appendChild(tag);
    });
    card.appendChild(metadata);
    container.appendChild(card);
  });
}

function renderPlan(planText) {
  const panel = document.getElementById('plan-panel');
  panel.replaceChildren();
  if (!planText) {
    const empty = document.createElement('p');
    empty.textContent = 'Sin plan generado.';
    panel.appendChild(empty);
    return;
  }

  let list = null;
  let listType = null;
  const addListItem = (tagName, text) => {
    if (listType !== tagName) {
      list = document.createElement(tagName);
      panel.appendChild(list);
      listType = tagName;
    }
    const item = document.createElement('li');
    item.textContent = text;
    list.appendChild(item);
  };

  planText.split(/\r?\n/).forEach((line) => {
    const text = line.trim();
    if (!text) {
      list = null;
      listType = null;
      return;
    }

    const heading = text.match(/^#{1,6}\s+(.+)$/);
    const bullet = text.match(/^[-*]\s+(.+)$/);
    const numbered = text.match(/^\d+[.)]\s+(.+)$/);

    if (heading) {
      list = null;
      listType = null;
      const title = document.createElement(heading[0].startsWith('# ') ? 'h2' : 'h3');
      title.textContent = heading[1];
      panel.appendChild(title);
    } else if (bullet) {
      addListItem('ul', bullet[1]);
    } else if (numbered) {
      addListItem('ol', numbered[1]);
    } else {
      list = null;
      listType = null;
      const paragraph = document.createElement('p');
      paragraph.textContent = text;
      panel.appendChild(paragraph);
    }
  });
}

async function buscar() {
  const algoritmo = document.getElementById('algoritmo').value;
  const consulta = document.getElementById('consulta').value.trim();

  if (!consulta) {
    setStatus('Debes ingresar una consulta.', 'error');
    return;
  }

  setStatus('Ejecutando búsqueda...', 'success');
  try {
    const perfil = {
      tema: document.getElementById('tema').value || '',
      nivel: document.getElementById('nivel').value || '',
      horas: Number(document.getElementById('horas').value || 0),
      modalidad: document.getElementById('modalidad').value || '',
      objetivo: document.getElementById('objetivo').value || '',
    };
    const data = await fetchJson(`${API_BASE}/buscar`, {
      method: 'POST',
      body: JSON.stringify({ algoritmo, consulta, perfil }),
    });

    renderTrace(data);
    setStatus(`Búsqueda finalizada con ${data.coincidencias?.length ?? 0} coincidencias.`, 'success');
  } catch (error) {
    setStatus(`No fue posible ejecutar la búsqueda: ${error.message}`, 'error');
  }
}

async function comparar() {
  const consulta = document.getElementById('consulta').value.trim() || 'inteligencia artificial';
  try {
    const data = await fetchJson(`${API_BASE}/comparar`, {
      method: 'POST',
      body: JSON.stringify({ consulta, perfil: {} }),
    });
    renderComparison(data.algoritmos || []);
    setStatus('Comparativa ejecutada correctamente.', 'success');
  } catch (error) {
    setStatus(`No fue posible comparar: ${error.message}`, 'error');
  }
}

async function recomendar() {
  const perfil = {
    nombre: document.getElementById('nombre').value || 'Estudiante',
    tema: document.getElementById('tema').value || 'Inteligencia Artificial',
    nivel: document.getElementById('nivel').value || 'Básico',
    horas: Number(document.getElementById('horas').value || 5),
    modalidad: document.getElementById('modalidad').value || 'Práctica',
    objetivo: document.getElementById('objetivo').value || 'Aprender con práctica y recursos claros.',
  };

  setStatus('Generando recomendación y plan de estudio...', 'success');
  try {
    const data = await fetchJson(`${API_BASE}/recomendar`, {
      method: 'POST',
      body: JSON.stringify(perfil),
    });

    renderRules(data.reglas_activadas || []);
    renderResources(data.ranking_final || []);
    renderPlan(data.plan || 'Sin plan disponible.');
    setStatus(`${data.origen_plan || 'Fallback'} y ${data.origen_semantica || 'Fallback'} aplicados.`, 'success');
  } catch (error) {
    setStatus(`No fue posible generar la recomendación: ${error.message}`, 'error');
  }
}

document.getElementById('buscar-btn').addEventListener('click', buscar);
document.getElementById('comparar-btn').addEventListener('click', comparar);
document.getElementById('perfil-form').addEventListener('submit', (event) => {
  event.preventDefault();
  recomendar();
});
