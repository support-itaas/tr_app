# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
import time
from odoo.exceptions import UserError

class Hr_payslip_department(models.Model):
    _inherit = "hr.payslip"

    department_id = fields.Many2one('hr.department',string="Department",related="employee_id.department_id",store=True)



class Hr_payslip_line_department(models.Model):
    _inherit = "hr.payslip.line"

    department_id = fields.Many2one('hr.department',string="Department",related="slip_id.department_id" ,store=True)


class Hr_salary_rule_inherit(models.Model):
    _inherit = "hr.salary.rule"

    account_id = fields.Many2one('account.account',string="Account")
    credit = fields.Boolean('Credit')