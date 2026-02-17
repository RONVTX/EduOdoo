-- ============================================================================
-- EduOdoo - Sistema Integral de Gestión para una Academia de Cursos
-- Diagrama de Relaciones de Base de Datos
-- ============================================================================

-- TABLA: eduodoo_curso
-- Descripción: Cursos académicos ofertados
-- Relaciones: 
--   - One2many a: eduodoo_sesion, eduodoo_clases
--   - Many2many a: eduodoo_alumno (tabla: curso_alumno_rel)
CREATE TABLE IF NOT EXISTS eduodoo_curso (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    nivel VARCHAR(10) NOT NULL, -- a1, a2, b1, b2, c1, c2
    precio NUMERIC(10, 2) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    create_uid INTEGER,
    write_uid INTEGER,
    create_date TIMESTAMP DEFAULT NOW(),
    write_date TIMESTAMP DEFAULT NOW()
);

-- TABLA: eduodoo_alumno
-- Descripción: Alumnos de la academia
-- Relaciones:
--   - One2many a: eduodoo_facturacion, eduodoo_asistencia
--   - Many2many a: eduodoo_curso (tabla: curso_alumno_rel)
--   - Many2many a: eduodoo_clases (tabla: clases_alumno_rel)
CREATE TABLE IF NOT EXISTS eduodoo_alumno (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    nombre_completo VARCHAR(200),
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    direccion TEXT,
    ciudad VARCHAR(100),
    codigo_postal VARCHAR(10),
    fecha_registro TIMESTAMP DEFAULT NOW(),
    activo BOOLEAN DEFAULT TRUE,
    create_uid INTEGER,
    write_uid INTEGER,
    create_date TIMESTAMP DEFAULT NOW(),
    write_date TIMESTAMP DEFAULT NOW()
);

-- TABLA: eduodoo_clases
-- Descripción: Grupos de clase dentro de cursos
-- Relaciones:
--   - Many2one a: eduodoo_curso (campo: curso_id)
--   - One2many a: eduodoo_sesion, eduodoo_asistencia
--   - Many2many a: eduodoo_alumno (tabla: clases_alumno_rel)
CREATE TABLE IF NOT EXISTS eduodoo_clases (
    id SERIAL PRIMARY KEY,
    nombre_clase VARCHAR(255) NOT NULL,
    codigo_clase VARCHAR(100) NOT NULL UNIQUE,
    curso_id INTEGER NOT NULL,
    dia_semana VARCHAR(20) NOT NULL, -- lunes, martes, miercoles, jueves, viernes, sabado, domingo
    hora_inicio NUMERIC(5, 2) NOT NULL,
    hora_fin NUMERIC(5, 2) NOT NULL,
    capacidad_maxima INTEGER NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_inicio_clase DATE,
    fecha_fin_clase DATE,
    create_uid INTEGER,
    write_uid INTEGER,
    create_date TIMESTAMP DEFAULT NOW(),
    write_date TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (curso_id) REFERENCES eduodoo_curso(id) ON DELETE CASCADE
);

-- TABLA: eduodoo_sesion
-- Descripción: Sesiones de clase
-- Relaciones:
--   - Many2one a: eduodoo_curso (campo: curso_id)
--   - Many2one a: eduodoo_clases (campo: clase_id)
--   - One2many a: eduodoo_asistencia
CREATE TABLE IF NOT EXISTS eduodoo_sesion (
    id SERIAL PRIMARY KEY,
    numero_sesion VARCHAR(100) NOT NULL,
    curso_id INTEGER NOT NULL,
    clase_id INTEGER NOT NULL,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP,
    duracion INTEGER NOT NULL, -- en minutos
    numero_asientos INTEGER NOT NULL,
    asientos_disponibles INTEGER,
    descripcion TEXT,
    estado VARCHAR(20) DEFAULT 'programada', -- programada, en_curso, finalizada, cancelada
    create_uid INTEGER,
    write_uid INTEGER,
    create_date TIMESTAMP DEFAULT NOW(),
    write_date TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (curso_id) REFERENCES eduodoo_curso(id) ON DELETE CASCADE,
    FOREIGN KEY (clase_id) REFERENCES eduodoo_clases(id) ON DELETE CASCADE
);

