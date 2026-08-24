/**
 * PWA - Gestor de Rutas para Conductores
 * App.js - Lógica principal
 */

const API_BASE = `${window.location.origin}/api`;
let conductorActual = null;
let rutaActual = null;
let paradasActuales = [];

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚌 PWA Cargada');
    
    // Registrar service worker
    if ('serviceWorker' in navigator) {
        try {
            const reg = await navigator.serviceWorker.register('sw.js');
            console.log('✓ Service Worker registrado');
        } catch (e) {
            console.warn('Service Worker no disponible:', e);
        }
    }
    
    // Cargar conductores
    await cargarConductores();
    
    // Verificar conexión
    verificarConexion();
    setInterval(verificarConexion, 5000);
});

// ============================================================================
// CONDUCTORES
// ============================================================================

async function cargarConductores() {
    try {
        const response = await fetch(`${API_BASE}/conductores`);
        if (!response.ok) throw new Error('Error al cargar conductores');
        
        const data = await response.json();
        const select = document.getElementById('conductorSelect');
        
        select.innerHTML = '<option value="">Selecciona Conductor...</option>';
        
        data.conductores.forEach(conductor => {
            const option = document.createElement('option');
            option.value = conductor.id;
            option.textContent = `${conductor.nombre} (${conductor.Plazas_Vehiculo} plazas)`;
            select.appendChild(option);
        });

        if (data.conductores.length > 0) {
            const primerConductor = data.conductores[0];
            select.value = String(primerConductor.id);
            await cambiarConductor();
            return;
        }
        
        mostrarToast('✓ Conductores cargados', 'success');
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error al cargar conductores', 'error');
    }
}

async function cambiarConductor() {
    const select = document.getElementById('conductorSelect');
    const conductorId = select.value;
    
    if (!conductorId) {
        mostrarPantalla('selectScreen');
        conductorActual = null;
        return;
    }
    
    const conductorName = select.options[select.selectedIndex].text.split(' (')[0];
    conductorActual = { id: conductorId, nombre: conductorName };
    
    document.getElementById('conductorInfo').textContent = conductorName;
    
    await cargarRutas();
    mostrarPantalla('rutasScreen');
}

// ============================================================================
// RUTAS
// ============================================================================

async function cargarRutas() {
    if (!conductorActual) return;
    
    try {
        const response = await fetch(`${API_BASE}/conductor/${conductorActual.id}/rutas`);
        if (!response.ok) throw new Error('Error al cargar rutas');
        
        const data = await response.json();
        const lista = document.getElementById('rutasList');
        
        if (data.rutas.length === 0) {
            lista.innerHTML = '<div class="empty-state"><div class="icon">🚫</div><p>No hay rutas asignadas</p></div>';
            return;
        }
        
        lista.innerHTML = data.rutas.map(ruta => `
            <div class="ruta-card ${ruta.estado}" onclick="abrirDetalleRuta(${ruta.id})">
                <div class="ruta-header-card">
                    <span class="ruta-numero">Ruta #${ruta.grupo_numero}</span>
                    <span class="estado-badge ${ruta.estado}">${formatearEstado(ruta.estado)}</span>
                </div>
                <div class="ruta-meta">
                    <div class="ruta-meta-item">🕒 ${formatearHora(ruta.hora_inicio)}</div>
                    <div class="ruta-meta-item">👥 ${ruta.total_personas} pax</div>
                    <div class="ruta-meta-item">📍 ${ruta.total_paradas} paradas</div>
                    <div class="ruta-meta-item">✓ ${ruta.confirmados}/${ruta.total_paradas}</div>
                </div>
                <div class="ruta-progress">
                    <div class="ruta-progress-bar" style="width: ${ruta.total_paradas > 0 ? (ruta.confirmados / ruta.total_paradas * 100) : 0}%"></div>
                </div>
            </div>
        `).join('');
        
        mostrarToast('✓ Rutas actualizadas', 'success');
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error al cargar rutas', 'error');
    }
}

