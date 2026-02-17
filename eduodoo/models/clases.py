from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Clases(models.Model):
    _name = 'eduodoo.clases'
    _description = 'Clase del Curso'
    _rec_name = 'nombre_clase'

    nombre_clase = fields.Char(string='Nombre de la Clase', required=True)
    codigo_clase = fields.Char(string='Código de Clase', required=True)
    
    # Horario de la clase
    dia_semana = fields.Selection(
        selection=[
            ('lunes', 'Lunes'),
            ('martes', 'Martes'),
            ('miercoles', 'Miércoles'),
            ('jueves', 'Jueves'),
            ('viernes', 'Viernes'),
            ('sabado', 'Sábado'),
            ('domingo', 'Domingo'),
        ],
        string='Día de la Semana',
        required=True
    )
    hora_inicio = fields.Float(string='Hora de Inicio', required=True, help='Ej: 09.00, 14.30')
    hora_fin = fields.Float(string='Hora de Fin', required=True)
    
    # Relación Many2one con Curso
    curso_id = fields.Many2one(
        comodel_name='eduodoo.curso',
        string='Curso',
        required=True,
        ondelete='cascade'
    )
    
    # Relación Many2many con Alumnos
    alumnos = fields.Many2many(
        comodel_name='eduodoo.alumno',
        relation='clases_alumno_rel',
        column1='clase_id',
        column2='alumno_id',
        string='Alumnos'
    )
    
    # Relaciones adicionales
    sesiones = fields.One2many(
        comodel_name='eduodoo.sesion',
        inverse_name='clase_id',
        string='Sesiones'
    )
    profesor_id = fields.Many2one(
        comodel_name='eduodoo.profesor',
        string='Profesor'
    )
    asistencias = fields.One2many(
        comodel_name='eduodoo.asistencia',
        inverse_name='clase_id',
        string='Registro de Asistencias'
    )
    
    # Información adicional
    capacidad_maxima = fields.Integer(string='Capacidad Máxima', required=True)
    descripcion = fields.Text(string='Descripción')
    activo = fields.Boolean(string='Activo', default=True)
    fecha_inicio_clase = fields.Date(string='Fecha de Inicio')
    fecha_fin_clase = fields.Date(string='Fecha de Fin')
    
    # Campos computados
    numero_alumnos = fields.Integer(
        string='Número de Alumnos',
        compute='_compute_numero_alumnos',
        readonly=True
    )
    
    capacidad_disponible = fields.Integer(
        string='Capacidad Disponible',
        compute='_compute_capacidad_disponible',
        readonly=True
    )
    
    porcentaje_ocupacion = fields.Float(
        string='% Ocupación',
        compute='_compute_porcentaje_ocupacion',
        readonly=True
    )
    
    duracion_clase = fields.Float(
        string='Duración (horas)',
        compute='_compute_duracion_clase',
        store=True
    )

    @api.depends('alumnos')
    def _compute_numero_alumnos(self):
        """Calcula el número de alumnos inscritos"""
        for record in self:
            record.numero_alumnos = len(record.alumnos)

    @api.depends('numero_alumnos', 'capacidad_maxima')
    def _compute_capacidad_disponible(self):
        """Calcula la capacidad disponible"""
        for record in self:
            record.capacidad_disponible = max(record.capacidad_maxima - record.numero_alumnos, 0)

    @api.depends('numero_alumnos', 'capacidad_maxima')
    def _compute_porcentaje_ocupacion(self):
        """Calcula el porcentaje de ocupación"""
        for record in self:
            if record.capacidad_maxima > 0:
                record.porcentaje_ocupacion = (record.numero_alumnos / record.capacidad_maxima) * 100
                record.porcentaje_ocupacion = min(record.porcentaje_ocupacion, 100.0)
            else:
                record.porcentaje_ocupacion = 0.0

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duracion_clase(self):
        """Calcula la duración de la clase en horas"""
        for record in self:
            if record.hora_inicio and record.hora_fin:
                record.duracion_clase = record.hora_fin - record.hora_inicio
            else:
                record.duracion_clase = 0.0

    def get_asistencia_promedio(self):
        """Calcula el promedio de asistencia de la clase"""
        if not self.asistencias:
            return 0.0
        presentes = len(self.asistencias.filtered(lambda x: x.presente))
        return (presentes / len(self.asistencias)) * 100 if self.asistencias else 0.0

    def get_alumnos_inactivos(self):
        """Retorna alumnos sin asistencia registrada"""
        return self.alumnos.filtered(
            lambda x: not self.asistencias.filtered(lambda a: a.alumno_id == x)
        )

    def action_generar_lista_asistencia(self):
        """Abre la lista de asistencia para la clase"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Lista de Asistencia - {self.nombre_clase}',
            'res_model': 'eduodoo.asistencia',
            'view_mode': 'list,form',
            'domain': [('clase_id', '=', self.id)],
            'context': {'default_clase_id': self.id},
        }

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_horario_valido(self):
        """Valida que la hora de fin sea mayor que la de inicio"""
        for record in self:
            if record.hora_fin <= record.hora_inicio:
                raise ValidationError('La hora de fin debe ser mayor que la hora de inicio')

    @api.constrains('numero_alumnos', 'capacidad_maxima')
    def _check_capacidad_no_superada(self):
        """Valida que no se supere la capacidad"""
        for record in self:
            if record.numero_alumnos > record.capacidad_maxima:
                raise ValidationError(
                    f'El número de alumnos ({record.numero_alumnos}) '
                    f'supera la capacidad máxima ({record.capacidad_maxima})'
                )

    @api.constrains('codigo_clase')
    def _check_codigo_clase_unique(self):
        """Valida que el código de clase sea único"""
        for record in self:
            if record.codigo_clase:
                existing = self.env['eduodoo.clases'].search([
                    ('codigo_clase', '=', record.codigo_clase),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError('El código de clase debe ser único')
