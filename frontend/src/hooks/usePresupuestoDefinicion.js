/**
 * usePresupuestoDefinicion -- datos para la pantalla de definicion de
 * presupuesto por categoria (modules/Presupuesto). Sigue el mismo patron
 * que useTransacciones.js: React Query para el fetch/cache, mutacion
 * dedicada para grabar.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { catalogosApi } from '@/api/catalogos'
import { presupuestosApi } from '@/api/presupuestos'

export function mesAnterior(anio, mes) {
  return mes === 1 ? { anio: anio - 1, mes: 12 } : { anio, mes: mes - 1 }
}

function porId(items) {
  const mapa = {}
  for (const item of items) mapa[item.id_categoria] = item.monto_presupuestado
  return mapa
}

export function usePresupuestoMes(anio, mes) {
  const anterior = mesAnterior(anio, mes)

  const categorias = useQuery({
    queryKey: ['categorias'],
    queryFn: () => catalogosApi.getCategorias(),
  })

  const resumen = useQuery({
    queryKey: ['presupuesto-resumen', anio, mes],
    queryFn: () => presupuestosApi.resumenPorCategoria(anio, mes),
  })

  const actual = useQuery({
    queryKey: ['presupuesto-mes', anio, mes],
    queryFn: () => presupuestosApi.listar(anio, mes),
  })

  const previo = useQuery({
    queryKey: ['presupuesto-mes', anterior.anio, anterior.mes],
    queryFn: () => presupuestosApi.listar(anterior.anio, anterior.mes),
  })

  const resumenById = {}
  for (const item of resumen.data?.categorias ?? []) {
    resumenById[item.id_categoria] = item.promedio_ultimos_3_meses
  }

  return {
    categorias: categorias.data?.items ?? [],
    resumenById,
    actualById: porId(actual.data?.items ?? []),
    anteriorById: porId(previo.data?.items ?? []),
    isLoading: categorias.isLoading || resumen.isLoading || actual.isLoading || previo.isLoading,
    error: categorias.error || resumen.error || actual.error || previo.error,
  }
}

export function useGuardarPresupuesto(anio, mes) {
  const qc = useQueryClient()

  const invalidar = () => {
    qc.invalidateQueries({ queryKey: ['presupuesto-mes', anio, mes] })
    qc.invalidateQueries({ queryKey: ['presupuesto-resumen', anio, mes] })
  }

  const guardar = useMutation({
    mutationFn: ({ items }) => presupuestosApi.guardarBatch(anio, mes, items),
    onSuccess: invalidar,
    onError: (e) => toast.error(e.message || 'No se pudo guardar el presupuesto'),
  })

  const eliminar = useMutation({
    mutationFn: ({ idCategoria }) => presupuestosApi.eliminar(anio, mes, idCategoria),
    onSuccess: invalidar,
    onError: (e) => toast.error(e.message || 'No se pudo actualizar el presupuesto'),
  })

  async function guardarPendientes({ paraGuardar, paraBorrar }) {
    if (paraGuardar.length > 0) {
      await guardar.mutateAsync({ items: paraGuardar })
    }
    for (const idCategoria of paraBorrar) {
      await eliminar.mutateAsync({ idCategoria })
    }
    if (paraGuardar.length > 0 || paraBorrar.length > 0) {
      toast.success('Presupuesto guardado')
    }
  }

  return { guardarPendientes, guardando: guardar.isPending || eliminar.isPending }
}
