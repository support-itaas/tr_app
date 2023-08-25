# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math

from odoo import api, models, _
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)

def roundup(x):
    return int(math.ceil(x / 10.0)) * 10
def roundupto(x):
    return int(math.ceil(x / 8.0)) * 8
def roundupto1(x):
    return int(math.ceil(x / 7.0)) * 7

class sps1_10_1_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.sps1_10_1_period_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company': company,
            'company_bank': company.bank_ac,
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city' : company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
        }

    def _get_total_salary(self,company_id,period_id,wage_type,con_branch_id):

        sum_salary = 0
        sum_sso_employee = 0
        sum_sso_employee_2 = 0
        sum_sso_no_employee = 0
        employee_ids = []

        domain = []
        # domain.append(('company_id', '=', company_id[0]))
        domain.append(('id', '=', period_id[0]))
        period_id = self.env['hr.period'].search(domain)

        if period_id:
            if con_branch_id:
                period_id_payslip_ids = period_id.payslip_ids.filtered(
                    lambda x: x.contract_id.con_branch_id.id == con_branch_id[0] and x.state == 'done' and x.deduct09)
            else:
                period_id_payslip_ids = period_id.payslip_ids.filtered(lambda x: x.state == 'done' and x.deduct09)
            if wage_type:
                period_id_payslip_ids = period_id_payslip_ids.filtered(
                    lambda x: x.contract_id.wage_type == wage_type)
            for line in period_id_payslip_ids:
                # if wage_type:
                #     if line.contract_id.wage_type == wage_type:
                #         sum_sso_employee += line.deduct09
                #         sum_salary += line.total_wage
                #         if line.employee_id.id not in employee_ids:
                #             employee_ids.append(line.employee_id.id)
                #             sum_sso_no_employee += 1
                # else:
                sum_sso_employee += line.deduct09
                sum_salary += line.sum_total_sso
                if line.employee_id.id not in employee_ids:
                    employee_ids.append(line.employee_id.id)
                    sum_sso_no_employee += 1
        else:
            sum_salary = 0
            sum_sso_employee = 0
            sum_sso_no_employee = 0

        sum_sso_employee_2 = sum_sso_employee * 2

        return {
            'sum_salary': sum_salary,
            'sum_sso_employee': sum_sso_employee,
            'sum_sso_employee_2': sum_sso_employee_2,
            'sum_sso_no_employee': sum_sso_no_employee,
        }

    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'])
        salary_info = self._get_total_salary(data['form']['company_id'], data['form']['period_id'],data['form']['wage_type'],data['form']['con_branch_id'])
        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.period'].search([('company_id','=',data['form']['company_id'][0]),('id','=',data['form']['period_id'][0])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
        }