-- TABLA: eduodoo_facturacion
-- Descripción: Facturación y pagos de alumnos
-- Relaciones:
--   - Many2one a: eduodoo_alumno (campo: alumno_id)
--   - Many2one a: eduodoo_curso (campo: curso_id)
CREATE TABLE IF NOT EXISTS eduodoo_facturacion (
    id SERIAL PRIMARY KEY,
    numero_factura VARCHAR(100) NOT NULL UNIQUE,
    alumno_id INTEGER NOT NULL,
    curso_id INTEGER NOT NULL,
    cantidad NUMERIC(10, 2) NOT NULL,
    cantidad_pagada NUMERIC(10, 2) DEFAULT 0.0,
    saldo_pendiente NUMERIC(10, 2),
    fecha_factura DATE NOT NULL,
    fecha_pago DATE,
    concepto VARCHAR(50) NOT NULL, -- matricula, mensualidad, clases_extra, material, otro
    descripcion TEXT,
    estado VARCHAR(50) DEFAULT 'pendiente', -- pendiente, pagada, parcialmente_pagada, cancelada
    notas TEXT,
    activo BOOLEAN DEFAULT TRUE,
    create_uid INTEGER,
    write_uid INTEGER,
    create_date TIMESTAMP DEFAULT NOW(),
    write_date TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (alumno_id) REFERENCES eduodoo_alumno(id) ON DELETE CASCADE,
    FOREIGN KEY (curso_id) REFERENCES eduodoo_curso(id) ON DELETE CASCADE
);

