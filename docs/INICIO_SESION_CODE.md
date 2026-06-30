# Inicio obligatorio de sesion en Claude Code
# Finanzas MCGHR -- Entorno de desarrollo

## Entorno
- Repo local: C:\Users\ghriz\finanzas-mcghr
- DB desarrollo: data/dev/finanzas_dev.db (usar sqlite_dev)
- DB produccion: NO tocar en sesiones de desarrollo (sqlite apunta a OneDrive)
- Branch: trabajar siempre en branch dedicada, nunca commitear directo en main

## Leer antes de cualquier tarea (en este orden)
1. CLAUDE.md -- reglas de arquitectura y estado actual del proyecto
2. docs/ADR.md -- decisiones de arquitectura con contexto y razon
3. docs/CITA.md -- errores conocidos y como prevenirlos
4. docs/HANDOFF_{YYYYMMDD}.md -- estado del dia (reemplazar fecha real)

## Reglas obligatorias
- Leer archivo real antes de modificarlo -- mostrar contenido leido (CITA-004)
- Pedir PRAGMA table_info antes de tocar cualquier modelo de DB (CITA-005)
- Solo ASCII en codigo, comentarios y nombres de archivo (CITA-009)
- Si un fix falla: PARAR -- mostrar diagnostico antes del segundo intento (CITA-010)
- Commits: listar archivos explicitos, nunca git add -A (CITA-008)
- Instrucciones de terminal siempre en segunda persona
- Incluir siempre: activar venv + Set-ExecutionPolicy en instrucciones PS1 (CITA-001)

## Separacion de entornos -- regla critica
- filesystem_dev: leer/escribir archivos del repo de desarrollo
- sqlite_dev: leer/escribir DB de desarrollo unicamente
- filesystem y sqlite (prod): NO escribir en sesiones de desarrollo
- Si necesitas consultar prod como referencia: solo lectura, confirmacion explicita

## Flujo de trabajo con branches
- Antes de empezar: confirmar en que branch estamos (git branch)
- Cada tema tiene su branch: chat-ux, chat-backend, etc.
- Al terminar: listar archivos modificados antes de cualquier commit
- Nunca mergear a main sin confirmacion de Hernan

## Chats paralelos
- Si este chat trabaja en paralelo con otro, confirmar lista de archivos
  antes de commitear para evitar pisar trabajo del otro chat

## Senales de alarma (detener y avisar a Hernan)
- El modelo propone modificar un archivo sin haberlo leido en este turno
- El modelo usa sqlite (prod) en lugar de sqlite_dev
- El modelo propone git add -A
- El modelo genera un segundo fix sin mostrar diagnostico del primero