class sps1_10_2_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.sps1_10_2_period_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_bank': company.bank_ac,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city': company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
        }

    def _get_total_salary(self, company_id, period_id, wage_type,con_branch_id ):
        sum_salary = 0
        sum_sso_employee = 0
        sum_sso_no_employee = 0
        employee_ids = []

        domain = []
        domain.append(('company_id', '=', company_id[0]))
        domain.append(('id', '=', period_id[0]))
        period_id = self.env['hr.period'].search(domain)

        if period_id:
            if con_branch_id:
                period_id_payslip_ids = period_id.payslip_ids.filtered(lambda x: x.contract_id.con_branch_id.id == con_branch_id[0] and x.state == 'done' and x.deduct09)
            else:
                period_id_payslip_ids = period_id.payslip_ids.filtered(lambda x: x.state == 'done' and x.deduct09)
            if wage_type:
                period_id_payslip_ids = period_id_payslip_ids.filtered(
                    lambda x: x.contract_id.wage_type == wage_type)
            for line in period_id_payslip_ids:
                # if wage_type:
                #     if line.contract_id.wage_type == wage_type:
                #         sum_sso_employee += line.deduct09
                #         sum_salary += line.total_wage
                #         if line.employee_id.id not in employee_ids:
                #             employee_ids.append(line.employee_id.id)
                #             sum_sso_no_employee += 1
                # else:
                sum_sso_employee += line.deduct09
                sum_total_sso = sum(line.line_ids.filtered(lambda x: x.salary_rule_id.cal_sso).mapped('total'))
                sum_salary += sum_total_sso
                # sum_salary += line.sum_total_sso
                if line.employee_id.id not in employee_ids:
                    employee_ids.append(line.employee_id.id)
                    sum_sso_no_employee += 1
        else:
            sum_salary = 0
            sum_sso_employee = 0
            sum_sso_no_employee = 0


        return {
            'sum_salary': sum_salary,
            'sum_sso_employee': sum_sso_employee,
            'sum_sso_no_employee': sum_sso_no_employee,
            'sum_sso_no_employee_10': roundup(sum_sso_no_employee),
        }

    def _get_period_line(self,company_id,period_id,wage_type,con_branch_id):

        period_line_s = []
        period_line = []
        i = 0
        domain = []
        domain.append(('company_id', '=', company_id[0]))
        domain.append(('id', '=', period_id[0]))
        period_id = self.env['hr.period'].search(domain)
        if period_id:
            if con_branch_id:
                period_id_payslip_ids = period_id.payslip_ids.filtered(lambda x: x.contract_id.con_branch_id.id == con_branch_id[0] and x.state == 'done' and x.deduct09)
            else:
                period_id_payslip_ids = period_id.payslip_ids.filtered(lambda x: x.state == 'done' and x.deduct09)
            if wage_type:
                period_id_payslip_ids = period_id_payslip_ids.filtered(lambda x: x.contract_id.wage_type == wage_type)
            for line in period_id_payslip_ids.sorted(lambda x: x.number):
                print('number : ',line.number)
                employee_id = line.employee_id.id
                if employee_id not in period_line:
                    val = {
                        'employee_id': line.employee_id,
                        'identification': line.employee_id.identification_id,
                        'name': line.employee_id.name,
                        'title': line.employee_id.title.name,
                        'first_name': line.employee_id.first_name,
                        'last_name': line.employee_id.last_name,
                        'sum_total_tax': line.sum_total_tax,
                        'tax_paid': line.tax_paid,
                        'sum_total_sso': line.sum_total_sso,
                        'total_sso': line.deduct09,
                    }
                    period_line.append(employee_id)
                    period_line_s.append(val)
                else:
                    index = period_line.index(employee_id)
                    period_line_s[index]['sum_total_tax'] += line.sum_total_tax
                    period_line_s[index]['tax_paid'] += line.tax_paid
                    period_line_s[index]['total_sso'] += line.deduct09

        # period_line_s = [value for key, value in period_line_s.items()]
        return period_line_s


    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'])
        salary_info = self._get_total_salary(data['form']['company_id'],data['form']['period_id'],data['form']['wage_type'],data['form']['con_branch_id'])
        period_info = self._get_period_line(data['form']['company_id'],data['form']['period_id'],data['form']['wage_type'],data['form']['con_branch_id'])

        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.period'].search([('company_id','=',data['form']['company_id'][0]),('id','=',data['form']['period_id'][0])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
            'get_period_info' : period_info,
            'num_page': int(math.ceil((len(period_info) / 10))),
        }


class pd1_1_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.pd_1_1_report_period_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city' : company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
        }

    def _get_total_salary(self,company_id,period_id,wage_type):
        sum_salary = 0
        sum_tax_employee = 0
        sum_tax_no_employee = 0
        employee = []
        domain = []
        domain.append(('company_id', '=', company_id[0]))
        domain.append(('id', '=', period_id[0]))
        # print('domain : ',domain)
        period_id = self.env['hr.period'].search(domain)

        # print('payslip_ids : ', len(period_id.payslip_ids))
        if wage_type:
            payslip_ids = period_id.payslip_ids.filtered(
                lambda x: x.contract_id.wage_type == wage_type and x.state == 'done')
            # print('payslip_ids wage_type: ', len(payslip_ids))
        else:
            payslip_ids = period_id.payslip_ids.filtered(lambda x: x.state == 'done')
            # print('payslip_ids not wage_type: ', len(payslip_ids))
        employee = []
        if payslip_ids:
            employee = payslip_ids.mapped('employee_id').ids
            sum_salary = sum(payslip_ids.mapped('sum_total_tax')) + sum(payslip_ids.mapped('summary_for_tax_one'))
            sum_tax_employee = sum(payslip_ids.mapped('deduct02'))
            sum_tax_no_employee = len(employee)

        return {
            'sum_salary': sum_salary,
            'sum_tax_employee': sum_tax_employee,
            'sum_tax_no_employee': sum_tax_no_employee,
            'num_page': int(math.ceil((len(employee) / 8))),
        }

    @api.multi
    def get_report_values(self, docids, data=None):
        # print('report.report_hr.pd_1_1_report_period_id')
        header_info = self.env['res.company'].browse(data['form']['company_id'][0])
        salary_info = self._get_total_salary(data['form']['company_id'],data['form']['period_id'],data['form']['wage_type'])

        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.period'].search([('company_id','=',data['form']['company_id'][0]),('id','=',data['form']['period_id'][0])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
        }


