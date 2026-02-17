from odoo import models, fields, api


class Curso(models.Model):
    _name = 'eduodoo.curso'
    _description = 'Curso Académico'
    _rec_name = 'titulo'

    titulo = fields.Char(string='Título', required=True, size=255)
    descripcion = fields.Text(string='Descripción')
    nivel = fields.Selection(
        selection=[
            ('a1', 'A1 - Principiante'),
            ('a2', 'A2 - Elemental'),
            ('b1', 'B1 - Intermedio'),
            ('b2', 'B2 - Intermedio Alto'),
            ('c1', 'C1 - Avanzado'),
            ('c2', 'C2 - Dominio Pleno'),
        ],
        string='Nivel del Curso',
        required=True
    )
    precio = fields.Float(string='Precio', required=True, digits=(10, 2))
    
    # Relaciones
    sesiones = fields.One2many(
        comodel_name='eduodoo.sesion',
        inverse_name='curso_id',
        string='Sesiones'
    )
    clases = fields.One2many(
        comodel_name='eduodoo.clases',
        inverse_name='curso_id',
        string='Clases'
    )
    alumnos = fields.Many2many(
        comodel_name='eduodoo.alumno',
        relation='curso_alumno_rel',
        column1='curso_id',
        column2='alumno_id',
        string='Alumnos Inscritos'
    )
    
    # Campos adicionales
    activo = fields.Boolean(string='Activo', default=True)
    fecha_creacion = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now)

    @api.model
    def name_create(self, name):
        """Allow creating a course from a quick 'create' (name_create) by
        providing defaults for required fields that the quick-create doesn't set.
        """
        vals = {
            'titulo': name,
            # sensible defaults to avoid RPC errors from the client quick-create
            'nivel': 'a1',
            'precio': 0.0,
        }
        record = self.create(vals)
        return record
