# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _

class Account_Tax(models.Model):
    _inherit = 'account.tax'

    wht = fields.Boolean(string="WHT")
    wht_personal_company = fields.Selection([('personal', 'ภงด3'), ('company', 'ภงด53')])
    tax_report = fields.Boolean(string="Tax Report")
    tax_no_refund = fields.Boolean(string="Tax No Refund")
