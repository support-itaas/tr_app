# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _


class Inventory(models.Model):
    _name = "assets.location"
    _rec_name = "name_location"

    # company_id = fields.Many2one('res.company',string="Company")
    # parent_id = fields.Char(string="Parent")
    name_location = fields.Char(string="Name")
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account')



