import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import {
  api,
  setOnUnauthorized,
  type Bodega,
  type Lote,
  type Medicamento,
  type Reporte,
} from "../lib/api";

export default function App() {
  const [autenticado, setAutenticado] = useState(api.estaAutenticado());

  useEffect(() => {
    setOnUnauthorized(() => setAutenticado(false));
  }, []);

  if (!autenticado) {
    return <Login onLogin={() => setAutenticado(true)} />;
  }
  return <Dashboard onLogout={() => { api.logout(); setAutenticado(false); }} />;
}

function Login({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.login(username, password);
      onLogin();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <form onSubmit={enviar} className="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm space-y-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-800">💊 SmartStock AI</h1>
          <p className="text-sm text-slate-500">Inventario de farmacia</p>
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Usuario</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required
            className="w-full border rounded px-3 py-2" autoFocus />
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Contraseña</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
            className="w-full border rounded px-3 py-2" />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={cargando}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded py-2">
          {cargando ? "Entrando…" : "Iniciar sesión"}
        </button>
        <p className="text-xs text-slate-400 text-center">Demo: admin / admin123</p>
      </form>
    </div>
  );
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [bodegas, setBodegas] = useState<Bodega[]>([]);
  const [medicamentos, setMedicamentos] = useState<Medicamento[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [alertas, setAlertas] = useState<Medicamento[]>([]);
  const [porCaducar, setPorCaducar] = useState<Lote[]>([]);
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [filtroBodega, setFiltroBodega] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function refrescar() {
    setCargando(true);
    setError(null);
    try {
      const [b, m, l, a, c, r] = await Promise.all([
        api.listarBodegas(),
        api.listarMedicamentos(),
        api.listarLotes(),
        api.alertasRestock(),
        api.alertasCaducidad(),
        api.reporte(),
      ]);
      setBodegas(b);
      setMedicamentos(m);
      setLotes(l);
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

  const nombreMed = useMemo(() => {
    const m = new Map(medicamentos.map((x) => [x.id, x]));
    return (id: string) => m.get(id);
  }, [medicamentos]);

  const lotesFiltrados = filtroBodega
    ? lotes.filter((l) => l.bodegaCodigo === filtroBodega)
    : lotes;

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <header className="bg-slate-900 text-white px-6 py-4 shadow">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold">💊 SmartStock AI — Inventario de Farmacia</h1>
          <div className="flex items-center gap-2">
            <button
              onClick={refrescar}
              className="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded"
            >
              {cargando ? "Actualizando…" : "Refrescar"}
            </button>
            <button
              onClick={onLogout}
              className="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded"
            >
              Salir
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {error && (
          <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-2 rounded">
            {error}
          </div>
        )}

        {reporte && <PanelReporte reporte={reporte} />}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <TablaMedicamentos medicamentos={medicamentos} />
            <TablaLotes
              lotes={lotesFiltrados}
              bodegas={bodegas}
              filtro={filtroBodega}
              setFiltro={setFiltroBodega}
              nombreMed={nombreMed}
            />
            <Formularios
              medicamentos={medicamentos}
              bodegas={bodegas}
              lotes={lotes}
              onHecho={refrescar}
            />
          </div>
          <div className="space-y-6">
            <PanelRestock alertas={alertas} />
            <PanelCaducidad lotes={porCaducar} nombreMed={nombreMed} />
            <Asistente />
          </div>
        </div>
      </main>
    </div>
  );
}

function Tarjeta({ titulo, extra, children }: { titulo: string; extra?: ReactNode; children: ReactNode }) {
  return (
    <section className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-slate-700">{titulo}</h2>
        {extra}
      </div>
      {children}
    </section>
  );
}

function Metrica({ titulo, valor, alerta }: { titulo: string; valor: string; alerta?: boolean }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="text-xs uppercase text-slate-500">{titulo}</div>
      <div className={`text-2xl font-bold ${alerta ? "text-red-600" : "text-slate-800"}`}>{valor}</div>
    </div>
  );
}

function PanelReporte({ reporte }: { reporte: Reporte }) {
  const bodegas = Object.entries(reporte.unidadesPorBodega);
  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
      <Metrica titulo="Medicamentos" valor={`${reporte.totalMedicamentos}`} />
      <Metrica titulo="Lotes" valor={`${reporte.totalLotes}`} />
      <Metrica titulo="Unidades" valor={`${reporte.totalUnidades}`} />
      <Metrica titulo="En riesgo" valor={`${reporte.medicamentosEnRiesgo.length}`} alerta={reporte.medicamentosEnRiesgo.length > 0} />
      <Metrica titulo="Por caducar" valor={`${reporte.lotesProximosACaducar.length}`} alerta={reporte.lotesProximosACaducar.length > 0} />
      <Metrica titulo="Caducados" valor={`${reporte.lotesCaducados.length}`} alerta={reporte.lotesCaducados.length > 0} />
      {bodegas.length > 0 && (
        <div className="col-span-2 md:col-span-6 bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-slate-600 mb-2">Unidades por bodega</h3>
          <div className="flex flex-wrap gap-2">
            {bodegas.map(([b, v]) => (
              <span key={b} className="text-sm bg-slate-100 px-3 py-1 rounded-full">
                {b}: <strong>{v}</strong>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function diasRestantes(fechaISO: string): number {
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const f = new Date(fechaISO + "T00:00:00");
  return Math.round((f.getTime() - hoy.getTime()) / 86400000);
}

function BadgeCaducidad({ fechaISO }: { fechaISO: string }) {
  const d = diasRestantes(fechaISO);
  if (d < 0) return <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Caducado</span>;
  if (d <= 30) return <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">{d}d</span>;
  return <span className="text-xs text-slate-500">{fechaISO}</span>;
}

function TablaMedicamentos({ medicamentos }: { medicamentos: Medicamento[] }) {
  return (
    <Tarjeta titulo="Medicamentos">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2">SKU</th><th>Nombre</th><th>Categoría</th>
              <th className="text-right">Lotes</th>
              <th className="text-right">Stock</th><th className="text-right">Mín.</th><th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {medicamentos.map((m) => (
              <tr key={m.id} className="border-b last:border-0">
                <td className="py-2 font-mono text-xs">{m.sku}</td>
                <td>{m.nombre}</td>
                <td>{m.categoria}</td>
                <td className="text-right">{m.numLotes}</td>
                <td className="text-right font-semibold">{m.stockTotal}</td>
                <td className="text-right text-slate-400">{m.stockMinimo}</td>
                <td>
                  {m.bajoStock
                    ? <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Bajo stock</span>
                    : <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">OK</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Tarjeta>
  );
}

function TablaLotes({
  lotes, bodegas, filtro, setFiltro, nombreMed,
}: {
  lotes: Lote[]; bodegas: Bodega[]; filtro: string;
  setFiltro: (v: string) => void; nombreMed: (id: string) => Medicamento | undefined;
}) {
  const selector = (
    <select value={filtro} onChange={(e) => setFiltro(e.target.value)} className="border rounded px-2 py-1 text-sm">
      <option value="">Todas las bodegas</option>
      {bodegas.map((b) => <option key={b.codigo} value={b.codigo}>{b.nombre}</option>)}
    </select>
  );
  return (
    <Tarjeta titulo={`Lotes (${lotes.length})`} extra={selector}>
      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-white">
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2">Medicamento</th><th>Lote</th><th>Bodega</th>
              <th className="text-right">Stock</th><th>Caducidad</th>
            </tr>
          </thead>
          <tbody>
            {lotes.map((l) => (
              <tr key={l.id} className="border-b last:border-0">
                <td className="py-2">{nombreMed(l.medicamentoId)?.nombre ?? l.medicamentoId}</td>
                <td className="font-mono text-xs">{l.numeroLote}</td>
                <td><span className="text-xs bg-slate-100 px-2 py-0.5 rounded-full">{l.bodegaCodigo}</span></td>
                <td className="text-right font-semibold">{l.stockActual}</td>
                <td><BadgeCaducidad fechaISO={l.fechaCaducidad} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Tarjeta>
  );
}

function Formularios({
  medicamentos, bodegas, lotes, onHecho,
}: {
  medicamentos: Medicamento[]; bodegas: Bodega[]; lotes: Lote[]; onHecho: () => void;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <FormEntrada medicamentos={medicamentos} bodegas={bodegas} onHecho={onHecho} />
      <FormSalida lotes={lotes} medicamentos={medicamentos} onHecho={onHecho} />
    </div>
  );
}

function FormEntrada({ medicamentos, bodegas, onHecho }: { medicamentos: Medicamento[]; bodegas: Bodega[]; onHecho: () => void }) {
  const [medId, setMedId] = useState("");
  const [bodega, setBodega] = useState("");
  const [numeroLote, setNumeroLote] = useState("");
  const [fecha, setFecha] = useState("");
  const [cantidad, setCantidad] = useState(10);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setMsg(null); setErr(null);
    try {
      const r = await api.registrarEntrada({ medicamentoId: medId, numeroLote, bodegaCodigo: bodega, fechaCaducidad: fecha, cantidad });
      setMsg(`Entrada registrada. Stock total: ${r.stockTotalMedicamento}`);
      onHecho();
    } catch (e) { setErr((e as Error).message); }
  }

  return (
    <Tarjeta titulo="Entrada (nuevo lote / reposición)">
      <form onSubmit={enviar} className="space-y-2">
        <select value={medId} onChange={(e) => setMedId(e.target.value)} required className="w-full border rounded px-2 py-1.5 text-sm">
          <option value="">Medicamento…</option>
          {medicamentos.map((m) => <option key={m.id} value={m.id}>{m.sku} — {m.nombre}</option>)}
        </select>
        <select value={bodega} onChange={(e) => setBodega(e.target.value)} required className="w-full border rounded px-2 py-1.5 text-sm">
          <option value="">Bodega…</option>
          {bodegas.map((b) => <option key={b.codigo} value={b.codigo}>{b.nombre}</option>)}
        </select>
        <div className="grid grid-cols-2 gap-2">
          <input value={numeroLote} onChange={(e) => setNumeroLote(e.target.value)} placeholder="N.º lote" required className="border rounded px-2 py-1.5 text-sm" />
          <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required className="border rounded px-2 py-1.5 text-sm" />
        </div>
        <input type="number" min={1} value={cantidad} onChange={(e) => setCantidad(Number(e.target.value))} className="w-full border rounded px-2 py-1.5 text-sm" />
        <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-500 text-white rounded py-2 text-sm">Registrar entrada</button>
      </form>
      {msg && <p className="mt-2 text-sm text-green-700">{msg}</p>}
      {err && <p className="mt-2 text-sm text-red-600">{err}</p>}
    </Tarjeta>
  );
}

function FormSalida({ lotes, medicamentos, onHecho }: { lotes: Lote[]; medicamentos: Medicamento[]; onHecho: () => void }) {
  const [loteId, setLoteId] = useState("");
  const [cantidad, setCantidad] = useState(1);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const nombre = new Map(medicamentos.map((m) => [m.id, m.nombre]));

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setMsg(null); setErr(null);
    try {
      const r = await api.registrarSalida({ loteId, cantidad });
      setMsg(`Salida registrada. Stock total: ${r.stockTotalMedicamento}${r.bajoStock ? " ⚠️ bajo stock" : ""}`);
      onHecho();
    } catch (e) { setErr((e as Error).message); }
  }

  return (
    <Tarjeta titulo="Salida (despacho por lote)">
      <form onSubmit={enviar} className="space-y-2">
        <select value={loteId} onChange={(e) => setLoteId(e.target.value)} required className="w-full border rounded px-2 py-1.5 text-sm">
          <option value="">Lote…</option>
          {lotes.map((l) => (
            <option key={l.id} value={l.id}>
              {nombre.get(l.medicamentoId)} · {l.numeroLote} · {l.bodegaCodigo} · stock {l.stockActual}
            </option>
          ))}
        </select>
        <input type="number" min={1} value={cantidad} onChange={(e) => setCantidad(Number(e.target.value))} className="w-full border rounded px-2 py-1.5 text-sm" />
        <button type="submit" className="w-full bg-slate-900 hover:bg-slate-700 text-white rounded py-2 text-sm">Registrar salida</button>
      </form>
      {msg && <p className="mt-2 text-sm text-green-700">{msg}</p>}
      {err && <p className="mt-2 text-sm text-red-600">{err}</p>}
    </Tarjeta>
  );
}

function PanelRestock({ alertas }: { alertas: Medicamento[] }) {
  return (
    <Tarjeta titulo={`Reabastecimiento (${alertas.length})`}>
      {alertas.length === 0 ? <p className="text-sm text-slate-400">Sin alertas 🎉</p> : (
        <ul className="space-y-2">
          {alertas.map((m) => (
            <li key={m.id} className="flex justify-between items-center bg-red-50 border border-red-200 rounded px-3 py-2">
              <div>
                <div className="font-medium text-sm">{m.nombre}</div>
                <div className="text-xs text-slate-500 font-mono">{m.sku}</div>
              </div>
              <div className="text-right text-xs">
                <div className="text-red-600 font-bold">{m.stockTotal}</div>
                <div className="text-slate-400">mín {m.stockMinimo}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}

function PanelCaducidad({ lotes, nombreMed }: { lotes: Lote[]; nombreMed: (id: string) => Medicamento | undefined }) {
  return (
    <Tarjeta titulo={`Próximos a caducar (${lotes.length})`}>
      {lotes.length === 0 ? <p className="text-sm text-slate-400">Sin alertas 🎉</p> : (
        <ul className="space-y-2">
          {lotes.map((l) => (
            <li key={l.id} className="flex justify-between items-center bg-amber-50 border border-amber-200 rounded px-3 py-2">
              <div>
                <div className="font-medium text-sm">{nombreMed(l.medicamentoId)?.nombre ?? l.medicamentoId}</div>
                <div className="text-xs text-slate-500 font-mono">{l.numeroLote} · {l.bodegaCodigo}</div>
              </div>
              <div className="text-amber-600 font-bold text-xs">{diasRestantes(l.fechaCaducidad)}d</div>
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
  const [meta, setMeta] = useState<{ modo: string; fuentes: string[] } | null>(null);
  const [cargando, setCargando] = useState(false);

  async function preguntar(e: FormEvent) {
    e.preventDefault();
    setCargando(true); setRespuesta(null);
    try {
      const r = await api.preguntarAsistente(pregunta);
      setRespuesta(r.respuesta);
      setMeta({ modo: r.modo, fuentes: r.fuentes });
    } catch (e) {
      setRespuesta(`Error: ${(e as Error).message}`);
      setMeta(null);
    } finally { setCargando(false); }
  }

  return (
    <Tarjeta titulo="🤖 Asistente">
      <form onSubmit={preguntar} className="space-y-2">
        <textarea
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder="¿Cuál lote caduca primero? ¿Cuál va a durar más? ¿Qué hay en la cámara de frío?"
          className="w-full border rounded px-2 py-1.5 text-sm h-20"
        />
        <button type="submit" disabled={cargando || !pregunta} className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded py-2 text-sm">
          {cargando ? "Pensando…" : "Preguntar"}
        </button>
      </form>
      {respuesta && (
        <div className="mt-3 text-sm">
          <p className="whitespace-pre-wrap">{respuesta}</p>
          {meta && (
            <div className="mt-2 text-xs text-slate-500">
              modo: <span className="font-mono">{meta.modo}</span>
              {meta.fuentes.length > 0 && <> · fuentes: {meta.fuentes.join(", ")}</>}
            </div>
          )}
        </div>
      )}
    </Tarjeta>
  );
}
