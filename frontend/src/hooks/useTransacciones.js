import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { transaccionesApi } from '@/api/transacciones'
import { useUndo } from '@/hooks/useUndo'
import toast from 'react-hot-toast'

export function useTransacciones(filtros = {}) {
  return useQuery({
    queryKey: ['transacciones', filtros],
    queryFn: () => transaccionesApi.listar(filtros),
  })
}

export function useConfirmarTransaccion() {
  const qc = useQueryClient()
  const { ejecutar } = useUndo()

  return useMutation({
    mutationFn: ({ id, data }) =>
      ejecutar({
        descripcion: 'Confirmar transacción',
        accion: () => transaccionesApi.confirmar(id),
        deshacer: () => transaccionesApi.descartar(id),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transacciones'] })
      qc.invalidateQueries({ queryKey: ['inbox'] })
      toast.success('Transacción confirmada')
    },
  })
}