class pd1_2_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.pd_1_2_report_period_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city' : company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
        }

    def _get_period_line(self,company_id,period_id,wage_type):
        period_line_s = []
        domain = []
        domain.append(('company_id', '=', company_id[0]))
        domain.append(('id', '=', period_id[0]))
        # print('domain : ',domain)
        period_id = self.env['hr.period'].search(domain)

        # print('payslip_ids : ', len(period_id.payslip_ids))
        if wage_type:
            payslip_ids = period_id.payslip_ids.filtered(lambda x: x.contract_id.wage_type == wage_type and x.state == 'done')
            # print('payslip_ids wage_type: ', len(payslip_ids))
        else:
            payslip_ids = period_id.payslip_ids.filtered(lambda x: x.state == 'done')
            # print('payslip_ids not wage_type: ', len(payslip_ids))

        employee = []
        if payslip_ids:
            employee = payslip_ids.mapped('employee_id')
            for emp_id in employee:
                emp_payslip_ids = payslip_ids.filtered(lambda x: x.employee_id.id == emp_id.id)
                val_pay = {
                    'employee_id': emp_id,
                    'identification': emp_id.identification_id,
                    'name': emp_id.name,
                    'title': emp_id.title.name,
                    'first_name': emp_id.first_name,
                    'last_name': emp_id.last_name,
                    'sum_total_tax': sum(emp_payslip_ids.mapped('sum_total_tax')) + sum(emp_payslip_ids.mapped('summary_for_tax_one')),
                    'total_tax': sum(emp_payslip_ids.mapped('deduct02')),
                    'tax_paid': sum(emp_payslip_ids.mapped('tax_paid')),
                    'total_sso': sum(emp_payslip_ids.mapped('deduct09')),
                }
                period_line_s.append(val_pay)
        else:
            raise UserError(_('Document is empty.'))

        return period_line_s

    @api.multi
    def get_report_values(self, docids, data=None):
        # print('report.report_hr.pd_1_2_report_period_id')
        header_info = self._get_header_info(data['form']['company_id'])
        period_info = self._get_period_line(data['form']['company_id'], data['form']['period_id'], data['form']['wage_type'])

        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.period'].search([('company_id','=',data['form']['company_id'][0]),('id','=',data['form']['period_id'][0])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_period_info' : period_info,
            'num_page' : int(math.ceil((len(period_info)/8))),
        }


class pngd_1kor_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.pngd_1kor_report_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city' : company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
        }

    def _get_total_salary(self,company_id,fiscal_id,wage_type):
        sum_salary = 0.0
        sum_tax_employee = 0.0
        sum_tax_no_employee = 0.0
        domain = [('company_id', '=', company_id[0]), ('id', '=', fiscal_id[0])]
        fiscalyear_id = self.env['hr.fiscalyear'].search(domain)

        if wage_type:
            payslip_ids = fiscalyear_id.period_ids.mapped('payslip_ids').filtered(lambda x: x.state == 'done' and x.employee_id.wage_type == wage_type)
        else:
            payslip_ids = fiscalyear_id.period_ids.mapped('payslip_ids').filtered(lambda x: x.state == 'done')

        if payslip_ids:
            sum_salary = sum(payslip_ids.mapped('sum_total_tax')) + sum(payslip_ids.mapped('summary_for_tax_one'))
            sum_tax_employee = sum(payslip_ids.mapped('deduct02'))
            sum_tax_no_employee = len(payslip_ids.mapped('employee_id'))
        else:
            sum_salary = 0.0
            sum_tax_employee = 0.0
            sum_tax_no_employee = 0.0

        return {
            'sum_salary': sum_salary,
            'sum_tax_employee': sum_tax_employee,
            'sum_tax_no_employee': sum_tax_no_employee,
        }

    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'])
        salary_info = self._get_total_salary(data['form']['company_id'],data['form']['fiscal_id'],data['form']['wage_type'])

        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.fiscalyear'].search([('company_id','=',data['form']['company_id'][0]),('id','=',data['form']['fiscal_id'][0])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
        }


