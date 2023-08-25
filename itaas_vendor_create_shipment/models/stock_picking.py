
from odoo import models, fields, api


class Stockpicking(models.Model):
    _inherit = 'stock.picking'

    bill_id = fields.Many2one('account.invoice', string='Invoice Id')
