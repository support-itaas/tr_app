# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class account_journal(models.Model):
    _inherit = "account.journal"

    type_pos_order = fields.Selection([('bank', "Bank"), ('cash', "Cash"), ('transfer', "Transfer"), ], string="Type Pos Order")