class pngd_1kor_nap_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.pngd_1kor_nap_report_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city' : company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
        }

    def _get_total_salary(self,company_id,fiscal_id,wage_type):
        sum_salary = 0.0
        sum_tax_employee = 0.0
        sum_tax_no_employee = 0.0
        domain = [('company_id', '=', company_id[0]),('id', '=', fiscal_id[0])]
        fiscalyear_id = self.env['hr.fiscalyear'].search(domain)

        if wage_type:
            payslip_ids = fiscalyear_id.period_ids.mapped('payslip_ids').filtered(lambda x: x.state == 'done' and x.employee_id.wage_type == wage_type)
        else:
            payslip_ids = fiscalyear_id.period_ids.mapped('payslip_ids').filtered(lambda x: x.state == 'done')

        if payslip_ids:
            sum_salary = sum(payslip_ids.mapped('sum_total_tax')) + sum(payslip_ids.mapped('summary_for_tax_one'))
            sum_tax_employee = sum(payslip_ids.mapped('deduct02'))
            sum_tax_no_employee = len(payslip_ids.mapped('employee_id'))
        else:
            sum_salary = 0.0
            sum_tax_employee = 0.0
            sum_tax_no_employee = 0.0

        return {
            'sum_salary': sum_salary,
            'sum_tax_employee': sum_tax_employee,
            'sum_tax_no_employee': sum_tax_no_employee,
            'sum_tax_no_employee_7': roundupto1(sum_tax_no_employee),
        }

    def _get_period_line(self,company_id,fiscal_id,wage_type):
        period_line_s = {}
        payslip_ids = self.env['hr.payslip']
        i = 0

        domain = [('company_id', '=', company_id[0]), ('id', '=', fiscal_id[0])]
        fiscalyear_id = self.env['hr.fiscalyear'].search(domain)

        if wage_type:
            payslip_ids = fiscalyear_id.period_ids.mapped('payslip_ids').filtered(lambda x: x.state == 'done' and x.contract_id.wage_type == wage_type)
        else:
            payslip_ids = fiscalyear_id.period_ids.mapped('payslip_ids').filtered(lambda x: x.state == 'done')

        period_line_s = []
        employee_ids = payslip_ids.mapped('employee_id')
        if employee_ids:
            for emp in employee_ids:
                employee_payslip_id = payslip_ids.filtered(lambda x: x.employee_id == emp)
                val = {
                    'employee_id': emp,
                    'identification': emp.identification_id,
                    'name': emp.name,
                    'title': emp.title.name,
                    'first_name': emp.first_name,
                    'last_name': emp.last_name,
                    'home_address': emp.home_address,
                    'sum_total_tax': sum(employee_payslip_id.mapped('sum_total_tax')) + sum(employee_payslip_id.mapped('summary_for_tax_one')),
                    'total_tax': sum(employee_payslip_id.mapped('deduct02')),
                    'tax_paid': sum(employee_payslip_id.mapped('tax_paid')),
                    'total_sso': sum(employee_payslip_id.mapped('deduct09'))
                }
                period_line_s.append(val)

        return period_line_s

    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'])
        salary_info = self._get_total_salary(data['form']['company_id'], data['form']['fiscal_id'], data['form']['wage_type'])
        period_info = self._get_period_line(data['form']['company_id'], data['form']['fiscal_id'], data['form']['wage_type'])
        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.period'].search([('company_id','=',data['form']['company_id'][0]),('id','=',data['form']['fiscal_id'][0])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
            'get_period_info' : period_info,
        }


