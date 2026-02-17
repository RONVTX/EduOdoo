from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Matricula(models.Model):
    _name = 'eduodoo.matricula'
    _description = 'Matrícula de Alumno a Sesión'
    _rec_name = 'display_name'

    alumno_id = fields.Many2one(
        comodel_name='eduodoo.alumno',
        string='Alumno',
        required=True,
        ondelete='cascade'
    )
    sesion_id = fields.Many2one(
        comodel_name='eduodoo.sesion',
        string='Sesión',
        required=True,
        ondelete='cascade'
    )
    fecha = fields.Date(string='Fecha de Matrícula', default=fields.Date.context_today)
    estado = fields.Selection(
        selection=[
            ('borrador', 'Borrador'),
            ('confirmada', 'Confirmada'),
            ('pagada', 'Pagada'),
            ('cancelada', 'Cancelada'),
        ],
        string='Estado',
        default='borrador'
    )
    notas = fields.Text(string='Notas')
    display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=True)
    
    # Campos adicionales para rastreo
    fecha_confirmacion = fields.Datetime(string='Fecha de Confirmación')
    fecha_pago = fields.Datetime(string='Fecha de Pago')
    observaciones = fields.Text(string='Observaciones')
    
    # Campo para saldo pendiente
    saldo_pendiente = fields.Float(
        string='Saldo Pendiente',
        compute='_compute_saldo_pendiente',
        store=True
    )
    
    precio_inscripcion = fields.Float(
        string='Precio de Inscripción',
        compute='_compute_precio_inscripcion',
        readonly=True
    )

    @api.depends('alumno_id', 'sesion_id')
    def _compute_display_name(self):
        for rec in self:
            partes = []
            if rec.alumno_id:
                partes.append(getattr(rec.alumno_id, 'nombre', str(rec.alumno_id.id)))
            if rec.sesion_id:
                partes.append(getattr(rec.sesion_id, 'numero_sesion', str(rec.sesion_id.id)))
            rec.display_name = ' - '.join(partes) if partes else '/'

    @api.depends('sesion_id.curso_id.precio')
    def _compute_precio_inscripcion(self):
        """Obtiene el precio del curso asociado a la sesión"""
        for rec in self:
            if rec.sesion_id and rec.sesion_id.curso_id:
                rec.precio_inscripcion = rec.sesion_id.curso_id.precio
            else:
                rec.precio_inscripcion = 0.0

    @api.constrains('alumno_id', 'sesion_id')
    def _check_matricula_unique(self):
        """Valida que el alumno no esté matriculado dos veces en la misma sesión"""
        for record in self:
            if record.alumno_id and record.sesion_id:
                existing = self.env['eduodoo.matricula'].search([
                    ('alumno_id', '=', record.alumno_id.id),
                    ('sesion_id', '=', record.sesion_id.id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError('El alumno ya está matriculado en esta sesión')

    @api.depends('estado', 'precio_inscripcion')
    def _compute_saldo_pendiente(self):
        """Calcula el saldo pendiente de la matrícula"""
        for rec in self:
            if rec.estado == 'pagada':
                rec.saldo_pendiente = 0.0
            else:
                rec.saldo_pendiente = rec.precio_inscripcion

    @api.onchange('sesion_id')
    def _onchange_sesion_validar_disponibilidad(self):
        """Valida disponibilidad al cambiar sesión y muestra advertencia"""
        if self.sesion_id:
            ocupados = self.sesion_id.asientos_ocupados or 0
            disponibles = self.sesion_id.numero_asientos - ocupados if self.sesion_id.numero_asientos else 0
            if disponibles <= 0:
                return {
                    'warning': {
                        'title': 'Advertencia',
                        'message': 'La sesión seleccionada está llena. No hay asientos disponibles.'
                    }
                }
            if disponibles <= 2:
                return {
                    'warning': {
                        'title': 'Advertencia',
                        'message': f'Solo hay {disponibles} asiento(s) disponible(s).'
                    }
                }

    def action_confirm(self):
        """Confirma la matrícula con validaciones exhaustivas"""
        for rec in self:
            if rec.estado != 'borrador':
                continue
            
            sesion = rec.sesion_id
            if not sesion:
                raise ValidationError('La matrícula debe estar asociada a una sesión')
            
            # Comprobar cupo
            ocupados = sesion.asientos_ocupados if sesion.asientos_ocupados is not None else 0
            if sesion.numero_asientos is not None and (ocupados + 1) > sesion.numero_asientos:
                raise ValidationError('No hay asientos disponibles en la sesión seleccionada')
            
            # Validar que el alumno no tenga otra matrícula en la misma clase simultáneamente
            clase = sesion.clase_id
            if clase:
                matriculas_existentes = self.search([
                    ('alumno_id', '=', rec.alumno_id.id),
                    ('sesion_id.clase_id', '=', clase.id),
                    ('estado', 'in', ['confirmada', 'pagada']),
                    ('id', '!=', rec.id),
                ])
                if matriculas_existentes:
                    raise ValidationError('El alumno ya está matriculado en otra sesión de esta clase')
            
            # Actualizar alumno en la clase
            if sesion.clase_id:
                sesion.clase_id.alumnos = [(4, rec.alumno_id.id)]
            
            rec.estado = 'confirmada'
            rec.fecha_confirmacion = fields.Datetime.now()

    def action_set_paid(self):
        """Marca la matrícula como pagada y genera factura automática"""
        for rec in self:
            if rec.estado not in ['confirmada', 'borrador']:
                raise ValidationError('Solo se puede marcar como pagada una matrícula confirmada o en borrador')
            
            rec.estado = 'pagada'
            rec.fecha_pago = fields.Datetime.now()
            
            # Crear factura automáticamente si no existe
            facturacion = self.env['eduodoo.facturacion'].search([
                ('alumno_id', '=', rec.alumno_id.id),
                ('sesion_id', '=', rec.sesion_id.id) if hasattr(rec.sesion_id, 'id') else False,
            ])
            if not facturacion and rec.sesion_id and rec.sesion_id.curso_id:
                self.env['eduodoo.facturacion'].create({
                    'alumno_id': rec.alumno_id.id,
                    'curso_id': rec.sesion_id.curso_id.id,
                    'cantidad': rec.precio_inscripcion,
                    'concepto': 'matricula',
                    'estado': 'pagada',
                    'fecha_factura': fields.Date.today(),
                    'fecha_pago': fields.Date.today(),
                })

    def action_cancel(self):
        """Cancela la matrícula y libera el asiento"""
        for rec in self:
            if rec.estado == 'cancelada':
                continue
            
            sesion = rec.sesion_id
            if sesion and sesion.clase_id:
                # Remover alumno de la clase
                sesion.clase_id.alumnos = [(3, rec.alumno_id.id)]
            
            rec.estado = 'cancelada'

    @api.constrains('sesion_id', 'alumno_id')
    def _check_cupo_en_confirm(self):
        """Valida cupo al confirmar"""
        for rec in self:
            if rec.estado == 'confirmada' or rec.estado == 'pagada':
                sesion = rec.sesion_id
                if sesion and sesion.numero_asientos is not None:
                    ocupados = sesion.asientos_ocupados if sesion.asientos_ocupados is not None else 0
                    ya_inscrito = rec.alumno_id.id in (sesion.clase_id.alumnos.ids if sesion.clase_id else [])
                    if not ya_inscrito and ocupados >= sesion.numero_asientos:
                        raise ValidationError('No quedan asientos disponibles en la sesión seleccionada')
