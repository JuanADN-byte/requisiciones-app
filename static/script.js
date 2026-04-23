// static/script.js
let todasLasRequisiciones = [];
let usuarioActual = null;
const API = "https://excavate-pushover-stool.ngrok-free.dev/api";
function getToken() {
  return localStorage.getItem("token");
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "/";
}

async function cargarDashboard() {
  console.log("TOKEN:", localStorage.getItem("token"));
  const token = getToken();

  if (!token) {
    window.location.href = "/";
    return;
  }

  try {
    const res = await fetch(`${API}/usuarios/perfil`, {
      headers: { "Authorization": `Bearer ${getToken()}` }
    });

    if (!res.ok) {
      alert("Sesión expirada");
      logout();
      return;
    }

    const user = await res.json();

    // Título
    document.getElementById("titulo").innerHTML =
      `Hola, <strong>${user.nombre}</strong> (<em>${user.rol}</em>)`;

    // Ocultar todo
    document.querySelectorAll(".seccion")
      .forEach(s => s.style.display = "none");

    // Normalizar rol (sin tildes)
    const rol = user.rol.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

    const seccion = document.getElementById(rol);

    if (!seccion) {
      alert("Rol no soportado: " + user.rol);
      return;
    }

    seccion.style.display = "block";

    // Cargar datos según rol
    if (rol === "solicitante") {
    cargarMisRequisiciones();
  } else if (rol === "admin" || rol === "tecnico" || rol === "supervisor") {
    cargarTodasRequisiciones(user);
    if (rol === "admin") cargarListaUsuarios();
  }

  } catch (err) {
    alert("Error: " + err.message);
    logout();
  }
}

async function crearUsuario() {
  const nombre = document.getElementById("nombre").value.trim();
  const correo = document.getElementById("correo_admin").value.trim();
  const rol = document.getElementById("rol").value;
  const password = document.getElementById("contraseña_admin").value;

  // VALIDACIÓN
  if (!nombre || !correo || !rol || !password) {
    alert("Completa todos los campos, incluido el rol");
    return;
  }

  const payload = { nombre, correo, rol, password };

  try {
    const res = await fetch(`${API}/usuarios/registro`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok) {
      alert("Usuario creado con éxito");
      document.getElementById("nombre").value = "";
      document.getElementById("correo_admin").value = "";
      document.getElementById("rol").value = "";
      document.getElementById("contraseña_admin").value = "";
    } else {
      alert(data.detail || JSON.stringify(data));
    }
  } catch (err) {
    alert("Error de red: " + err.message);
  }
}

