# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import datetime

class hr_contract(models.Model):
    _inherit = 'hr.contract'

    hr_tax_deduction_ids = fields.One2many('hr.employee.tax.deduction', 'hr_contract_id')
    total_deduction_amount = fields.Float(string='Total Deduction Amount',compute='get_total_deduction',store=True)

    @api.multi
    @api.depends('hr_tax_deduction_ids')
    def get_total_deduction(self):
        for contract in self:
            contract.total_deduction_amount = sum(line.amount for line in contract.hr_tax_deduction_ids)

