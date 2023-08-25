# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import datetime

class personal_income_tax(models.Model):
    _name = 'personal.income.tax'
    _rec_name = 'year'

    def year_choices(self):
        return [(r, r) for r in range(1984, datetime.date.today().year + 1)]

    def current_year(self):
        return datetime.date.today().year

    year = fields.Integer(_('Year'), choices=year_choices, default=current_year)
    deduct_general_expense_percent = fields.Float(string='General Expense Deduction %')
    deduct_general_expense_max = fields.Float(string='General Expense Dedcution Max Amount')
    deduction_after_expense_amount = fields.Float(string='Deduction After Deduct General Expense')
    personal_tax_line_ids = fields.One2many('personal.income.tax.line', 'personal_tax_id')

class personal_income_tax_line(models.Model):
    _name = 'personal.income.tax.line'

    rate_no = fields.Integer('Rate No.')
    minimum_rate = fields.Integer('Minimum Rate')
    maximum_rate = fields.Integer('Maximum Rate')
    tax_rate = fields.Float('Rate %')
    personal_tax_id = fields.Many2one('personal.income.tax')