class kortor20kor_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.kortor20kor_report_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city' : company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'company_registry': company.company_registry,
        }

    def _get_total_salary(self, company_id, fiscal_id, wage_type):

        sum_total_daily = 0
        sum_total_monthly = 0
        sum_total_other = 0
        sum_total_ot = 0
        sum_total_bonut = 0
        sum_total_saraly = 0
        sum_more_20 = 0
        sum_total = 0
        sum_sso_no_employee = 0

        employee_ids = []
        payslip_ids = []

        domain = []
        domain.append(('company_id', '=', company_id[0]))
        domain.append(('id', '=', fiscal_id[0]))
        fiscalyear_id = self.env['hr.fiscalyear'].search(domain)

        if fiscalyear_id:
            for fisc in fiscalyear_id.period_ids:
                if fisc.payslip_ids:
                    for slip in fisc.payslip_ids:
                        # if slip.state == 'done':
                        payslip_ids.append(slip)

        if payslip_ids:
            for line in payslip_ids:
                if wage_type:
                    if wage_type == 'daily':
                        if line.employee_id.id not in employee_ids:
                            employee_ids.append(line.employee_id.id)
                            sum_sso_no_employee += 1
                        for rule in line.details_by_salary_rule_category:
                            if rule.code == 'NET':
                                sum_total_saraly += rule.total
                        if line.total_wage > 20000:
                            sum_more_20 += (line.total_wage - 20000)

                        sum_total_daily += line.total_wage
                        sum_total_ot += line.overtime
                        sum_total_bonut += line.allow11
                        sum_total_other += (line.allow11 + line.overtime)

                    elif wage_type == 'monthly':
                        if line.employee_id.id not in employee_ids:
                            employee_ids.append(line.employee_id.id)
                            sum_sso_no_employee += 1
                        for rule in line.details_by_salary_rule_category:
                            if rule.code == 'NET':
                                sum_total_saraly += rule.total
                        if line.total_wage > 20000:
                            sum_more_20 += (line.total_wage - 20000)

                        sum_total_monthly += line.total_wage
                        sum_total_ot += line.overtime
                        sum_total_bonut += line.allow11
                        sum_total_other += (line.allow11 + line.overtime)
                else:
                    if line.contract_id.wage_type == 'daily':
                        if line.employee_id.id not in employee_ids:
                            employee_ids.append(line.employee_id.id)
                            sum_sso_no_employee += 1
                        for rule in line.details_by_salary_rule_category:
                            if rule.code == 'NET':
                                sum_total_saraly += rule.total
                        if line.total_wage > 20000:
                            sum_more_20 += (line.total_wage - 20000)

                        sum_total_daily += line.total_wage
                        sum_total_ot += line.overtime
                        sum_total_bonut += line.allow11
                        sum_total_other += (line.allow11 + line.overtime)


                    elif line.contract_id.wage_type == 'monthly':
                        if line.employee_id.id not in employee_ids:
                            employee_ids.append(line.employee_id.id)
                            sum_sso_no_employee += 1
                        for rule in line.details_by_salary_rule_category:
                            if rule.code == 'NET':
                                sum_total_saraly += rule.total
                        if line.total_wage > 20000:
                            sum_more_20 += (line.total_wage - 20000)

                        sum_total_monthly += line.total_wage
                        sum_total_ot += line.overtime
                        sum_total_bonut += line.allow11
                        sum_total_other += (line.allow11 + line.overtime)


        sum_total = (sum_total_saraly - sum_more_20)

        return {
            'sum_total_daily': sum_total_daily,
            'sum_total_monthly': sum_total_monthly,
            'sum_total_other': sum_total_other,
            'sum_total_ot': sum_total_ot,
            'sum_total_bonut': sum_total_bonut,
            'sum_total_saraly': sum_total_saraly,
            'sum_more_20': sum_more_20,
            'sum_total': sum_total,
            'sum_sso_no_employee': sum_sso_no_employee,
        }

    def _get_period_line(self, company_id, fiscal_id, wage_type):

        period_line_s = {}
        i = 0

        domain = []
        domain.append(('company_id', '=', company_id[0]))
        domain.append(('id', '=', fiscal_id[0]))
        fiscalyear_id = self.env['hr.fiscalyear'].search(domain)

        if fiscalyear_id:
            for period in fiscalyear_id.period_ids:
                employee_ids = []
                sum_sso_no_employee = 0
                sum_total_saraly = 0
                sum_more_20 = 0
                sum_total_daily = 0
                sum_total_monthly = 0
                sum_total_other = 0
                sum_total = 0
                for line in period.payslip_ids:
                    if wage_type:
                        if wage_type == 'daily':
                            if line.employee_id.id not in employee_ids:
                                employee_ids.append(line.employee_id.id)
                                sum_sso_no_employee += 1
                            sum_total_daily = line.total_wage
                            for rule in line.details_by_salary_rule_category:
                                if rule.code == 'NET':
                                    sum_total_saraly += rule.total
                            if line.total_wage > 20000:
                                sum_more_20 += (line.total_wage - 20000)
                            sum_total_other = (line.allow11 + line.overtime)
                            sum_total = (sum_total_saraly - sum_more_20)


                        elif wage_type == 'monthly':
                            if line.employee_id.id not in employee_ids:
                                employee_ids.append(line.employee_id.id)
                                sum_sso_no_employee += 1
                            sum_total_monthly += line.total_wage
                            for rule in line.details_by_salary_rule_category:
                                if rule.code == 'NET':
                                    sum_total_saraly += rule.total
                            if line.total_wage > 20000:
                                sum_more_20 += (line.total_wage - 20000)
                            sum_total_other = (line.allow11 + line.overtime)
                            sum_total = (sum_total_saraly - sum_more_20)
                    else:
                        if line.contract_id.wage_type == 'daily':
                            if line.employee_id.id not in employee_ids:
                                employee_ids.append(line.employee_id.id)
                                sum_sso_no_employee += 1
                            sum_total_daily = line.total_wage
                            for rule in line.details_by_salary_rule_category:
                                if rule.code == 'NET':
                                    sum_total_saraly += rule.total
                            if line.total_wage > 20000:
                                sum_more_20 += (line.total_wage - 20000)
                            sum_total_other = (line.allow11 + line.overtime)
                            sum_total = (sum_total_saraly - sum_more_20)


                        elif line.contract_id.wage_type == 'monthly':
                            if line.employee_id.id not in employee_ids:
                                employee_ids.append(line.employee_id.id)
                                sum_sso_no_employee += 1
                            sum_total_monthly += line.total_wage
                            for rule in line.details_by_salary_rule_category:
                                if rule.code == 'NET':
                                    sum_total_saraly += rule.total
                            if line.total_wage > 20000:
                                sum_more_20 += (line.total_wage - 20000)
                            sum_total_other = (line.allow11 + line.overtime)
                            sum_total = (sum_total_saraly - sum_more_20)

                period_line_s[i] = {
                    'sum_total_daily': sum_total_daily,
                    'sum_total_saraly': sum_total_saraly,
                    'sum_more_20': sum_more_20,
                    'sum_total_other': sum_total_other,
                    'sum_total': sum_total,
                    'sum_total_monthly': sum_total_monthly,
                    'sum_sso_no_employee': sum_sso_no_employee,
                }
                i += 1

        period_line_s = [value for key, value in period_line_s.items()]
        return period_line_s

    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'])
        salary_info = self._get_total_salary(data['form']['company_id'], data['form']['fiscal_id'], data['form']['wage_type'])
        period_info = self._get_period_line(data['form']['company_id'], data['form']['fiscal_id'], data['form']['wage_type'])
        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.period'].search(
                [('company_id', '=', data['form']['company_id'][0]), ('id', '=', data['form']['fiscal_id'][0])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info': salary_info,
            'get_period_info': period_info,
        }


