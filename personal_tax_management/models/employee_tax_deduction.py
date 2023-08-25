# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import datetime

class employee_tax_deduction_line(models.Model):
    _name = 'employee.tax.deduction.line'
    _rec_name = 'type'

    type = fields.Many2one('employee.tax.deduction.type', string='Type')
    amount = fields.Float('Amount')

class employee_tax_deduction_type(models.Model):
    _name = 'employee.tax.deduction.type'

    name = fields.Char('Name')

class hr_employee_tax_deduction(models.Model):
    _name = "hr.employee.tax.deduction"

    employee_tax_deduction_id = fields.Many2one('employee.tax.deduction.line', string='Type')
    person = fields.Integer(string='Person',default=1)
    rate_amount = fields.Float(related='employee_tax_deduction_id.amount', string='Max Amount Rate', readonly=True)
    amount = fields.Float(string='Amount')
    hr_contract_id = fields.Many2one('hr.contract')

    @api.onchange('employee_tax_deduction_id', 'person')
    def _onchange_employee_tax_deduction(self):
        # print 'compute_employee_tax_deduction_id'
        for deduct in self:
            deduct.amount = deduct.rate_amount * deduct.person

    @api.multi
    def write(self, vals):

        if 'employee_tax_deduction_id' in vals:
            deduction_id = self.env['employee.tax.deduction.line'].browse(vals['employee_tax_deduction_id'])
        else:
            deduction_id = self.employee_tax_deduction_id


        if 'amount' in vals:
            amount = vals['amount']
        else:
            amount = self.amount

        if 'person' in vals:
            person = vals['person']
        else:
            person = self.person


        max_amount = self.rate_amount * person
        if amount > max_amount:
            raise UserError(_("Amount more than authorize tax deduction rate."))
        return super(hr_employee_tax_deduction, self).write(vals)



