async function crearRequisicion(event) {
  const seccion = event.target.closest(".seccion");

  const select = seccion.querySelector(".tipo_equipo");
  const textarea = seccion.querySelector(".problema_descripcion");

  const tipo_equipo = select.value;
  const problema_descripcion = textarea.value;

  if (!tipo_equipo || !problema_descripcion) {
    alert("Completa todos los campos");
    return;
  }

  try {
    const res = await fetch(`${API}/requisiciones/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        tipo_equipo,
        problema_descripcion
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Error al crear requisición");
    }

    alert("✅ Requisición creada correctamente");

    // limpiar campos
    select.value = "";
    textarea.value = "";

    // recargar lista
    const perfilRes = await fetch(`${API}/usuarios/perfil`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });

    const user = await perfilRes.json();

    if (user.rol === "solicitante") {
      cargarMisRequisiciones();
    } else {
      cargarTodasRequisiciones(user);
    }

  } catch (err) {
    console.error("Error:", err);
    alert("Error al crear requisición");
  }
}

async function cargarMisRequisiciones() {
  const res = await fetch(`${API}/requisiciones/`, {
    headers: { "Authorization": `Bearer ${getToken()}` }
  });
  const data = await res.json();
  const container = document.getElementById("lista-mis-requisiciones");
  container.innerHTML = data.length === 0 ? "<p><em>No tienes requisiciones.</em></p>" : "";

  data.forEach(r => {
    const div = document.createElement("div");
    div.className = "req";

  // 🔍 Decisión del supervisor
    let decisionSupervisor = "⏳ Pendiente de revisión";
    if (r.aprobado_por_supervisor === "aprobado")
      decisionSupervisor = "✅ Aprobada por supervisor";
    if (r.aprobado_por_supervisor === "rechazado")
      decisionSupervisor = "❌ Rechazada por supervisor";

let motivoTexto = "";
if (r.aprobado_por_supervisor === "rechazado" && r.motivo_rechazo) {
  motivoTexto = `<small>📝 Motivo: <strong>${r.motivo_rechazo}</strong></small><br>`;
}

div.innerHTML = `
  <strong>${r.tipo_equipo}</strong><br>
  ${r.problema_descripcion}<br>
  <small>Estado: <strong>${r.estado}</strong></small><br>
  <small>Decisión: <strong>${decisionSupervisor}</strong></small><br>
  ${motivoTexto}
`;

  container.appendChild(div);
});
}

if (window.location.pathname.includes("dashboard")) {
  cargarDashboard();
}

async function cargarTodasRequisiciones(user) {
  try {
    const rol = user.rol
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();

    console.log("👤 Rol normalizado:", rol);

    // 🔥 Ahora incluimos supervisor también
    if (rol !== "admin" && rol !== "tecnico" && rol !== "supervisor") {
      console.warn("⛔ No autorizado:", rol);
      return;
    }

    const res = await fetch(`${API}/requisiciones/`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`
      }
    });

    if (!res.ok) throw new Error("Error API: " + res.status);

    let data = await res.json();

    todasLasRequisiciones = data;
    usuarioActual = user;


    console.log("📦 DATA DEL BACKEND:", data);

    if (rol === "tecnico") {
    data = data.filter(r => r.aprobado_por_supervisor === "aprobado");
    }

    const containerId =
      rol === "admin"
        ? "lista-admin"
        : rol === "tecnico"
        ? "lista-tecnico"
        : "lista-supervisor";

    const container = document.getElementById(containerId);

    if (!container) {
      console.error("❌ No existe el contenedor:", containerId);
      return;
    }

    container.innerHTML = "";

    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = "<p><em>No hay requisiciones.</em></p>";
      return;
    }

    data.forEach(r => renderRequisicion(r, rol, container));

  } catch (err) {
    console.error("💥 ERROR:", err);
  }
}

// Función para aprobar o rechazar requisición por supervisor
async function cambiarAprobacionSupervisor(id, decision) {
  let motivo = "";

  if (decision === "rechazado") {
    motivo = prompt("¿Cuál es el motivo del rechazo?");
    if (motivo === null) return; // canceló
    if (!motivo.trim()) {
      alert("Debes escribir un motivo de rechazo");
      return;
    }
  }

  try {
    const res = await fetch(`${API}/requisiciones/${id}/aprobacion`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`
      },
      body: JSON.stringify({
        aprobado_por_supervisor: decision,
        motivo_rechazo: motivo
      })
    });

    if (!res.ok) throw new Error("No se pudo actualizar la aprobación");

    alert(`✅ Requisición ${decision}`);

    const perfilRes = await fetch(`${API}/usuarios/perfil`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    const user = await perfilRes.json();
    cargarTodasRequisiciones(user);

  } catch (err) {
    console.error("❌ Error al actualizar aprobación:", err);
    alert("Error al actualizar la aprobación");
  }
}

// === CAMBIAR ESTADO (TECNICO) ===
async function cambiarEstado(reqId, nuevoEstado) {
  try {
    const res = await fetch(`${API}/requisiciones/${reqId}/estado`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`
      },
      body: JSON.stringify({ estado: nuevoEstado })
    });

    if (!res.ok) {
      throw new Error("No se pudo actualizar");
    }
    console.log("TOKEN ENVIADO:", getToken());
    
    console.log("✅ Estado actualizado");

    // 🔄 recargar lista
    const perfilRes = await fetch(`${API}/usuarios/perfil`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });

    const user = await perfilRes.json();
    cargarTodasRequisiciones(user);

  } catch (err) {
    console.error("❌ Error:", err);
    alert("Error al cambiar estado");
  }
}

