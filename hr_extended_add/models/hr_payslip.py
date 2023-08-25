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

class hr_contract(models.Model):
    _inherit = "hr.contract"

    is_manager = fields.Boolean("ไม่คำนวณ ขาด/ลา/มาสาย")

    total_revenue_summary_for_tax_one = fields.Float(string='รายได้ไม่คงที่สำหรับคิดภาษีบุคคลธรรมดาสะสม')
    total_tax_one_paid = fields.Float(string='ภาษีหักสะสม รายได้ไม่คงที่')

class hr_payslip(models.Model):
    _inherit = "hr.payslip"

    deduct02_man = fields.Float(default='0.00',string='deduct02 man')
    total_wage_man = fields.Float(string='Total Wage man')
    is_manual_salary = fields.Boolean(string='Manual Salary')

    summary_for_tax_one = fields.Float(string='รายได้ไม่คงที่สำหรับคิดภาษีบุคคลธรรมดา' ,copy=False)
    total_revenue_summary_for_tax_one = fields.Float(string='รายได้ไม่คงที่สำหรับคิดภาษีบุคคลธรรมดาสะสม', related='contract_id.total_revenue_summary_for_tax_one',copy=False)
    tax_one_paid = fields.Float(string='ภาษี หัก ณ ที่จ่ายรายได้ไม่คงที่', copy=False)
    total_tax_one_paid = fields.Float(string='ภาษีหักสะสม รายได้ไม่คงที่', related='contract_id.total_tax_one_paid',copy=False)

    is_sso = fields.Boolean(string='Get SSO', compute='_get_sso')
    is_tax = fields.Boolean(string='Get Tax', compute='_get_tax')


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        print('dup compute_sheet')
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            # slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            # print('slip_data : ', slip_data)
            contract_ids = self.get_contract(employee, from_date, to_date)
            print('employee : ',employee)
            print('contract_ids : ',contract_ids)
            if contract_ids:
                contract = contract_ids[0]
                res = {
                    'employee_id': employee.id,
                    # 'name': slip_data['value'].get('name'),
                    # 'struct_id': slip_data['value'].get('struct_id'),
                    # 'contract_id': slip_data['value'].get('contract_id'),
                    'contract_id': contract,
                    'payslip_run_id': active_id,
                    # 'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                    # 'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                    'date_from': from_date,
                    'date_to': to_date,
                    'credit_note': run_data.get('credit_note'),
                    'company_id': employee.company_id.id,
                }
                print('res : ', res)
                payslip = self.env['hr.payslip'].create(res)
                payslip.onchange_employee()
                print('payslip contract_id',payslip.contract_id)
                payslips += payslip
        print('payslips : ', payslips)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}

    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids