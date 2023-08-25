#-*-coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from odoo import api, tools
from odoo.osv import osv
from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
import pytz
from datetime import datetime,timedelta,date
from odoo import SUPERUSER_ID
from odoo.tools import float_compare, float_is_zero
from decimal import *
import math

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class HR_Payslip(models.Model):
    _inherit = "hr.payslip"

    hr_user_id = fields.Many2one('res.users', string='HR User', default=lambda self: self.env.user.id)
    wage_type = fields.Selection([('daily', 'รายวัน'), ('monthly', 'รายเดือน'), ('hour', 'รายชั่วโมง')], compute='_compute_wage_type', store=True, readonly=False, string="ประเภทเงินเดือน")
    is_manual_leave = fields.Boolean(string='Manual Leave')

    @api.onchange('hr_user_id')
    def onchange_employee_wage_type(self):
        # print('def onchange_employee_wage_type')
        wage_type = self.env.context.get('default_wage_type')
        if wage_type == 'daily':
            domain = [('wage_type', '=', 'daily')]
        elif wage_type == 'monthly':
            domain = [('wage_type', '=', 'monthly')]
        elif wage_type == 'hour':
            domain = [('wage_type', '=', 'hour')]
        else:
            domain = ['|', '|', ('wage_type', '=', 'hour'), ('wage_type', '=', 'monthly'), ('wage_type', '=', 'daily')]
        return {'domain': {'employee_id': domain}}

    @api.depends('hr_user_id')
    def _compute_wage_type(self):
        # print('def _compute_wage_type')
        wage_type = self.env.context.get('default_wage_type')
        self.update({'wage_type' : wage_type,})

        # group_id = self.env['res.groups'].search([('name','=','Payroll Officer Monthly')], limit=1)
        # user_ids = []
        # if group_id:
        #     for user in group_id.users:
        #         user_ids.append(user.id)
        # if user_ids:
        #     if self.env.user.id in user_ids:
        #         wage_type = 'monthly'
        #         self.update({
        #             'wage_type' : wage_type,
        #         })
        #     else:
        #         wage_type = 'daily'
        #         self.update({
        #             'wage_type': wage_type,
        #         })

    def get_summary_for_tax(self):
        res = super(HR_Payslip, self).get_summary_for_tax()
        self.update_benefits_rule_category()
        return res

    def update_benefits_rule_category(self):
        # print('START--update_benefits_rule_category')
        sum_total_tax = self.sum_total_tax
        # print('sum_total_tax : ' + str(self.sum_total_tax))
        for benefit_line in self.benefit_line_ids:
            if benefit_line.category_id.rate_ids:
                for line in benefit_line.category_id.salary_rule_ids:
                    if line.cal_tax:
                        sum_total_tax = sum_total_tax + benefit_line.employee_amount
        self.sum_total_tax = sum_total_tax
        # print('sum benefits and tax : ' + str(sum_total_tax))
        # print('END--update_benefits_rule_category')

    def get_cal_leave(self):
        if not self.is_manual_leave:
            return super(HR_Payslip, self).get_cal_leave()


class HR_Employee(models.Model):
    _inherit = "hr.employee"

    wage_type = fields.Selection([('daily', 'รายวัน'), ('monthly', 'รายเดือน'), ('hour', 'รายชั่วโมง')], related='contract_id.wage_type', store=True, string="ประเภทเงินเดือน")

