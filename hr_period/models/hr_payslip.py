# -*- coding: utf-8 -*-
# Copyright 2015 Savoir-faire Linux. All Rights Reserved.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    hr_period_id = fields.Many2one(
        'hr.period',
        string='Period',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    date_payment = fields.Date(
        'Date of Payment',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    @api.multi
    @api.constrains('hr_period_id', 'company_id')
    def _check_period_company(self):
        for slip in self:
            if slip.hr_period_id:
                if slip.hr_period_id.company_id != slip.company_id:
                    raise UserError(_(
                        "The company on the selected period must be the same "
                        "as the company on the payslip."))

    @api.onchange('company_id', 'contract_id')
    def onchange_company_id(self):
        # print "onchange_company_id"
        if self.company_id:
            if self.contract_id:
                contract = self.contract_id
                period = self.env['hr.period'].get_next_period(
                    self.company_id.id, contract.schedule_pay)
            else:
                schedule_pay = self.env['hr.payslip.run'].get_default_schedule(
                    self.company_id.id)
                if self.company_id and schedule_pay:
                    period = self.env['hr.period'].get_next_period(
                        self.company_id.id, schedule_pay)

            # print "Assign period--company"
            self.hr_period_id = period.id if period else False
            self.onchange_hr_period_id()
            # print self.hr_period_id

    @api.multi
    @api.onchange('contract_id')
    def onchange_contract(self):
        # print "onchange_contract"
        super(HrPayslip, self).onchange_contract()
        if self.contract_id.employee_id and self.contract_id:
            employee = self.contract_id.employee_id
            contract = self.contract_id
            period = self.env['hr.period'].get_next_period(
                employee.company_id.id, contract.schedule_pay)
            if period:
                # print "Assign-contract-period"
                self.hr_period_id = period.id if period else False
                self.name = _('Salary Slip of %s for %s') % (employee.name,
                                                             period.name)

    @api.onchange('hr_period_id')
    def onchange_hr_period_id(self):
        # print "111111111-hr-period"
        # print self.hr_period_id
        # print "-----------------"
        if self.hr_period_id:
            # print "xxxxxxx"
            # dates must be updated together to prevent constraint
            self.date_from = self.hr_period_id.date_start
            self.date_to = self.hr_period_id.date_end
            self.date_payment = self.hr_period_id.date_payment
            # print self.date_payment

    @api.model
    def create(self, vals):
        # print "CREATE------------Payslip"
        # print vals
        if vals.get('payslip_run_id'):
            # print "------111--------"
            payslip_run = self.env['hr.payslip.run'].browse(
                vals['payslip_run_id'])
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            period = payslip_run.hr_period_id
            vals['date_payment'] = payslip_run.date_payment
            vals['hr_period_id'] = period.id
            vals['name'] = _('Salary Slip of %s for %s') % (
                employee.name, period.name)
        elif vals.get('date_to') and not vals.get('date_payment'):
            vals['date_payment'] = vals['date_to']
            # print "------222--------"
        return super(HrPayslip, self).create(vals)


    # @api.onchange('employee_id', 'date_from', 'date_to')
    # def onchange_employee(self):
    #
    #     if (not self.employee_id) or (not self.date_from) or (not self.date_to):
    #         return
    #
    #     employee = self.employee_id
    #     date_from = self.date_from
    #     date_to = self.date_to
    #
    #     ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_to, "%Y-%m-%d")))
    #     locale = self.env.context.get('lang', 'en_US')
    #     self.name = _('Salary Slip of %s for %s') % (
    #     employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
    #     self.company_id = employee.company_id
    #
    #     if not self.env.context.get('contract') or not self.contract_id:
    #         contract_ids = self.get_contract(employee, date_from, date_to)
    #         if not contract_ids:
    #             return
    #         self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
    #
    #     if not self.contract_id.struct_id:
    #         return
    #     self.struct_id = self.contract_id.struct_id
    #
    #     # computation of the salary input
    #     worked_days_line_ids = self.get_worked_day_lines(contract_ids, date_from, date_to)
    #     worked_days_lines = self.worked_days_line_ids.browse([])
    #     for r in worked_days_line_ids:
    #         worked_days_lines += worked_days_lines.new(r)
    #     self.worked_days_line_ids = worked_days_lines
    #
    #     input_line_ids = self.get_inputs(contract_ids, date_from, date_to)
    #     input_lines = self.input_line_ids.browse([])
    #     for r in input_line_ids:
    #         input_lines += input_lines.new(r)
    #     self.input_line_ids = input_lines
    #     return