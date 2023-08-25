# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class account_journal(models.Model):
    _inherit = "account.journal"

    pos_method_type = fields.Selection([
        ('default', 'Default'),
        ('voucher', 'Voucher'),
    ], default='default', string='POS method type', required=1)





