from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Asistencia(models.Model):
    _name = 'eduodoo.asistencia'
    _description = 'Registro de Asistencia'
    _rec_name = 'alumno_id'

    # Relación Many2one con Alumno
    alumno_id = fields.Many2one(
        comodel_name='eduodoo.alumno',
        string='Alumno',
        required=True,
        ondelete='cascade'
    )
    
    # Relación Many2one con Clase
    clase_id = fields.Many2one(
        comodel_name='eduodoo.clases',
        string='Clase',
        required=True,
        ondelete='cascade'
    )
    
    # Relación Many2one con Sesión
    sesion_id = fields.Many2one(
        comodel_name='eduodoo.sesion',
        string='Sesión',
        required=True,
        ondelete='cascade'
    )
    
    # Información de asistencia
    fecha_asistencia = fields.Date(string='Fecha de Asistencia', required=True)
    presente = fields.Boolean(string='Presente', default=False)
    justificacion = fields.Text(string='Justificación de Ausencia')
    
    # Observaciones
    observaciones = fields.Text(string='Observaciones')
    
    # Campo para estado visual
    estado_asistencia = fields.Selection(
        selection=[
            ('presente', 'Presente'),
            ('ausente', 'Ausente'),
            ('ausente_justificado', 'Ausente Justificado'),
            ('retraso', 'Retraso'),
        ],
        string='Estado de Asistencia',
        compute='_compute_estado_asistencia',
        readonly=True
    )

    @api.depends('presente', 'justificacion')
    def _compute_estado_asistencia(self):
        """Calcula el estado de asistencia según presente y justificación"""
        for record in self:
            if record.presente:
                record.estado_asistencia = 'presente'
            elif record.justificacion:
                record.estado_asistencia = 'ausente_justificado'
            else:
                record.estado_asistencia = 'ausente'

    @api.onchange('presente')
    def _onchange_presente_limpiar_justificacion(self):
        """Si marca como presente, limpia el campo de justificación"""
        if self.presente:
            self.justificacion = False

    def action_marcar_presente(self):
        """Marca rápidamente al alumno como presente"""
        for record in self:
            record.presente = True
            record.justificacion = False

    def action_marcar_ausente(self, justificacion=''):
        """Marca al alumno como ausente con justificación opcional"""
        for record in self:
            record.presente = False
            record.justificacion = justificacion

    def action_marcar_ausente_justificado(self, justificacion):
        """Marca al alumno como ausente pero justificado"""
        for record in self:
            if not justificacion:
                raise ValidationError('Debe proporcionar una justificación')
            record.presente = False
            record.justificacion = justificacion

    @api.constrains('fecha_asistencia', 'sesion_id')
    def _check_fecha_asistencia_valida(self):
        """Valida que la fecha de asistencia sea la fecha de la sesión"""
        for record in self:
            if record.sesion_id and record.fecha_asistencia:
                # Solo valida si la sesión tiene fecha_inicio
                if record.sesion_id.fecha_inicio:
                    fecha_sesion = record.sesion_id.fecha_inicio.date()
                    if record.fecha_asistencia != fecha_sesion:
                        raise ValidationError(
                            f'La fecha de asistencia debe coincidir con la fecha de la sesión '
                            f'({fecha_sesion.strftime("%d/%m/%Y")})'
                        )
