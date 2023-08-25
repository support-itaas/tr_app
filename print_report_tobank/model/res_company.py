# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  ITaas.
from odoo import fields, api, models


class res_company(models.Model):
    _inherit = 'res.company'

    scb_code = fields.Char(string='SCB Code')
    bank_ac = fields.Char(string='Bank Account')
    # scb_code = fields.Char(string='SCB Code#2')
    # bank_ac = fields.Char(string='Bank Account#2')
