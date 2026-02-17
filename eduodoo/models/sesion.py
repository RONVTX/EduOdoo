from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class Sesion(models.Model):
    _name = 'eduodoo.sesion'
    _description = 'Sesión del Curso'
    _rec_name = 'numero_sesion'

    numero_sesion = fields.Char(string='Número de Sesión', required=True)
    fecha_inicio = fields.Datetime(string='Fecha de Inicio', required=True)
    duracion = fields.Integer(string='Duración (minutos)', required=True)
    numero_asientos = fields.Integer(string='Número de Asientos', required=True)
    profesor_id = fields.Many2one(
        comodel_name='eduodoo.profesor',
        string='Profesor',
        help='Profesor responsable de la sesión'
    )
    
    # Relación Many2one con Curso
    curso_id = fields.Many2one(
        comodel_name='eduodoo.curso',
        string='Curso',
        required=True,
        ondelete='cascade'
    )
    
    # Relación Many2one con Clases
    clase_id = fields.Many2one(
        comodel_name='eduodoo.clases',
        string='Clase',
        required=True,
        ondelete='cascade'
    )
    
    # Campo calculado para la fecha de fin
    fecha_fin = fields.Datetime(
        string='Fecha de Fin',
        compute='_compute_fecha_fin',
        store=True
    )
    
    # Información adicional
    descripcion = fields.Text(string='Descripción')
    asientos_disponibles = fields.Integer(
        string='Asientos Disponibles',
        compute='_compute_asientos_disponibles',
        readonly=True
    )
    asientos_ocupados = fields.Integer(
        string='Asientos Ocupados',
        compute='_compute_asientos_ocupados',
        readonly=True
    )
    porcentaje_ocupacion = fields.Float(
        string='Porcentaje Ocupación',
        compute='_compute_porcentaje_ocupacion',
        readonly=True
    )
    is_full = fields.Boolean(
        string='Sesión Llena',
        compute='_compute_porcentaje_ocupacion',
        readonly=True
    )
    # Campo estándar que algunas vistas usan para colorear/reglas visuales
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
        store=True
    )
    occupancy_color = fields.Char(
        string='Color de Ocupación',
        compute='_compute_occupancy_color',
        store=True
    )
    occupancy_color_hsl = fields.Char(
        string='Color HSL de Ocupación',
        compute='_compute_occupancy_color_hsl',
        store=True
    )
    occupancy_bar_html = fields.Html(
        string='Barra de Ocupación',
        compute='_compute_occupancy_bar_html',
        store=False
    )
    estado = fields.Selection(
        selection=[
            ('programada', 'Programada'),
            ('en_curso', 'En Curso'),
            ('finalizada', 'Finalizada'),
            ('cancelada', 'Cancelada'),
        ],
        string='Estado',
        default='programada'
    )

    @api.depends('fecha_inicio', 'duracion')
    def _compute_fecha_fin(self):
        from datetime import timedelta
        for record in self:
            if record.fecha_inicio and record.duracion:
                record.fecha_fin = record.fecha_inicio + timedelta(minutes=record.duracion)
            else:
                record.fecha_fin = False

    def _compute_asientos_disponibles(self):
        for record in self:
            asientos_ocupados = len(record.clase_id.alumnos) if record.clase_id else 0
            record.asientos_ocupados = asientos_ocupados
            # No permitir negativos en asientos disponibles
            record.asientos_disponibles = max(record.numero_asientos - asientos_ocupados, 0)

    @api.depends('clase_id.alumnos')
    def _compute_asientos_ocupados(self):
        for record in self:
            record.asientos_ocupados = len(record.clase_id.alumnos) if record.clase_id else 0

    @api.depends('asientos_ocupados', 'numero_asientos')
    def _compute_porcentaje_ocupacion(self):
        for record in self:
            if record.numero_asientos and record.numero_asientos > 0:
                record.porcentaje_ocupacion = round(float(record.asientos_ocupados) * 100.0 / float(record.numero_asientos), 2)
                record.porcentaje_ocupacion = min(record.porcentaje_ocupacion, 100.0)
            else:
                record.porcentaje_ocupacion = 0.0
            record.is_full = record.asientos_ocupados >= record.numero_asientos if record.numero_asientos else False

    @api.depends('is_full')
    def _compute_color(self):
        # Asigna un código numérico simple para que la vista pueda cambiar colores (kanban/árbol)
        for record in self:
            # Si está llena, color alto (p. ej. 10), si no, color bajo (p. ej. 1)
            record.color = 10 if record.is_full else 1

    @api.depends('porcentaje_ocupacion')
    def _compute_occupancy_color(self):
        """Calcula el color de la barra de ocupación según el porcentaje"""
        for record in self:
            if record.porcentaje_ocupacion >= 70:
                # Rojo: 70% o más
                record.occupancy_color = 'danger'
            elif record.porcentaje_ocupacion >= 35:
                # Amarillo: 35% a 70%
                record.occupancy_color = 'warning'
            else:
                # Verde: menos de 35%
                record.occupancy_color = 'success'

    @api.depends('porcentaje_ocupacion')
    def _compute_occupancy_color_hsl(self):
        """Calcula el color HSL dinámico según el porcentaje"""
        for record in self:
            porcentaje = record.porcentaje_ocupacion or 0
            # Verde: 120, Amarillo: 60, Rojo: 0
            hue = max(0, 120 - (porcentaje * 1.2))
            saturation = 100
            lightness = 45
            record.occupancy_color_hsl = f"hsl({hue}, {saturation}%, {lightness}%)"

    @api.depends('porcentaje_ocupacion', 'occupancy_color_hsl')
    def _compute_occupancy_bar_html(self):
        """Genera HTML de la barra con color dinámico según porcentaje"""
        for record in self:
            porcentaje = record.porcentaje_ocupacion or 0
            color_hsl = record.occupancy_color_hsl or "hsl(120, 100%, 45%)"
            
            # Ancho mínimo pequeño para que el texto sea visible incluso en porcentajes bajos
            bar_width = max(porcentaje, 18)
            
            html = f'''
            <div style="width: 100%; margin: 8px 0;">
                <div style="background-color: #f0f0f0; border-radius: 8px; overflow: hidden; height: 32px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="width: {bar_width}%; background-color: {color_hsl}; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; transition: width 0.3s ease; white-space: nowrap;">
                        {porcentaje:.1f} %
                    </div>
                </div>
            </div>
            '''
            record.occupancy_bar_html = html

    @api.constrains('profesor_id', 'fecha_inicio', 'duracion')
    def _check_profesor_horario(self):
        from datetime import timedelta
        for record in self:
            if not (record.profesor_id and record.fecha_inicio and record.duracion):
                continue
            fecha_fin = record.fecha_inicio + timedelta(minutes=record.duracion)

            overlapping = self.search([
                ('id', '!=', record.id),
                ('profesor_id', '=', record.profesor_id.id),
            ])
            if overlapping:
                for other in overlapping:
                    other_fin = other.fecha_inicio + timedelta(minutes=other.duracion) if other.duracion else other.fecha_inicio
                    # Validar si hay solapamiento real
                    if other.fecha_inicio < fecha_fin and other_fin > record.fecha_inicio:
                        raise ValidationError(
                            f'El profesor {record.profesor_id.name} ya tiene otra sesión programada.\n'
                            f'Conflicto: {other.numero_sesion} ({other.fecha_inicio}) con duración {other.duracion} minutos.'
                        )

    @api.constrains('numero_asientos', 'clase_id')
    def _check_asientos_no_superan(self):
        for record in self:
            asientos_ocupados = len(record.clase_id.alumnos) if record.clase_id else 0
            if record.numero_asientos is not None and asientos_ocupados > record.numero_asientos:
                raise ValidationError('El número de alumnos inscritos (%d) supera el número de asientos (%d).' % (asientos_ocupados, record.numero_asientos))

    def action_cambiar_estado(self, nuevo_estado):
        """Cambia el estado de la sesión con validaciones"""
        for record in self:
            estados_validos = ['programada', 'en_curso', 'finalizada', 'cancelada']
            if nuevo_estado not in estados_validos:
                raise ValidationError(f'Estado inválido. Válidos: {", ".join(estados_validos)}')
            record.estado = nuevo_estado

    def action_iniciar_sesion(self):
        """Inicia la sesión"""
        self.action_cambiar_estado('en_curso')

    def action_finalizar_sesion(self):
        """Finaliza la sesión"""
        self.action_cambiar_estado('finalizada')

    def action_cancelar_sesion(self):
        """Cancela la sesión y libera todos los asientos"""
        for record in self:
            if record.clase_id:
                # Remover todos los alumnos
                record.clase_id.alumnos = [(5, 0)]
            record.estado = 'cancelada'

    def get_asistencia_sesion(self):
        """Retorna los registros de asistencia de la sesión"""
        return self.env['eduodoo.asistencia'].search([('sesion_id', '=', self.id)])

    def get_tasa_asistencia(self):
        """Calcula la tasa de asistencia de la sesión"""
        asistencias = self.get_asistencia_sesion()
        if not asistencias:
            return 0.0
        presentes = len(asistencias.filtered(lambda x: x.presente))
        return (presentes / len(asistencias)) * 100 if asistencias else 0.0

    def action_generar_reporte_sesion(self):
        """Abre un reporte detallado de la sesión"""

        report_action = None
        try:
            report_action = self.env.ref('eduodoo.action_sesion_report', raise_if_not_found=False)
        except TypeError:

            try:
                report_action = self.env.ref('eduodoo.action_sesion_report')
            except Exception:
                report_action = None
        except Exception:
            _logger.exception('Error buscando XMLID eduodoo.action_sesion_report para sesión %s', self.id)

        if report_action:
            try:
                _logger.info('Usando XMLID eduodoo.action_sesion_report -> report_name=%s id=%s', getattr(report_action, 'report_name', False), report_action.id)
                action = report_action.report_action(self)
                _logger.info('Report action returned (XMLID): %s', bool(action))
                return action
            except Exception:
                _logger.exception('Error ejecutando report_action desde XMLID eduodoo.action_sesion_report para sesión %s', self.id)

        _logger.warning('XMLID eduodoo.action_sesion_report no encontrado, intentando búsquedas alternativas para sesión %s', self.id)

        try:
            report = self.env['ir.actions.report']._get_report_from_name('eduodoo.report_sesion_document')
            if report:
                try:
                    _logger.info('Reporte encontrado por nombre: %s (id=%s)', report.report_name, report.id)
                    action = report.report_action(self)
                    _logger.info('Report action returned (name lookup): %s', bool(action))
                    return action
                except Exception:
                    _logger.exception('Error ejecutando report_action desde reporte encontrado por nombre para sesión %s', self.id)
        except Exception:
            _logger.exception('Error buscando reporte por nombre eduodoo.report_sesion_document para sesión %s', self.id)

        try:
            reports = self.env['ir.actions.report'].search([('model', '=', 'eduodoo.sesion')])
            if reports:
                try:
                    _logger.info('Reportes encontrados para model eduodoo.sesion: %s', reports.mapped('report_name'))
                    action = reports[0].report_action(self)
                    _logger.info('Report action returned (model search): %s', bool(action))
                    return action
                except Exception:
                    _logger.exception('Error ejecutando report_action desde report encontrado por modelo para sesión %s', self.id)
            else:
                _logger.warning('No se encontraron reportes en ir.actions.report para el modelo eduodoo.sesion')
        except Exception:
            _logger.exception('Error buscando reportes por modelo eduodoo.sesion para sesión %s', self.id)

        try:
            reports_like_eduodoo = self.env['ir.actions.report'].search([('report_name', 'ilike', 'eduodoo')], limit=20)
            _logger.info('Reportes con report_name ilike "eduodoo": %s', reports_like_eduodoo.mapped('report_name'))
            reports_like_sesion = self.env['ir.actions.report'].search([('report_name', 'ilike', 'sesion')], limit=20)
            _logger.info('Reportes con report_name ilike "sesion": %s', reports_like_sesion.mapped('report_name'))
        except Exception:
            _logger.exception('Error listando reportes para depuración de sesión %s', self.id)

        try:
            _logger.info('Intentando localizar o crear ir.actions.report para eduodoo.report_sesion_document')
            report = self.env['ir.actions.report'].search([('report_name', '=', 'eduodoo.report_sesion_document')], limit=1)
            if not report:
                report = self.env['ir.actions.report'].search([('model', '=', 'eduodoo.sesion'), ('report_type', '=', 'qweb-pdf')], limit=1)
            if not report:
                _logger.info('No existe ir.actions.report; creando uno temporal para renderizado')
                report = self.env['ir.actions.report'].create({
                    'name': 'Reporte de Sesión (temporal)',
                    'model': 'eduodoo.sesion',
                    'report_type': 'qweb-pdf',
                    'report_name': 'eduodoo.report_sesion_document',
                })

            _logger.info('Usando ir.actions.report id=%s report_name=%s', report.id, report.report_name)
            
            pdf_content = None
            try:
                pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(report, self.ids)
            except Exception as pdf_error:
                _logger.warning('Error renderizando PDF (probablemente falta wkhtmltopdf): %s. Intentando HTML...', str(pdf_error))
            
            if pdf_content:
                attachment = self.env['ir.attachment'].create({
                    'name': f'Reporte_Sesion_{self.id}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content).decode('utf-8'),
                    'res_model': 'eduodoo.sesion',
                    'res_id': self.id,
                })
                _logger.info('Adjunto PDF creado para reporte de sesión: ir.attachment id=%s', attachment.id)
                return {
                    'type': 'ir.actions.act_url',
                    'url': f'/web/content/{attachment.id}?download=true',
                    'target': 'self',
                }
            try:
                _logger.info('Renderizando reporte como HTML')
                html_content = self.env['ir.actions.report']._render_qweb_html(report, self.ids)[0]
                if isinstance(html_content, str):
                    html_bytes = html_content.encode('utf-8')
                else:
                    html_bytes = html_content
                attachment = self.env['ir.attachment'].create({
                    'name': f'Reporte_Sesion_{self.id}.html',
                    'type': 'binary',
                    'datas': base64.b64encode(html_bytes).decode('utf-8'),
                    'res_model': 'eduodoo.sesion',
                    'res_id': self.id,
                })
                _logger.info('Adjunto HTML creado para reporte de sesión: ir.attachment id=%s', attachment.id)
                return {
                    'type': 'ir.actions.act_url',
                    'url': f'/web/content/{attachment.id}?download=true',
                    'target': 'self',
                }
            except Exception as html_error:
                _logger.exception('Error renderizando HTML para sesión %s: %s', self.id, str(html_error))
        except Exception:
            _logger.exception('Error intentando renderizar plantilla QWeb directamente para sesión %s', self.id)

        raise UserError('No se pudo generar el reporte de sesión. Revisa los logs del servidor para más detalles.')