class sps1_02_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.sps1_02_report_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city' : company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
            'company_registry': company.company_registry,
        }



    def _get_total_salary(self,company_id,wage_type):

        sum_sso_no_employee = 0

        domain = [('submit_sso','=',True),('end_sso','=',False)]
        if wage_type:
            domain.append(('wage_type', '=', wage_type))
        domain.append(('employee_id.company_id', '=', company_id[0]))
        contract_ids = self.env['hr.contract'].search(domain)

        if contract_ids:
            for line in contract_ids:
                sum_sso_no_employee += 1
        else:
            sum_sso_no_employee = 0


        return {
            'sum_sso_no_employee': sum_sso_no_employee,
        }


    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'])
        salary_info = self._get_total_salary(data['form']['company_id'],data['form']['wage_type'])

        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.contract'].search([('company_id','=',data['form']['company_id'][0]),('wage_type','=',data['form']['wage_type'])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
        }


class sps1_03_2_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.sps1_03_2_report_id'

    def _get_header_info(self, company_id,con_branch_id):
        company = self.env['res.company'].browse(company_id[0])
        con_branch = self.env['contract.branch'].browse(con_branch_id[0])
        # print('con_branch_id :', con_branch_id)
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city': company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
            'company_registry': company.company_registry,

            'con_branch_partner_name': con_branch.partner_id.name,
            'con_branch_ids': con_branch.name,
            'con_branch_description': con_branch.description,
            'con_branch_bank_ac': con_branch.bank_ac,
            # 'con_branch_eng_add': con_branch.eng_address,
            'con_branch_building': con_branch.building,
            'con_branch_roomnumber': con_branch.roomnumber,
            'con_branch_floornumber': con_branch.floornumber,
            'con_branch_village': con_branch.village,
            'con_branch_house_number': con_branch.house_number,
            'con_branch_moo_number': con_branch.moo_number,
            'con_branch_soi_number': con_branch.soi_number,
            'con_branch_street': con_branch.street,
            'con_branch_street2': con_branch.street2,
            'con_branch_tumbon': con_branch.tumbon,
            'con_branch_city': con_branch.city,
            'con_branch_province': con_branch.state_id.name,
            'con_branch_code': con_branch.zip,
            'con_branch_phone': con_branch.phone,
            # 'con_branch_email': con_branch.email,
        }


    def _get_total_salary(self, company_id, wage_type,date_from,date_to, con_branch_id):

        sum_sso_no_employee = 0

        domain = [('submit_sso','=',True),('end_sso','=',False)]
        if date_from:
            domain.append(('date_start', '>=', date_from))
        if date_to:
            domain.append(('date_start', '<=', date_to))
        if wage_type:
            domain.append(('wage_type', '=', wage_type))
        if con_branch_id:
            domain.append(('con_branch_id', '=', con_branch_id))
        domain.append(('company_id', '=', company_id[0]))
        contract_ids = self.env['hr.contract'].search(domain)

        if contract_ids:
            for line in contract_ids:
                sum_sso_no_employee += 1
        else:
            sum_sso_no_employee = 0

        return {
            'sum_sso_no_employee': sum_sso_no_employee,
            'sum_sso_no_employee_7': roundupto1(sum_sso_no_employee),
        }

    def _get_period_line(self,company_id,wage_type,date_from,date_to, con_branch_id):

        employee_line_s = {}
        i = 0

        domain = [('submit_sso','=',True),('end_sso','=',False)]
        if date_from:
            domain.append(('date_start', '>=', date_from))
        if date_to:
            domain.append(('date_start', '<=', date_to))
        if wage_type:
            domain.append(('wage_type', '=', wage_type))
        if con_branch_id:
            domain.append(('con_branch_id', '=', con_branch_id))
        domain.append(('company_id', '=', company_id[0]))
        contract_ids = self.env['hr.contract'].search(domain)

        if contract_ids:
            for line in contract_ids:
                employee_id = line.employee_id.id
                employee_vat = line.employee_id.identification_id
                employee_name = line.employee_id.name
                employee_title = line.employee_id.title.name
                employee_first = line.employee_id.first_name
                employee_last = line.employee_id.last_name
                employee_date = strToDate(line.date_start).strftime("%d/%m/%Y")
                if line.employee_id.fam_experience_ids:
                    employee_work = line.employee_id.fam_experience_ids[0].name
                else:
                    employee_work = ""

                if employee_id not in employee_line_s:
                    employee_line_s[employee_id] = {
                        'employee_id': employee_id,
                        'employee_name': employee_name,
                        'employee_vat': employee_vat,
                        'employee_title': employee_title,
                        'employee_first': employee_first,
                        'employee_last': employee_last,
                        'employee_work': employee_work,
                        'employee_date': employee_date,
                    }
                    i += 1

            employee_line_s = [value for key, value in employee_line_s.items()]
        return employee_line_s

    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'],data['form']['con_branch_id'])
        salary_info = self._get_total_salary(data['form']['company_id'],data['form']['wage_type'],data['form']['date_from'],data['form']['date_to'],data['form']['con_branch_id'])
        period_info = self._get_period_line(data['form']['company_id'],data['form']['wage_type'],data['form']['date_from'],data['form']['date_to'],data['form']['con_branch_id'])
        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.contract'].search([('company_id','=',data['form']['company_id'][0]),('wage_type','=',data['form']['wage_type'])]),
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
            'get_period_info' : period_info,
        }

