from odoo import models, fields


class Profesor(models.Model):
    _name = 'eduodoo.profesor'
    _description = 'Profesor'
    _rec_name = 'name'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contacto'
    )
    email = fields.Char(string='Email')
    phone = fields.Char(string='Teléfono')
    notas = fields.Text(string='Notas')

    # Relaciones
    sesiones = fields.One2many(
        comodel_name='eduodoo.sesion',
        inverse_name='profesor_id',
        string='Sesiones'
    )
    clases = fields.One2many(
        comodel_name='eduodoo.clases',
        inverse_name='profesor_id',
        string='Clases'
    )