-- TABLA: eduodoo_asistencia
-- Descripción: Registro de asistencia de alumnos
-- Relaciones:
--   - Many2one a: eduodoo_alumno (campo: alumno_id)
--   - Many2one a: eduodoo_clases (campo: clase_id)
--   - Many2one a: eduodoo_sesion (campo: sesion_id)
CREATE TABLE IF NOT EXISTS eduodoo_asistencia (
    id SERIAL PRIMARY KEY,
    alumno_id INTEGER NOT NULL,
    clase_id INTEGER NOT NULL,
    sesion_id INTEGER NOT NULL,
    fecha_asistencia DATE NOT NULL,
    presente BOOLEAN DEFAULT FALSE,
    justificacion TEXT,
    observaciones TEXT,
    create_uid INTEGER,
    write_uid INTEGER,
    create_date TIMESTAMP DEFAULT NOW(),
    write_date TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (alumno_id) REFERENCES eduodoo_alumno(id) ON DELETE CASCADE,
    FOREIGN KEY (clase_id) REFERENCES eduodoo_clases(id) ON DELETE CASCADE,
    FOREIGN KEY (sesion_id) REFERENCES eduodoo_sesion(id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLAS DE RELACIÓN MANY2MANY
-- ============================================================================

-- TABLA: curso_alumno_rel
-- Descripción: Relación muchos-a-muchos entre Cursos y Alumnos
CREATE TABLE IF NOT EXISTS curso_alumno_rel (
    id SERIAL PRIMARY KEY,
    curso_id INTEGER NOT NULL,
    alumno_id INTEGER NOT NULL,
    FOREIGN KEY (curso_id) REFERENCES eduodoo_curso(id) ON DELETE CASCADE,
    FOREIGN KEY (alumno_id) REFERENCES eduodoo_alumno(id) ON DELETE CASCADE,
    UNIQUE (curso_id, alumno_id)
);

-- TABLA: clases_alumno_rel
-- Descripción: Relación muchos-a-muchos entre Clases y Alumnos
CREATE TABLE IF NOT EXISTS clases_alumno_rel (
    id SERIAL PRIMARY KEY,
    clase_id INTEGER NOT NULL,
    alumno_id INTEGER NOT NULL,
    FOREIGN KEY (clase_id) REFERENCES eduodoo_clases(id) ON DELETE CASCADE,
    FOREIGN KEY (alumno_id) REFERENCES eduodoo_alumno(id) ON DELETE CASCADE,
    UNIQUE (clase_id, alumno_id)
);

-- ============================================================================
-- ÍNDICES PARA MEJORAR RENDIMIENTO
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_sesion_curso ON eduodoo_sesion(curso_id);
CREATE INDEX IF NOT EXISTS idx_sesion_clase ON eduodoo_sesion(clase_id);
CREATE INDEX IF NOT EXISTS idx_clases_curso ON eduodoo_clases(curso_id);
CREATE INDEX IF NOT EXISTS idx_facturacion_alumno ON eduodoo_facturacion(alumno_id);
CREATE INDEX IF NOT EXISTS idx_facturacion_curso ON eduodoo_facturacion(curso_id);
CREATE INDEX IF NOT EXISTS idx_facturacion_estado ON eduodoo_facturacion(estado);
CREATE INDEX IF NOT EXISTS idx_asistencia_alumno ON eduodoo_asistencia(alumno_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_clase ON eduodoo_asistencia(clase_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_sesion ON eduodoo_asistencia(sesion_id);
CREATE INDEX IF NOT EXISTS idx_curso_nivel ON eduodoo_curso(nivel);
CREATE INDEX IF NOT EXISTS idx_alumno_email ON eduodoo_alumno(email);
CREATE INDEX IF NOT EXISTS idx_clases_codigo ON eduodoo_clases(codigo_clase);

-- ============================================================================
-- VISTAS ÚTILES PARA CONSULTAS
-- ============================================================================

-- Vista: Alumnos inscritos por curso
CREATE OR REPLACE VIEW v_alumnos_por_curso AS
SELECT 
    c.id as curso_id,
    c.titulo,
    c.nivel,
    a.id as alumno_id,
    a.nombre,
    a.apellidos,
    a.email,
    COUNT(DISTINCT a.id) as total_alumnos
FROM eduodoo_curso c
LEFT JOIN curso_alumno_rel car ON c.id = car.curso_id
LEFT JOIN eduodoo_alumno a ON car.alumno_id = a.id
GROUP BY c.id, c.titulo, c.nivel, a.id, a.nombre, a.apellidos, a.email;

-- Vista: Sesiones programadas
CREATE OR REPLACE VIEW v_sesiones_programadas AS
SELECT 
    s.id,
    s.numero_sesion,
    c.titulo as curso,
    cl.nombre_clase as clase,
    s.fecha_inicio,
    s.fecha_fin,
    s.duracion,
    s.numero_asientos,
    s.asientos_disponibles,
    s.estado
FROM eduodoo_sesion s
JOIN eduodoo_curso c ON s.curso_id = c.id
JOIN eduodoo_clases cl ON s.clase_id = cl.id
ORDER BY s.fecha_inicio;

-- Vista: Facturas pendientes
CREATE OR REPLACE VIEW v_facturas_pendientes AS
SELECT 
    f.id,
    f.numero_factura,
    CONCAT(a.nombre, ' ', a.apellidos) as alumno,
    c.titulo as curso,
    f.cantidad,
    f.cantidad_pagada,
    f.saldo_pendiente,
    f.fecha_factura,
    f.concepto,
    f.estado
FROM eduodoo_facturacion f
JOIN eduodoo_alumno a ON f.alumno_id = a.id
JOIN eduodoo_curso c ON f.curso_id = c.id
WHERE f.estado IN ('pendiente', 'parcialmente_pagada')
ORDER BY f.fecha_factura;

-- Vista: Asistencia por clase
CREATE OR REPLACE VIEW v_asistencia_por_clase AS
SELECT 
    cl.id,
    cl.nombre_clase,
    cl.codigo_clase,
    COUNT(DISTINCT a.id) as total_registros,
    SUM(CASE WHEN a.presente = TRUE THEN 1 ELSE 0 END) as presentes,
    SUM(CASE WHEN a.presente = FALSE THEN 1 ELSE 0 END) as ausentes,
    ROUND(
        (SUM(CASE WHEN a.presente = TRUE THEN 1 ELSE 0 END)::NUMERIC / 
         COUNT(DISTINCT a.id)) * 100, 2
    ) as porcentaje_asistencia
FROM eduodoo_clases cl
LEFT JOIN eduodoo_asistencia a ON cl.id = a.clase_id
GROUP BY cl.id, cl.nombre_clase, cl.codigo_clase;

-- ============================================================================
-- CONSULTAS DE VERIFICACIÓN Y REPORTES
-- ============================================================================

-- Reporte: Resumen de cursos activos
-- SELECT 
--     c.titulo,
--     c.nivel,
--     c.precio,
--     COUNT(DISTINCT car.alumno_id) as total_alumnos,
--     COUNT(DISTINCT cl.id) as total_clases,
--     COUNT(DISTINCT s.id) as total_sesiones
-- FROM eduodoo_curso c
-- LEFT JOIN curso_alumno_rel car ON c.id = car.curso_id
-- LEFT JOIN eduodoo_clases cl ON c.id = cl.curso_id
-- LEFT JOIN eduodoo_sesion s ON c.id = s.curso_id
-- WHERE c.activo = TRUE
-- GROUP BY c.id, c.titulo, c.nivel, c.precio
-- ORDER BY c.titulo;

-- Reporte: Ingresos por concepto de facturación
-- SELECT 
--     f.concepto,
--     COUNT(*) as cantidad_facturas,
--     SUM(f.cantidad) as total_monto,
--     SUM(f.cantidad_pagada) as total_pagado,
--     SUM(f.saldo_pendiente) as total_pendiente
-- FROM eduodoo_facturacion f
-- GROUP BY f.concepto
-- ORDER BY total_monto DESC;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