async function abrirDetalleRuta(rutaId) {
    rutaActual = rutaId;
    
    try {
        // Cargar paradas
        const response = await fetch(`${API_BASE}/ruta/${rutaId}/paradas`);
        if (!response.ok) throw new Error('Error al cargar paradas');
        
        const data = await response.json();
        paradasActuales = data.paradas;
        
        // Encontrar datos de la ruta
        const rutasResponse = await fetch(`${API_BASE}/conductor/${conductorActual.id}/rutas`);
        const rutasData = await rutasResponse.json();
        const ruta = rutasData.rutas.find(r => r.id === rutaId);
        
        if (!ruta) return;
        
        // Actualizar UI
        document.getElementById('rutaTitulo').textContent = `Ruta #${ruta.grupo_numero}`;
        document.getElementById('rutaEstado').textContent = formatearEstado(ruta.estado);
        document.getElementById('rutaEstado').className = `estado-badge ${ruta.estado}`;
        document.getElementById('rutaHoraInicio').textContent = formatearHora(ruta.hora_inicio);
        document.getElementById('rutaHoraFin').textContent = formatearHora(ruta.hora_fin);
        document.getElementById('rutaPersonas').textContent = ruta.total_personas;
        document.getElementById('rutaParadas').textContent = ruta.total_paradas;
        document.getElementById('rutaFechaInicioReal').textContent = formatearFechaHora(ruta.fecha_inicio_real);
        document.getElementById('rutaFechaFinReal').textContent = formatearFechaHora(ruta.fecha_fin_real);
        document.getElementById('rutaObservaciones').textContent = ruta.observaciones || 'Sin observaciones';
        
        // Actualizar botones
        const btnIniciar = document.getElementById('btnIniciarRuta');
        const btnFinalizar = document.getElementById('btnFinalizarRuta');
        
        if (ruta.estado === 'programada') {
            btnIniciar.style.display = 'block';
            btnFinalizar.style.display = 'none';
        } else if (ruta.estado === 'en_curso') {
            btnIniciar.style.display = 'none';
            btnFinalizar.style.display = 'block';
        } else {
            btnIniciar.style.display = 'none';
            btnFinalizar.style.display = 'none';
        }
        
        // Cargar paradas
        const paradasList = document.getElementById('paradasList');
        paradasList.innerHTML = paradasActuales.map((parada, idx) => `
            <div class="parada-item ${parada.confirmado ? 'confirmada' : ''}">
                <div class="parada-header">
                    <div>
                        <span class="parada-numero">${parada.orden}</span>
                        <span class="parada-lugar">${parada.establecimiento}</span>
                    </div>
                    ${parada.confirmado ? '<span class="check-icon">✓</span>' : ''}
                </div>
                <div class="parada-hora">${parada.lugar_recogida || 'Sin especificar'}</div>
                <div class="parada-detalles">
                    <div class="parada-detalle-item">🕒 ${parada.hora}</div>
                    <div class="parada-detalle-item">👥 ${parada.personas}p</div>
                    <div class="parada-detalle-item">👨‍👩‍👧 ${parada.adultos}A ${parada.ninos}N</div>
                </div>
                ${!parada.confirmado ? `
                    <button class="btn-confirmar" onclick="confirmarParada(${parada.id})">
                        ✓ Confirmar Recogida
                    </button>
                ` : ''}
            </div>
        `).join('');
        
        mostrarPantalla('detalleRutaScreen');
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error al cargar ruta', 'error');
    }
}

async function iniciarRuta() {
    if (!rutaActual) return;
    
    if (!confirm('¿Iniciar esta ruta?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/ruta/${rutaActual}/iniciar`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Error al iniciar ruta');
        
        const data = await response.json();
        mostrarToast('✓ Ruta iniciada', 'success');
        
        // Actualizar
        await cargarRutas();
        await abrirDetalleRuta(rutaActual);
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error al iniciar ruta', 'error');
    }
}

async function finalizarRuta() {
    if (!rutaActual) return;
    
    if (!confirm('¿Finalizar esta ruta?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/ruta/${rutaActual}/finalizar`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Error al finalizar ruta');
        
        const data = await response.json();
        mostrarToast('✓ Ruta finalizada', 'success');
        
        // Actualizar
        await cargarRutas();
        await abrirDetalleRuta(rutaActual);
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error al finalizar ruta', 'error');
    }
}

async function confirmarParada(paradaId) {
    if (!rutaActual) return;
    
    try {
        const response = await fetch(`${API_BASE}/parada/${rutaActual}/${paradaId}/confirmar`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Error al confirmar parada');
        
        mostrarToast('✓ Parada confirmada', 'success');
        
        // Actualizar
        await abrirDetalleRuta(rutaActual);
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error al confirmar parada', 'error');
    }
}

// ============================================================================
// NAVEGACIÓN
// ============================================================================

function volverArutas() {
    mostrarPantalla('rutasScreen');
}

function mostrarPantalla(pantalla) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(pantalla).classList.add('active');
}

// ============================================================================
// UTILIDADES
// ============================================================================

function formatearHora(hora) {
    if (!hora) return '--:--';
    try {
        const date = new Date(hora);
        return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    } catch {
        return hora.substring(11, 16);
    }
}

function formatearFechaHora(fechaHora) {
    if (!fechaHora) return '--';
    try {
        const date = new Date(fechaHora.replace(' ', 'T'));
        if (Number.isNaN(date.getTime())) throw new Error('Fecha inválida');
        return date.toLocaleString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return fechaHora.includes(' ') ? fechaHora.replace(' ', ' · ') : fechaHora;
    }
}

function formatearEstado(estado) {
    const estados = {
        'programada': 'Programada',
        'en_curso': 'En Curso',
        'completada': 'Completada'
    };
    return estados[estado] || estado;
}

function mostrarToast(mensaje, tipo = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast show ${tipo}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

async function verificarConexion() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        const indicator = document.getElementById('syncIndicator');
        const text = document.getElementById('syncText');
        
        if (data.status === 'ok') {
            indicator.classList.remove('offline');
            text.textContent = 'Conectado';
        } else {
            indicator.classList.add('offline');
            text.textContent = 'Desconectado';
        }
    } catch (error) {
        document.getElementById('syncIndicator').classList.add('offline');
        document.getElementById('syncText').textContent = 'Sin conexión';
    }
}

// ============================================================================
// SERVICE WORKER (Offline support)
// ============================================================================

// Se cargará desde sw.js si existe
