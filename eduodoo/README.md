# EduOdoo - Sistema de Gestión Académica

## Descripción

EduOdoo es un módulo integral de gestión académica para Odoo que permite administrar cursos, clases, sesiones, alumnos, profesores y matrículas de manera eficiente y segura.

## Restricciones Implementadas y Soluciones

### 1. Restricciones de Horarios y Disponibilidad

#### a) Conflicto de Horarios de Profesores
**Problema**: Un profesor no puede impartir múltiples sesiones simultáneamente.

**Solución**: Implementada en `models/sesion.py` con el método `@api.constrains('profesor_id', 'fecha_inicio', 'duracion')`:
- Valida que no existan sesiones solapadas para el mismo profesor
- Calcula el rango temporal de cada sesión (fecha_inicio + duración)
- Lanza `ValidationError` si detecta conflicto con mensaje descriptivo

#### b) Horarios Válidos de Clases
**Problema**: Las clases deben tener horarios coherentes.

**Solución**: Implementada en `models/clases.py` con el método `@api.constrains('hora_inicio', 'hora_fin')`:
- Valida que la hora de fin sea mayor que la hora de inicio
- Previene la creación de clases con horarios inválidos

### 2. Restricciones de Capacidad y Cupos

#### a) Límite de Asientos en Sesiones
**Problema**: Las sesiones tienen capacidad limitada y no pueden excederse.

**Solución**: Implementada en `models/sesion.py` con el método `@api.constrains('numero_asientos', 'clase_id')`:
- Valida que el número de alumnos inscritos no supere los asientos disponibles
- Calcula asientos ocupados dinámicamente desde la relación con clases
- Lanza `ValidationError` con conteo detallado

#### b) Capacidad Máxima de Clases
**Problema**: Las clases tienen capacidad máxima que no debe excederse.

**Solución**: Implementada en `models/clases.py` con el método `@api.constrains('numero_alumnos', 'capacidad_maxima')`:
- Valida que el número de alumnos no supere la capacidad máxima
- Proporciona mensaje claro con números específicos

### 3. Restricciones de Unicidad e Integridad

#### a) Unicidad de Códigos de Clase
**Problema**: Los códigos de clase deben ser únicos en el sistema.

**Solución**: Implementada en `models/clases.py` con el método `@api.constrains('codigo_clase')`:
- Busca códigos duplicados excluyendo el registro actual
- Garantiza integridad de datos a nivel de clase

#### b) Unicidad de Matrículas
**Problema**: Un alumno no puede matricularse dos veces en la misma sesión.

**Solución**: Implementada en `models/matricula.py` con el método `@api.constrains('alumno_id', 'sesion_id')`:
- Valida combinaciones únicas de alumno + sesión
- Previene duplicación de matrículas

#### c) No Matriculación Simultánea en Mismas Clases
**Problema**: Un alumno no puede estar matriculado en múltiples sesiones de la misma clase simultáneamente.

**Solución**: Implementada en `models/matricula.py` en el método `action_confirm()`:
- Verifica matrículas existentes en otras sesiones de la misma clase
- Solo permite estados 'confirmada' o 'pagada' como conflicto

### 4. Validaciones de Estado y Transiciones

#### a) Transiciones de Estado Controladas
**Problema**: Las matrículas deben seguir un flujo lógico de estados.

**Solución**: Implementada en `models/matricula.py`:
- `action_confirm()`: Valida cupo disponible antes de confirmar
- `action_set_paid()`: Solo permite pago desde estados válidos
- `action_cancel()`: Libera asientos al cancelar

#### b) Estados de Sesión
**Problema**: Las sesiones tienen estados que controlan su ciclo de vida.

**Solución**: Implementada en `models/sesion.py`:
- Estados: programada → en_curso → finalizada/cancelada
- Métodos `action_iniciar_sesion()`, `action_finalizar_sesion()`, `action_cancelar_sesion()`
- Cancelación libera todos los asientos automáticamente

### 5. Validaciones de Disponibilidad en Tiempo Real

#### a) Advertencias de Capacidad
**Problema**: Los usuarios deben ser informados sobre disponibilidad limitada.

**Solución**: Implementada en `models/matricula.py` con `@api.onchange('sesion_id')`:
- Muestra advertencias cuando quedan pocos asientos
- Bloquea selección cuando la sesión está llena

### 6. Cálculos Automáticos y Monitoreo

#### a) Ocupación y Disponibilidad
**Problema**: Necesidad de monitorear capacidad en tiempo real.

**Solución**: Campos computados en múltiples modelos:
- `asientos_disponibles`, `porcentaje_ocupacion` en sesiones
- `capacidad_disponible`, `porcentaje_ocupacion` en clases
- Barras de progreso visuales con colores dinámicos

#### b) Integridad de Datos Relacional
**Problema**: Mantener consistencia entre modelos relacionados.

**Solución**: Relaciones One2many/Many2one con `ondelete='cascade'`:
- Eliminación en cascada mantiene integridad referencial
- Actualización automática de listas de alumnos en clases

## Beneficios de las Soluciones Implementadas

1. **Prevención de Errores**: Las restricciones evitan inconsistencias en los datos
2. **Experiencia de Usuario**: Mensajes claros y advertencias proactivas
3. **Integridad de Datos**: Unicidad y validaciones mantienen la calidad de la información
4. **Automatización**: Cálculos automáticos reducen errores manuales
5. **Escalabilidad**: Las validaciones funcionan independientemente del volumen de datos

## Dependencias

- `base`: Funcionalidades básicas de Odoo
- `mail`: Sistema de mensajería para notificaciones

## Instalación

1. Colocar el módulo en la carpeta `addons` de Odoo
2. Actualizar la lista de módulos
3. Instalar "EduOdoo - Sistema de Gestión Académica"

## Uso

Después de la instalación, acceder al módulo desde el menú principal para:
- Gestionar cursos y clases
- Administrar alumnos y profesores
- Controlar matrículas y pagos
- Monitorear asistencia y rendimiento</content>
<parameter name="filePath">c:\Users\benro\Desktop\odoo\addons\eduodoo\README.md