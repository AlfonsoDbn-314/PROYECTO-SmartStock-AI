// Cliente del backend SmartStock. Usa el proxy /api → http://localhost:8080.

export interface Medicamento {
  id: string;
  sku: string;
  nombre: string;
  categoria: string;
  fechaCaducidad: string; // ISO YYYY-MM-DD
  stockActual: number;
  stockMinimo: number;
  bajoStock: boolean;
}

export interface Reporte {
  totalMedicamentos: number;
  totalUnidades: number;
  unidadesPorCategoria: Record<string, number>;
  medicamentosEnRiesgo: Medicamento[];
  proximosACaducar: Medicamento[];
  caducados: Medicamento[];
}

export type TipoMovimiento = "entrada" | "salida";

export interface ResultadoMovimiento {
  movimientoId: string;
  medicamento: Medicamento;
  bajoStock: boolean;
}

export interface RespuestaAsistente {
  respuesta: string;
  fuentes: string[];
  modo: string;
}

// --- Mapeo snake_case (API) → camelCase (TS) ---

function aMedicamento(m: any): Medicamento {
  return {
    id: m.id,
    sku: m.sku,
    nombre: m.nombre,
    categoria: m.categoria,
    fechaCaducidad: m.fecha_caducidad,
    stockActual: m.stock_actual,
    stockMinimo: m.stock_minimo,
    bajoStock: m.bajo_stock,
  };
}

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${url}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => ({}));
    throw new Error(cuerpo.detail ?? `Error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async health(): Promise<{ status: string }> {
    return pedir("/health");
  },

  async listarMedicamentos(): Promise<Medicamento[]> {
    const data = await pedir<any[]>("/medications");
    return data.map(aMedicamento);
  },

  async crearMedicamento(body: {
    sku: string;
    nombre: string;
    categoria: string;
    fechaCaducidad: string;
    stockInicial: number;
    stockMinimo: number;
  }): Promise<Medicamento> {
    const data = await pedir<any>("/medications", {
      method: "POST",
      body: JSON.stringify({
        sku: body.sku,
        nombre: body.nombre,
        categoria: body.categoria,
        fecha_caducidad: body.fechaCaducidad,
        stock_inicial: body.stockInicial,
        stock_minimo: body.stockMinimo,
      }),
    });
    return aMedicamento(data);
  },

  async registrarMovimiento(body: {
    medicamentoId: string;
    tipo: TipoMovimiento;
    cantidad: number;
    motivo?: string;
  }): Promise<ResultadoMovimiento> {
    const data = await pedir<any>("/inventory/movements", {
      method: "POST",
      body: JSON.stringify({
        medicamento_id: body.medicamentoId,
        tipo: body.tipo,
        cantidad: body.cantidad,
        motivo: body.motivo ?? null,
      }),
    });
    return {
      movimientoId: data.movimiento_id,
      medicamento: aMedicamento(data.medicamento),
      bajoStock: data.bajo_stock,
    };
  },

  async alertasRestock(): Promise<Medicamento[]> {
    const data = await pedir<any[]>("/alerts/restock");
    return data.map(aMedicamento);
  },

  async alertasCaducidad(): Promise<Medicamento[]> {
    const data = await pedir<any[]>("/alerts/expiring");
    return data.map(aMedicamento);
  },

  async reporte(): Promise<Reporte> {
    const r = await pedir<any>("/reports/inventory");
    return {
      totalMedicamentos: r.total_medicamentos,
      totalUnidades: r.total_unidades,
      unidadesPorCategoria: r.unidades_por_categoria,
      medicamentosEnRiesgo: (r.medicamentos_en_riesgo ?? []).map(aMedicamento),
      proximosACaducar: (r.proximos_a_caducar ?? []).map(aMedicamento),
      caducados: (r.caducados ?? []).map(aMedicamento),
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
