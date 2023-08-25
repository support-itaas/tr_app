from odoo import api, fields, models


class Hr_Employee(models.Model):
    _inherit = 'hr.employee'

    source_location_id = fields.Many2one('stock.location', string="Source Location")