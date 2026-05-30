import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import {
  api,
  type Medicamento,
  type Reporte,
  type TipoMovimiento,
} from "../lib/api";

export default function App() {
  const [medicamentos, setMedicamentos] = useState<Medicamento[]>([]);
  const [alertas, setAlertas] = useState<Medicamento[]>([]);
  const [porCaducar, setPorCaducar] = useState<Medicamento[]>([]);
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function refrescar() {
    setCargando(true);
    setError(null);
    try {
      const [m, a, c, r] = await Promise.all([
        api.listarMedicamentos(),
        api.alertasRestock(),
        api.alertasCaducidad(),
        api.reporte(),
      ]);
      setMedicamentos(m);
      setAlertas(a);
      setPorCaducar(c);
      setReporte(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    refrescar();
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <header className="bg-slate-900 text-white px-6 py-4 shadow">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold">💊 SmartStock AI — Medicamentos</h1>
          <button
            onClick={refrescar}
            className="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded"
          >
            {cargando ? "Actualizando…" : "Refrescar"}
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        {error && (
          <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-2 rounded">
            {error}
          </div>
        )}

        {reporte && <PanelReporte reporte={reporte} />}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <TablaMedicamentos medicamentos={medicamentos} />
            <FormularioMovimiento medicamentos={medicamentos} onHecho={refrescar} />
          </div>
          <div className="space-y-6">
            <PanelAlertas titulo="Reabastecimiento" items={alertas} tipo="stock" />
            <PanelAlertas titulo="Próximos a caducar" items={porCaducar} tipo="caducidad" />
            <Asistente />
          </div>
        </div>
      </main>
    </div>
  );
}

function Tarjeta({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <section className="bg-white rounded-lg shadow p-4">
      <h2 className="font-semibold text-slate-700 mb-3">{titulo}</h2>
      {children}
    </section>
  );
}

function PanelReporte({ reporte }: { reporte: Reporte }) {
  const cats = Object.entries(reporte.unidadesPorCategoria);
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Metrica titulo="Medicamentos" valor={`${reporte.totalMedicamentos}`} />
      <Metrica titulo="Unidades" valor={`${reporte.totalUnidades}`} />
      <Metrica
        titulo="En riesgo"
        valor={`${reporte.medicamentosEnRiesgo.length}`}
        alerta={reporte.medicamentosEnRiesgo.length > 0}
      />
      <Metrica
        titulo="Caducados"
        valor={`${reporte.caducados.length}`}
        alerta={reporte.caducados.length > 0}
      />
      {cats.length > 0 && (
        <div className="col-span-2 md:col-span-4 bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-slate-600 mb-2">
            Unidades por categoría
          </h3>
          <div className="flex flex-wrap gap-2">
            {cats.map(([c, v]) => (
              <span
                key={c}
                className="text-sm bg-slate-100 px-3 py-1 rounded-full"
              >
                {c}: <strong>{v}</strong>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Metrica({
  titulo,
  valor,
  alerta,
}: {
  titulo: string;
  valor: string;
  alerta?: boolean;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="text-xs uppercase text-slate-500">{titulo}</div>
      <div
        className={`text-2xl font-bold ${alerta ? "text-red-600" : "text-slate-800"}`}
      >
        {valor}
      </div>
    </div>
  );
}

function diasRestantes(fechaISO: string): number {
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const f = new Date(fechaISO + "T00:00:00");
  return Math.round((f.getTime() - hoy.getTime()) / 86400000);
}

function EstadoCaducidad({ fechaISO }: { fechaISO: string }) {
  const d = diasRestantes(fechaISO);
  if (d < 0)
    return (
      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
        Caducado
      </span>
    );
  if (d <= 30)
    return (
      <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
        Caduca en {d}d
      </span>
    );
  return <span className="text-xs text-slate-400">{fechaISO}</span>;
}

function TablaMedicamentos({ medicamentos }: { medicamentos: Medicamento[] }) {
  return (
    <Tarjeta titulo="Medicamentos">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2">SKU</th>
              <th>Nombre</th>
              <th>Categoría</th>
              <th>Caducidad</th>
              <th className="text-right">Stock</th>
              <th className="text-right">Mín.</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {medicamentos.map((m) => (
              <tr key={m.id} className="border-b last:border-0">
                <td className="py-2 font-mono text-xs">{m.sku}</td>
                <td>{m.nombre}</td>
                <td>{m.categoria}</td>
                <td>
                  <EstadoCaducidad fechaISO={m.fechaCaducidad} />
                </td>
                <td className="text-right font-semibold">{m.stockActual}</td>
                <td className="text-right text-slate-400">{m.stockMinimo}</td>
                <td>
                  {m.bajoStock ? (
                    <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                      Bajo stock
                    </span>
                  ) : (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                      OK
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {medicamentos.length === 0 && (
              <tr>
                <td colSpan={7} className="py-4 text-center text-slate-400">
                  Sin medicamentos
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Tarjeta>
  );
}

function FormularioMovimiento({
  medicamentos,
  onHecho,
}: {
  medicamentos: Medicamento[];
  onHecho: () => void;
}) {
  const [medicamentoId, setMedicamentoId] = useState("");
  const [tipo, setTipo] = useState<TipoMovimiento>("salida");
  const [cantidad, setCantidad] = useState(1);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setErr(null);
    try {
      const r = await api.registrarMovimiento({ medicamentoId, tipo, cantidad });
      setMsg(
        `${tipo === "salida" ? "Salida" : "Entrada"} registrada. Stock: ${
          r.medicamento.stockActual
        }${r.bajoStock ? " ⚠️ ¡bajo stock!" : ""}`
      );
      onHecho();
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  return (
    <Tarjeta titulo="Registrar movimiento">
      <form onSubmit={enviar} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <select
          value={medicamentoId}
          onChange={(e) => setMedicamentoId(e.target.value)}
          required
          className="border rounded px-2 py-1.5 sm:col-span-2"
        >
          <option value="">Selecciona medicamento…</option>
          {medicamentos.map((m) => (
            <option key={m.id} value={m.id}>
              {m.sku} — {m.nombre} (stock {m.stockActual})
            </option>
          ))}
        </select>
        <select
          value={tipo}
          onChange={(e) => setTipo(e.target.value as TipoMovimiento)}
          className="border rounded px-2 py-1.5"
        >
          <option value="salida">Salida</option>
          <option value="entrada">Entrada</option>
        </select>
        <input
          type="number"
          min={1}
          value={cantidad}
          onChange={(e) => setCantidad(Number(e.target.value))}
          className="border rounded px-2 py-1.5"
        />
        <button
          type="submit"
          className="sm:col-span-4 bg-slate-900 hover:bg-slate-700 text-white rounded py-2"
        >
          Registrar
        </button>
      </form>
      {msg && <p className="mt-2 text-sm text-green-700">{msg}</p>}
      {err && <p className="mt-2 text-sm text-red-600">{err}</p>}
    </Tarjeta>
  );
}

function PanelAlertas({
  titulo,
  items,
  tipo,
}: {
  titulo: string;
  items: Medicamento[];
  tipo: "stock" | "caducidad";
}) {
  const colores =
    tipo === "stock"
      ? "bg-red-50 border-red-200 text-red-600"
      : "bg-amber-50 border-amber-200 text-amber-600";
  return (
    <Tarjeta titulo={`${titulo} (${items.length})`}>
      {items.length === 0 ? (
        <p className="text-sm text-slate-400">Sin alertas 🎉</p>
      ) : (
        <ul className="space-y-2">
          {items.map((m) => (
            <li
              key={m.id}
              className={`flex justify-between items-center border rounded px-3 py-2 ${colores.split(" text-")[0]}`}
            >
              <div>
                <div className="font-medium text-sm text-slate-800">{m.nombre}</div>
                <div className="text-xs text-slate-500 font-mono">{m.sku}</div>
              </div>
              <div className="text-right text-xs">
                {tipo === "stock" ? (
                  <>
                    <div className="text-red-600 font-bold">{m.stockActual}</div>
                    <div className="text-slate-400">mín {m.stockMinimo}</div>
                  </>
                ) : (
                  <div className="text-amber-600 font-bold">
                    {diasRestantes(m.fechaCaducidad)}d
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}

function Asistente() {
  const [pregunta, setPregunta] = useState("");
  const [respuesta, setRespuesta] = useState<string | null>(null);
  const [fuentes, setFuentes] = useState<string[]>([]);
  const [cargando, setCargando] = useState(false);

  async function preguntar(e: FormEvent) {
    e.preventDefault();
    setCargando(true);
    setRespuesta(null);
    try {
      const r = await api.preguntarAsistente(pregunta);
      setRespuesta(r.respuesta);
      setFuentes(r.fuentes);
    } catch (e) {
      setRespuesta(`Error: ${(e as Error).message}`);
    } finally {
      setCargando(false);
    }
  }

  return (
    <Tarjeta titulo="🤖 Asistente">
      <form onSubmit={preguntar} className="space-y-2">
        <textarea
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder="¿Qué medicamentos debería reabastecer o están por caducar?"
          className="w-full border rounded px-2 py-1.5 text-sm h-20"
        />
        <button
          type="submit"
          disabled={cargando || !pregunta}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded py-2 text-sm"
        >
          {cargando ? "Pensando…" : "Preguntar"}
        </button>
      </form>
      {respuesta && (
        <div className="mt-3 text-sm">
          <p className="whitespace-pre-wrap">{respuesta}</p>
          {fuentes.length > 0 && (
            <div className="mt-2 text-xs text-slate-500">
              Fuentes: {fuentes.join(", ")}
            </div>
          )}
        </div>
      )}
    </Tarjeta>
  );
}
