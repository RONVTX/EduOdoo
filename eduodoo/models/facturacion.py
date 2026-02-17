from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class Facturacion(models.Model):
    _name = 'eduodoo.facturacion'
    _description = 'Facturación de Estudiantes'
    _rec_name = 'numero_factura'

    numero_factura = fields.Char(
        string='Número de Factura',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('eduodoo.facturacion')
    )
    
    # Relación Many2one con Alumno
    alumno_id = fields.Many2one(
        comodel_name='eduodoo.alumno',
        string='Alumno',
        required=True,
        ondelete='cascade'
    )
    
    # Relación Many2one con Curso
    curso_id = fields.Many2one(
        comodel_name='eduodoo.curso',
        string='Curso',
        required=True,
        ondelete='cascade'
    )
    
    # Información de facturación
    cantidad = fields.Float(string='Cantidad', required=True, digits=(10, 2))
    fecha_factura = fields.Date(string='Fecha de Factura', required=True, default=fields.Date.today)
    fecha_pago = fields.Date(string='Fecha de Pago')
    fecha_vencimiento = fields.Date(
        string='Fecha de Vencimiento',
        compute='_compute_fecha_vencimiento',
        store=True
    )
    
    # Concepto de la facturación
    concepto = fields.Selection(
        selection=[
            ('matricula', 'Matrícula'),
            ('mensualidad', 'Mensualidad'),
            ('clases_extra', 'Clases Extra'),
            ('material', 'Material'),
            ('otro', 'Otro'),
        ],
        string='Concepto',
        required=True
    )
    
    # Descripción adicional del concepto
    descripcion = fields.Text(string='Descripción')
    
    # Estado de la factura
    estado = fields.Selection(
        selection=[
            ('pendiente', 'Pendiente de Pago'),
            ('pagada', 'Pagada'),
            ('parcialmente_pagada', 'Parcialmente Pagada'),
            ('cancelada', 'Cancelada'),
        ],
        string='Estado',
        default='pendiente'
    )
    
    # Cantidad pagada
    cantidad_pagada = fields.Float(
        string='Cantidad Pagada',
        digits=(10, 2),
        default=0.0,
        compute='_compute_cantidad_pagada'
    )
    
    # Saldo pendiente
    saldo_pendiente = fields.Float(
        string='Saldo Pendiente',
        digits=(10, 2),
        compute='_compute_saldo_pendiente'
    )
    
    # Información adicional
    notas = fields.Text(string='Notas')
    activo = fields.Boolean(string='Activo', default=True)
    
    # Campo para días de vencimiento
    dias_vencimiento = fields.Integer(string='Días para Vencimiento', default=30)
    
    # Campo para identificar si está vencida
    factura_vencida = fields.Boolean(
        string='Factura Vencida',
        compute='_compute_factura_vencida',
        readonly=True
    )

    @api.depends('cantidad', 'estado')
    def _compute_cantidad_pagada(self):
        for record in self:
            if record.estado == 'pagada':
                record.cantidad_pagada = record.cantidad
            elif record.estado == 'parcialmente_pagada':
                if not record.cantidad_pagada:
                    record.cantidad_pagada = 0.0
            else:
                record.cantidad_pagada = 0.0

    @api.depends('cantidad', 'cantidad_pagada')
    def _compute_saldo_pendiente(self):
        for record in self:
            record.saldo_pendiente = record.cantidad - record.cantidad_pagada

    @api.depends('fecha_factura', 'dias_vencimiento')
    def _compute_fecha_vencimiento(self):
        """Calcula la fecha de vencimiento sumando días"""
        for record in self:
            if record.fecha_factura:
                record.fecha_vencimiento = record.fecha_factura + timedelta(days=record.dias_vencimiento)
            else:
                record.fecha_vencimiento = False

    @api.depends('fecha_vencimiento', 'estado')
    def _compute_factura_vencida(self):
        """Determina si la factura está vencida y aún no pagada"""
        for record in self:
            if record.estado in ['pagada', 'cancelada']:
                record.factura_vencida = False
            elif record.fecha_vencimiento:
                record.factura_vencida = record.fecha_vencimiento < fields.Date.today()
            else:
                record.factura_vencida = False

    def action_marcar_pagada(self):
        """Marca la factura como pagada"""
        for record in self:
            if record.estado == 'cancelada':
                raise ValidationError('No se puede marcar como pagada una factura cancelada')
            record.estado = 'pagada'
            record.cantidad_pagada = record.cantidad
            record.fecha_pago = fields.Date.today()

    def action_marcar_parcialmente_pagada(self, cantidad_pagada):
        """Marca la factura como parcialmente pagada"""
        for record in self:
            if cantidad_pagada <= 0 or cantidad_pagada > record.cantidad:
                raise ValidationError('El monto pagado debe ser mayor a 0 y menor al total adeudado')
            record.estado = 'parcialmente_pagada'
            record.cantidad_pagada = cantidad_pagada
            record.fecha_pago = fields.Date.today()

    def action_cancelar_factura(self):
        """Cancela la factura"""
        for record in self:
            record.estado = 'cancelada'

    def action_generar_reporte_pdf(self):
        """Genera un reporte PDF de la factura"""
        return self.env.ref('eduodoo.action_facturacion_report').report_action(self)

    def get_facturas_vencidas(self):
        """Retorna todas las facturas vencidas del alumno"""
        return self.filtered(lambda x: x.factura_vencida and x.estado != 'pagada')

    def get_estado_cuenta(self):
        """Retorna un resumen del estado de cuenta del alumno"""
        return {
            'alumno': self.alumno_id.nombre_completo,
            'total_adeudado': sum(map(lambda x: x.saldo_pendiente, self)),
            'total_pagado': sum(map(lambda x: x.cantidad_pagada, self)),
            'numero_facturas': len(self),
            'facturas_vencidas': len(self.get_facturas_vencidas()),
        }

    @api.constrains('cantidad', 'dias_vencimiento')
    def _check_cantidad_positiva(self):
        """Valida que la cantidad sea positiva"""
        for record in self:
            if record.cantidad <= 0:
                raise ValidationError('La cantidad debe ser un valor positivo')
            if record.dias_vencimiento < 0:
                raise ValidationError('Los días de vencimiento no pueden ser negativos')
            record.saldo_pendiente = record.cantidad - record.cantidad_pagada

    @api.constrains('numero_factura')
    def _check_numero_factura_unique(self):
        """Valida que el número de factura sea único"""
        for record in self:
            if record.numero_factura:
                existing = self.env['eduodoo.facturacion'].search([
                    ('numero_factura', '=', record.numero_factura),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError('El número de factura debe ser único')