class sps6_09_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.sps6_09_report_id'

    def _get_header_info(self, company_id,con_branch_id):
        company = self.env['res.company'].browse(company_id[0])
        con_branch = self.env['contract.branch'].browse(con_branch_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city': company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'con_branch_name': company.branch_no,
            'company_registry': company.company_registry,

            'con_branch_partner_name': con_branch.partner_id.name,
            'con_branch_ids': con_branch.name,
            'con_branch_description': con_branch.description,
            'con_branch_bank_ac': con_branch.bank_ac,
            # 'con_branch_eng_add': con_branch.eng_address,
            'con_branch_building': con_branch.building,
            'con_branch_roomnumber': con_branch.roomnumber,
            'con_branch_floornumber': con_branch.floornumber,
            'con_branch_village': con_branch.village,
            'con_branch_house_number': con_branch.house_number,
            'con_branch_moo_number': con_branch.moo_number,
            'con_branch_soi_number': con_branch.soi_number,
            'con_branch_street': con_branch.street,
            'con_branch_street2': con_branch.street2,
            'con_branch_tumbon': con_branch.tumbon,
            'con_branch_city': con_branch.city,
            'con_branch_province': con_branch.state_id.name,
            'con_branch_code': con_branch.zip,
            'con_branch_phone': con_branch.phone,
            # 'con_branch_email': con_branch.email,
        }

    def _get_total_salary(self, company_id, wage_type,date_from,date_to,con_branch_id):

        sum_sso_no_employee = 0

        domain = [('end_sso', '!=', False)]
        domain.append(('employee_id.company_id', '=', company_id[0]))
        if date_from:
            domain.append(('date_end', '>=', date_from))
        if date_to:
            domain.append(('date_end', '<=', date_to))
        if wage_type:
            domain.append(('wage_type', '=', wage_type))
        if con_branch_id:
            domain.append(('con_branch_id', '=', con_branch_id))
        domain.append(('company_id', '=', company_id[0]))
        contract_ids = self.env['hr.contract'].search(domain)
        if contract_ids:
            for line in contract_ids:
                sum_sso_no_employee += 1
        else:
            sum_sso_no_employee = 0

        return {
            'sum_sso_no_employee': sum_sso_no_employee,
            'sum_sso_no_employee_7': roundupto1(sum_sso_no_employee),
        }

    def _get_period_line(self,company_id,wage_type,date_from,date_to,con_branch_id):

        employee_line_s = {}
        i = 0

        domain = [('end_sso', '!=', False)]
        domain.append(('employee_id.company_id', '=', company_id[0]))
        if date_from:
            domain.append(('date_end', '>=', date_from))
        if date_to:
            domain.append(('date_end', '<=', date_to))
        if wage_type:
            domain.append(('wage_type', '=', wage_type))
        if con_branch_id:
            domain.append(('con_branch_id', '=', con_branch_id))
        domain.append(('company_id', '=', company_id[0]))
        contract_ids = self.env['hr.contract'].search(domain)
        print('contract_ids :', contract_ids)

        if contract_ids:
            for line in contract_ids:
                employee_id = line.employee_id.id
                employee_vat = line.employee_id.identification_id
                employee_name = line.employee_id.name
                employee_title = line.employee_id.title.name
                employee_first = line.employee_id.first_name
                employee_last = line.employee_id.last_name
                employee_date = strToDate(line.date_end).strftime("%d/%m/%Y")
                end_sso = line.end_sso

                if employee_id not in employee_line_s:
                    employee_line_s[employee_id] = {
                        'employee_id': employee_id,
                        'employee_name': employee_name,
                        'employee_vat': employee_vat,
                        'employee_title': employee_title,
                        'employee_first': employee_first,
                        'employee_last': employee_last,
                        'employee_date': employee_date,
                        'end_sso': end_sso,
                    }
                    i += 1
            employee_line_s = [value for key, value in employee_line_s.items()]
            print('employee_line_s :', employee_line_s)
        return employee_line_s

    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'],data['form']['con_branch_id'])
        salary_info = self._get_total_salary(data['form']['company_id'],data['form']['wage_type'],data['form']['date_from'],data['form']['date_to'],data['form']['con_branch_id'])
        period_info = self._get_period_line(data['form']['company_id'],data['form']['wage_type'],data['form']['date_from'],data['form']['date_to'],data['form']['con_branch_id'])
        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.contract'],
            'data': data['form'],
            'get_header_info': header_info,
            'get_salary_info' : salary_info,
            'get_period_info' : period_info,
        }