async function cargarListaUsuarios() {
  const res = await fetch(`${API}/usuarios/lista`, {
    headers: { Authorization: `Bearer ${getToken()}` }
  });
  const data = await res.json();
  const container = document.getElementById("lista-usuarios");
  container.innerHTML = "";

  if (!data.length) {
    container.innerHTML = "<p><em>No hay usuarios.</em></p>";
    return;
  }

  data.forEach(u => {
    const div = document.createElement("div");
    div.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:8px; border-bottom:1px solid #ccc; flex-wrap:wrap; gap:5px;";
    div.innerHTML = `
      <span><strong>${u.nombre}</strong> — ${u.correo} (${u.rol})</span>
      <div style="display:flex; gap:5px;">
        <button onclick="resetearPassword('${u.id}', '${u.nombre}')" style="background:orange; color:white; border:none; padding:5px 10px; cursor:pointer;">
          Resetear
        </button>
      <button onclick="eliminarUsuario('${u.id}', '${u.nombre}')" style="background:red; color:white; border:none; padding:5px 10px; cursor:pointer;">
        Eliminar
      </button>
    </div>
  `;
    container.appendChild(div);
  });
}

async function eliminarUsuario(id, nombre) {
  if (!confirm("¿Seguro que deseas eliminar a este usuario?")) return;

  const res = await fetch(`${API}/usuarios/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${getToken()}` }
  });

  const data = await res.json();

  if (res.ok) {
    alert("✅ Usuario eliminado");
    cargarListaUsuarios();
  } else {
    alert("❌ " + (data.detail || "Error al eliminar"));
  }
}

function abrirModalUsuarios() {
  const modal = document.getElementById("modal-usuarios");
  modal.style.display = "flex";
  cargarListaUsuarios();
}

function cerrarModalUsuarios() {
  document.getElementById("modal-usuarios").style.display = "none";
}

// Cerrar al hacer click fuera del modal
document.getElementById("modal-usuarios").addEventListener("click", function(e) {
  if (e.target === this) cerrarModalUsuarios();
});

async function resetearPassword(id, nombre) {
  if (!confirm(`¿Resetear contraseña de ${nombre} a "0000"?`)) return;

  const res = await fetch(`${API}/usuarios/${id}/resetear-password`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${getToken()}` }
  });

  const data = await res.json();
  if (res.ok) {
    alert(`✅ Contraseña de ${nombre} reseteada a 0000`);
  } else {
    alert("❌ " + (data.detail || "Error al resetear"));
  }
}

async function cambiarMiPassword() {
  const password_actual = document.getElementById("password_actual").value;
  const password_nueva = document.getElementById("password_nueva").value;

  if (!password_actual || !password_nueva) {
    alert("Completa ambos campos");
    return;
  }

  const res = await fetch(`${API}/usuarios/mi-password`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`
    },
    body: JSON.stringify({ password_actual, password_nueva })
  });

  const data = await res.json();
  if (res.ok) {
    alert("✅ Contraseña actualizada");
    document.getElementById("password_actual").value = "";
    document.getElementById("password_nueva").value = "";
  } else {
    alert("❌ " + (data.detail || "Error al actualizar"));
  }
}

function aplicarFiltros() {
  console.log("filtros:", todasLasRequisiciones.length, usuarioActual?.rol);
  const seccionVisible = document.querySelector(".seccion[style*='block']");
  const texto = seccionVisible?.querySelector(".filtro-texto")?.value.toLowerCase() || "";
  const estado = seccionVisible?.querySelector(".filtro-estado")?.value || "";
  const equipo = seccionVisible?.querySelector(".filtro-equipo")?.value || "";

  const rol = usuarioActual.rol
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  let filtrados = todasLasRequisiciones;

  // Filtro base por rol
  if (rol === "tecnico") {
    filtrados = filtrados.filter(r => r.aprobado_por_supervisor === "aprobado");
  }

  // Filtros del usuario
  if (texto) {
    filtrados = filtrados.filter(r =>
      r.usuario_nombre?.toLowerCase().includes(texto) ||
      r.problema_descripcion?.toLowerCase().includes(texto)
    );
  }
  if (estado) {
    filtrados = filtrados.filter(r => r.estado === estado);
  }
  if (equipo) {
    filtrados = filtrados.filter(r => r.tipo_equipo === equipo);
    console.log("después filtro equipo:", filtrados.length, equipo);
  }

  // Re-renderizar con datos filtrados
  const containerId =
    rol === "admin" ? "lista-admin" :
    rol === "tecnico" ? "lista-tecnico" : "lista-supervisor";

  const container = document.getElementById(containerId);
  container.innerHTML = "";

  if (!filtrados.length) {
    container.innerHTML = "<p><em>No hay requisiciones que coincidan.</em></p>";
    return;
  }

  filtrados.forEach(r => renderRequisicion(r, rol, container));
}

