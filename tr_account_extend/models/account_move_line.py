# -*- coding: utf-8 -*-

from odoo import api, fields, models

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    is_extra_no_paid = fields.Boolean(string='ตั้งค่าเผื่อหนี้สังสัยจะสูญ')

    