class pvd_report_id_period(models.AbstractModel):
    _name = 'report.report_hr.pvd_report_id'

    def _get_header_info(self, company_id):
        company = self.env['res.company'].browse(company_id[0])
        return {
            'company_vat': company.vat,
            'company_branch': company.branch_no,
            'company_name': company.name,
            'company_eng_add': company.eng_address,
            'company_building': company.building,
            'company_roomnumber': company.roomnumber,
            'company_floornumber': company.floornumber,
            'company_village': company.village,
            'company_house_number': company.house_number,
            'company_moo_number': company.moo_number,
            'company_soi_number': company.soi_number,
            'company_street': company.street,
            'company_street2': company.street2,
            'company_tumbon': company.tumbon,
            'company_city': company.city,
            'company_province': company.state_id.name,
            'company_code': company.zip,
            'company_phone': company.phone,
            'company_email': company.email,
            'company_registry': company.company_registry,
        }

    def _get_period_line(self,company_id,date_from,date_to):

        employee_line_s = {}
        i = 0

        domain = [('wage_type','=','monthly')]
        domain.append(('employee_id.company_id', '=', company_id[0]))
        domain.append(('pvd_end_date', '=', False))

        if date_from:
            domain.append(('pvd_start_date', '>=', date_from))
        if date_to:
            domain.append(('pvd_start_date', '<=', date_to))

        contract_ids = self.env['hr.contract'].search(domain)

        if contract_ids:
            for line in contract_ids:
                employee_id = line.employee_id.id
                employee_vat = line.employee_id.identification_id
                employee_name = line.employee_id.name
                employee_code = line.employee_id.employee_code
                employee_title = line.employee_id.title.name
                employee_first = line.employee_id.first_name
                employee_last = line.employee_id.last_name
                employee_start_date = strToDate(line.date_start).strftime("%y/%m/%d")
                employee_pvd_date = line.pvd_start_date
                employee_wage = line.wage
                employee_pvd_rate = line.pvd_rate
                if employee_pvd_rate:
                    employee_pvd_amount = (employee_wage * employee_pvd_rate) / 100
                else:
                    employee_pvd_amount = 0

                if employee_id not in employee_line_s:
                    employee_line_s[employee_id] = {
                        'employee_id': employee_id,
                        'employee_name': employee_name,
                        'employee_code': employee_code,
                        'employee_vat': employee_vat,
                        'employee_title': employee_title,
                        'employee_first': employee_first,
                        'employee_last': employee_last,
                        'employee_start_date': employee_start_date,
                        'employee_pvd_date': employee_pvd_date,
                        'employee_wage': employee_wage,
                        'employee_pvd_rate': employee_pvd_rate,
                        'employee_pvd_amount': employee_pvd_amount,
                        'employee_pvd_tamount': (employee_pvd_amount * 2),
                    }
                    i += 1

            employee_line_s = [value for key, value in employee_line_s.items()]
        return employee_line_s

    @api.multi
    def get_report_values(self, docids, data=None):
        header_info = self._get_header_info(data['form']['company_id'])
        period_info = self._get_period_line(data['form']['company_id'],data['form']['date_from'],data['form']['date_to'])
        return {
            'doc_ids': docids,
            'doc_model': self.env['hr.contract'],
            'data': data['form'],
            'get_header_info': header_info,
            'get_period_info' : period_info,
        }


class teejai_50_all_report(models.AbstractModel):
    _name = 'report.report_hr.teejai_50_all_report_id'

    @api.multi
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        domain = []
        if docs.wage_type:
            domain.append(('wage_type', '=', docs.wage_type))
        if docs.con_branch_id:
            domain.append(('con_branch_id', '=', docs.con_branch_id.id))

        contract_ids = self.env['hr.contract'].search(domain)

        docargs = {
            'doc_ids': docids,
            'data': data['form'],
            'docs': docs,
            'fiscal_id': docs.fiscal_id,
            'year': datetime.strptime(docs.fiscal_id.date_start, DEFAULT_SERVER_DATE_FORMAT).year,
            'period_ids': docs.fiscal_id.period_ids,
            'contract_ids': contract_ids,
        }
        return docargs