function renderRequisicion(r, rol, container) {
  const div = document.createElement("div");
  div.className = "req";

  let estadoSupervisor = "⏳ Pendiente";
  if (r.aprobado_por_supervisor === "aprobado") estadoSupervisor = "✅ Aprobado";
  if (r.aprobado_por_supervisor === "rechazado") estadoSupervisor = "❌ Rechazado";

  if (rol === "supervisor") {
    div.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong>${r.tipo_equipo}</strong><br>
          ${r.problema_descripcion}<br>
          <small>👤 Solicitante: <strong>${r.usuario_nombre}</strong></small><br>
          <small>📅 Fecha: <strong>${r.fecha_solicitud ? new Date(r.fecha_solicitud).toLocaleString("es-CO") : "Sin fecha"}</strong></small><br>
          <small>Estado: ${r.estado}</small><br>
          <small>Decisión: ${estadoSupervisor}</small>
          ${r.motivo_rechazo ? `<small>📝 Motivo: <strong>${r.motivo_rechazo}</strong></small>` : ""}
        </div>
        <div style="display:flex; gap:5px;">
          <button onclick="cambiarAprobacionSupervisor('${r.id}', 'aprobado')">✅</button>
          <button onclick="cambiarAprobacionSupervisor('${r.id}', 'rechazado')">❌</button>
        </div>
      </div>
    `;
  } else {
    div.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong>${r.tipo_equipo}</strong><br>
          ${r.problema_descripcion}<br>
          <small>👤 Solicitante: <strong>${r.usuario_nombre}</strong></small><br>
          <small>📅 Fecha: <strong>${r.fecha_solicitud ? new Date(r.fecha_solicitud).toLocaleString("es-CO") : "Sin fecha"}</strong></small><br>
          <small>Estado:</small>
          <select class="estado-select" disabled>
            <option value="pendiente" ${r.estado === "pendiente" ? "selected" : ""}>Pendiente</option>
            <option value="en_proceso" ${r.estado === "en_proceso" ? "selected" : ""}>En Proceso</option>
            <option value="completada" ${r.estado === "completada" ? "selected" : ""}>Completada</option>
          </select><br>
          <small>Decisión Supervisor: ${estadoSupervisor}</small>
          ${r.motivo_rechazo ? `<small>📝 Motivo: <strong>${r.motivo_rechazo}</strong></small>` : ""}
        </div>
        <div>
          ${r.estado === "completada"
            ? `<span style="color:green; font-weight:bold;">✅ Completada</span>`
            : `<button class="editar-btn" ${r.aprobado_por_supervisor === "rechazado" && rol !== "admin" ? "disabled title='Rechazada por supervisor'" : ""}>Editar</button>
               <button class="guardar-btn" disabled>Guardar</button>`
          }
        </div>
      </div>
    `;

    const editarBtn = div.querySelector(".editar-btn");
    const guardarBtn = div.querySelector(".guardar-btn");
    const estadoSelect = div.querySelector(".estado-select");

    if (editarBtn) {
      editarBtn.addEventListener("click", () => {
        estadoSelect.disabled = false;
        guardarBtn.disabled = false;
        editarBtn.disabled = true;
      });

      guardarBtn.addEventListener("click", async () => {
        const nuevoEstado = estadoSelect.value;
        try {
          const res = await fetch(`${API}/requisiciones/${r.id}/estado`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ estado: nuevoEstado })
          });

          if (!res.ok) throw new Error("No se pudo actualizar");
          alert("✅ Estado actualizado");
          estadoSelect.disabled = true;
          guardarBtn.disabled = true;
          editarBtn.disabled = false;
        } catch (err) {
          console.error(err);
          alert("❌ Error al actualizar estado");
        }
      });
    }
  }

  container.appendChild(div);
}