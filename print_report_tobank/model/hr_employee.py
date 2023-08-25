# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  ITaas.
from odoo import fields, api, models


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    bank_branch_code = fields.Char(string='สาขาธนาคาร')