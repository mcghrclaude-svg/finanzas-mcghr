/**
 * modules/Inbox/index.jsx
 *
 * Punto de entrada del modulo Inbox.
 * Por defecto usa InboxA (revision una por una, YNAB-inspired).
 *
 * Para probar InboxB (triaje en masa, Gmail-inspired):
 *   Cambiar el import a './InboxB'
 *
 * Ambas versiones respetan Issue #26:
 *   completitud es TEXT: 'minimo' | 'parcial' | 'completo'
 *   Nunca se compara contra numeros flotantes.
 *
 * Endpoints consumidos:
 *   GET  /api/v1/inbox/               -- lista pendientes
 *   GET  /api/v1/inbox/stats          -- contadores para badge
 *   POST /api/v1/inbox/{id}/confirmar -- confirmar
 *   POST /api/v1/inbox/{id}/descartar -- descartar
 *   POST /api/v1/inbox/confirmar-lote -- confirmar varios (solo InboxB)
 */
export { default } from './InboxA'
