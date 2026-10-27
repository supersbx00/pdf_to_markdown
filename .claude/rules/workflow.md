# Flujo de Trabajo y Reglas de Ejecución

## 1. El Ciclo OpenSpec
Todo desarrollo debe seguir el ciclo riguroso de OpenSpec:
1. **Planificar** (`/opsx:propose`, después del protocolo de preguntas de `CLAUDE.md`; el usuario debe aprobarlo antes de aplicar): Analizar el alcance, definir contratos de la API y decidir qué componentes del Feature Layer Cascade se verán afectados.
2. **Aplicar**: Implementar los cambios escribiendo el código de las capas correspondientes.
3. **Hacer los Changes**: Ejecutar la validación, pruebas y confirmar que la integración sea correcta.
   - **Tope de intentos:** si una prueba del feature sigue fallando tras **3 intentos** de corrección, detente y reporta al usuario qué falla y qué se intentó.
   - **Tests preexistentes:** antes de aplicar, corre la suite para tener la línea base. Los tests que ya fallaban antes del cambio no se tocan sin que el usuario lo pida; se reportan como preexistentes.

## 2. Regla de Desarrollo Secuencial Estricto
- **Un Feature a la vez:** Está estrictamente prohibido crear, modificar o planificar más de un feature por petición.
- Si el requerimiento incluye múltiples módulos (ej. `usuarios` y `carro_de_compras`), **se debe resolver primero uno por completo** (Planificar -> Aplicar -> Testear). Solo una vez aprobado ese módulo (el usuario lo dice explícitamente), se avanza al siguiente. Esto mantiene el hilo de contexto limpio y evita errores de cruce de lógica.