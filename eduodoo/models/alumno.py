from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Alumno(models.Model):
    _name = 'eduodoo.alumno'
    _description = 'Alumno de la Academia'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True, size=100)
    apellidos = fields.Char(string='Apellidos', required=True, size=100)
    email = fields.Char(string='Email', required=True)
    
    # Campo calculado para el nombre completo
    nombre_completo = fields.Char(
        string='Nombre Completo',
        compute='_compute_nombre_completo',
        store=True
    )
    
    # Información de contacto adicional
    telefono = fields.Char(string='Teléfono')
    direccion = fields.Text(string='Dirección')
    ciudad = fields.Char(string='Ciudad')
    codigo_postal = fields.Char(string='Código Postal')
    
    # Relaciones
    cursos = fields.Many2many(
        comodel_name='eduodoo.curso',
        relation='curso_alumno_rel',
        column1='alumno_id',
        column2='curso_id',
        string='Cursos Inscritos'
    )
    facturas = fields.One2many(
        comodel_name='eduodoo.facturacion',
        inverse_name='alumno_id',
        string='Facturas'
    )
    asistencias_clases = fields.One2many(
        comodel_name='eduodoo.asistencia',
        inverse_name='alumno_id',
        string='Asistencias'
    )
    
    matriculas = fields.One2many(
        comodel_name='eduodoo.matricula',
        inverse_name='alumno_id',
        string='Matrículas'
    )
    
    # Campos calculados para estadísticas
    porcentaje_asistencia = fields.Float(
        string='% Asistencia',
        compute='_compute_porcentaje_asistencia',
        readonly=True
    )
    
    total_facturas_pendientes = fields.Float(
        string='Total Adeudado',
        compute='_compute_total_facturas_pendientes',
        readonly=True
    )
    
    numero_matriculas = fields.Integer(
        string='Número de Matrículas',
        compute='_compute_numero_matriculas',
        readonly=True
    )
    
    # Campos adicionales
    fecha_registro = fields.Datetime(string='Fecha de Registro', default=fields.Datetime.now)
    activo = fields.Boolean(string='Activo', default=True)

    def _compute_nombre_completo(self):
        for record in self:
            record.nombre_completo = f"{record.nombre} {record.apellidos}"

    @api.depends('asistencias_clases')
    def _compute_porcentaje_asistencia(self):
        """Calcula el porcentaje de asistencia del alumno"""
        for record in self:
            if not record.asistencias_clases:
                record.porcentaje_asistencia = 0.0
            else:
                total = len(record.asistencias_clases)
                presentes = len(record.asistencias_clases.filtered(lambda x: x.presente))
                record.porcentaje_asistencia = (presentes / total * 100) if total > 0 else 0.0

    @api.depends('facturas.estado', 'facturas.saldo_pendiente')
    def _compute_total_facturas_pendientes(self):
        """Calcula el total pendiente de pago del alumno"""
        for record in self:
            record.total_facturas_pendientes = sum(
                record.facturas.filtered(lambda x: x.estado in ['pendiente', 'parcialmente_pagada']).mapped('saldo_pendiente')
            )

    @api.depends('matriculas')
    def _compute_numero_matriculas(self):
        """Cuenta el número de matrículas confirmadas"""
        for record in self:
            record.numero_matriculas = len(record.matriculas.filtered(lambda x: x.estado in ['confirmada', 'pagada']))

    def get_promedio_asistencia(self):
        """Retorna el porcentaje de asistencia como valor numérico"""
        return self.porcentaje_asistencia

    def get_facturas_pendientes(self):
        """Retorna las facturas pendientes de pago"""
        return self.facturas.filtered(lambda x: x.estado in ['pendiente', 'parcialmente_pagada'])

    def get_matriculas_activas(self):
        """Retorna las matrículas confirmadas o pagadas"""
        return self.matriculas.filtered(lambda x: x.estado in ['confirmada', 'pagada'])

    def action_generar_reporte_desempenio(self):
        """Abre un reporte con el desempeño académico del alumno"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Reporte de Desempeño - {self.nombre_completo}',
            'res_model': 'eduodoo.alumno',
            'res_id': self.id,
            'view_mode': 'form',
            'context': {'report_mode': True},
        }
