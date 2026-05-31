// Cliente del backend SmartStock. Usa el proxy /api → http://localhost:8080.

export interface Bodega {
  codigo: string;
  nombre: string;
  ubicacion: string;
}

export interface Medicamento {
  id: string;
  sku: string;
  nombre: string;
  categoria: string;
  stockMinimo: number;
  stockTotal: number;
  numLotes: number;
  bajoStock: boolean;
}

export interface Lote {
  id: string;
  medicamentoId: string;
  numeroLote: string;
  bodegaCodigo: string;
  fechaCaducidad: string; // ISO YYYY-MM-DD
  stockActual: number;
}

export interface MedEnRiesgo {
  sku: string;
  nombre: string;
  categoria: string;
  stockTotal: number;
  stockMinimo: number;
}

export interface Reporte {
  totalMedicamentos: number;
  totalLotes: number;
  totalUnidades: number;
  unidadesPorCategoria: Record<string, number>;
  unidadesPorBodega: Record<string, number>;
  medicamentosEnRiesgo: MedEnRiesgo[];
  lotesProximosACaducar: Lote[];
  lotesCaducados: Lote[];
}

export interface ResultadoMovimiento {
  movimientoId: string;
  lote: Lote;
  stockTotalMedicamento: number;
  bajoStock: boolean;
}

export interface RespuestaAsistente {
  respuesta: string;
  fuentes: string[];
  modo: string;
}

function aMedicamento(m: any): Medicamento {
  return {
    id: m.id, sku: m.sku, nombre: m.nombre, categoria: m.categoria,
    stockMinimo: m.stock_minimo, stockTotal: m.stock_total,
    numLotes: m.num_lotes, bajoStock: m.bajo_stock,
  };
}

function aLote(l: any): Lote {
  return {
    id: l.id, medicamentoId: l.medicamento_id, numeroLote: l.numero_lote,
    bodegaCodigo: l.bodega_codigo, fechaCaducidad: l.fecha_caducidad,
    stockActual: l.stock_actual,
  };
}

// --- Token de sesión ---
const TOKEN_KEY = "smartstock_token";
let token: string | null = localStorage.getItem(TOKEN_KEY);
let onUnauthorized: (() => void) | null = null;

export function setOnUnauthorized(cb: () => void) {
  onUnauthorized = cb;
}

function setToken(t: string | null) {
  token = t;
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`/api${url}`, {
    ...init,
    headers: { ...headers, ...(init?.headers as Record<string, string>) },
  });
  if (res.status === 401) {
    setToken(null);
    if (onUnauthorized) onUnauthorized();
    throw new Error("Sesión expirada o no autenticado.");
  }
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => ({}));
    throw new Error(cuerpo.detail ?? `Error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  estaAutenticado(): boolean {
    return token !== null;
  },

  async login(username: string, password: string): Promise<void> {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const cuerpo = await res.json().catch(() => ({}));
      throw new Error(cuerpo.detail ?? "No se pudo iniciar sesión.");
    }
    const data = await res.json();
    setToken(data.access_token);
  },

  logout(): void {
    setToken(null);
  },

  async listarBodegas(): Promise<Bodega[]> {
    const d = await pedir<any[]>("/warehouses");
    return d.map((b) => ({ codigo: b.codigo, nombre: b.nombre, ubicacion: b.ubicacion }));
  },

  async listarMedicamentos(): Promise<Medicamento[]> {
    return (await pedir<any[]>("/medications")).map(aMedicamento);
  },

  async crearMedicamento(body: {
    sku: string; nombre: string; categoria: string; stockMinimo: number;
  }): Promise<Medicamento> {
    return aMedicamento(await pedir<any>("/medications", {
      method: "POST",
      body: JSON.stringify({
        sku: body.sku, nombre: body.nombre,
        categoria: body.categoria, stock_minimo: body.stockMinimo,
      }),
    }));
  },

  async listarLotes(bodega?: string): Promise<Lote[]> {
    const q = bodega ? `?bodega=${encodeURIComponent(bodega)}` : "";
    return (await pedir<any[]>(`/lots${q}`)).map(aLote);
  },

  async registrarEntrada(body: {
    medicamentoId: string; numeroLote: string; bodegaCodigo: string;
    fechaCaducidad: string; cantidad: number;
  }): Promise<ResultadoMovimiento> {
    const d = await pedir<any>("/inventory/entries", {
      method: "POST",
      body: JSON.stringify({
        medicamento_id: body.medicamentoId, numero_lote: body.numeroLote,
        bodega_codigo: body.bodegaCodigo, fecha_caducidad: body.fechaCaducidad,
        cantidad: body.cantidad,
      }),
    });
    return { movimientoId: d.movimiento_id, lote: aLote(d.lote), stockTotalMedicamento: d.stock_total_medicamento, bajoStock: d.bajo_stock };
  },

  async registrarSalida(body: { loteId: string; cantidad: number }): Promise<ResultadoMovimiento> {
    const d = await pedir<any>("/inventory/exits", {
      method: "POST",
      body: JSON.stringify({ lote_id: body.loteId, cantidad: body.cantidad }),
    });
    return { movimientoId: d.movimiento_id, lote: aLote(d.lote), stockTotalMedicamento: d.stock_total_medicamento, bajoStock: d.bajo_stock };
  },

  async alertasRestock(): Promise<Medicamento[]> {
    return (await pedir<any[]>("/alerts/restock")).map(aMedicamento);
  },

  async alertasCaducidad(): Promise<Lote[]> {
    return (await pedir<any[]>("/alerts/expiring")).map(aLote);
  },

  async reporte(): Promise<Reporte> {
    const r = await pedir<any>("/reports/inventory");
    return {
      totalMedicamentos: r.total_medicamentos,
      totalLotes: r.total_lotes,
      totalUnidades: r.total_unidades,
      unidadesPorCategoria: r.unidades_por_categoria,
      unidadesPorBodega: r.unidades_por_bodega,
      medicamentosEnRiesgo: (r.medicamentos_en_riesgo ?? []).map((x: any) => ({
        sku: x.sku, nombre: x.nombre, categoria: x.categoria,
        stockTotal: x.stock_total, stockMinimo: x.stock_minimo,
      })),
      lotesProximosACaducar: (r.lotes_proximos_a_caducar ?? []).map(aLote),
      lotesCaducados: (r.lotes_caducados ?? []).map(aLote),
    };
  },

  async preguntarAsistente(pregunta: string): Promise<RespuestaAsistente> {
    const r = await pedir<any>("/assistant/query", {
      method: "POST",
      body: JSON.stringify({ pregunta }),
    });
    return { respuesta: r.respuesta, fuentes: r.fuentes ?? [], modo: r.modo };
  },
};
