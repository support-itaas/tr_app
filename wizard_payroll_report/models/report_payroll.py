# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models,_
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError



class ProductTemplateCostStructure(models.AbstractModel):
    _name = 'report.wizard_payroll_report.payroll_salary_report'

    @api.model
    def get_report_values(self, docids, data=None):
        print('get_report_values:')
        print('data:',data)
        line_payslip = []
        t1 = 0.00
        count = 0
        company = self.env.user.company_id
        print('data:',data['form']['period_id'])
        hr_payslip_ids = self.env['hr.payslip'].search([('hr_period_id.id', '=', data['form']['period_id'][0]),
                                                        ('contract_id.struct_id', '=', data['form']['salary_struct'][0]),
                                                        ('contract_id.con_branch_id', '=', data['form']['con_branch_id'][0]),
                                                        ('employee_id.operating_unit_id', '=', data['form']['operating_unit'][0]),

                                                        ])
        print('hr_payslip_ids:',hr_payslip_ids)
        temp_all = []
        if not hr_payslip_ids:
            raise UserError(_("ไม่พบรายการ"))

        date_payment = hr_payslip_ids[0].date_payment
        date_today = datetime.today()
        date_today= date_today.strftime('%Y-%m-%d')
        rule_ids = hr_payslip_ids[0].struct_id.rule_ids.filtered(lambda x: x.check_active == True)
        rule_ids = rule_ids.sorted(key=lambda p: p.sequence)
        for payslip_id in hr_payslip_ids.filtered(lambda x: x.details_by_salary_rule_category):
            print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
            period = self.env['hr.period'].search([('id', '=', payslip_id.hr_period_id.id)])
            temp_val = []
            temp_val.append(payslip_id.employee_id.employee_code)
            temp_val.append(payslip_id.employee_id.name)
            temp_val.append(payslip_id.employee_id.job_id.code)
            temp_val.append(period.number)
            temp_val.append(payslip_id.hr_period_id.date_end)
            # ========================================
            payslip_line_ids = payslip_id.details_by_salary_rule_category.filtered(lambda x: x.salary_rule_id.check_active == True)
            payslip_line_ids = payslip_line_ids.sorted(key=lambda p: p.salary_rule_id.sequence)
            print('payslip_line_ids:',payslip_line_ids)
            for line_ids in payslip_line_ids:
                print('line_ids_seq:',line_ids.sequence)
                print('line_ids_seq:',line_ids.name)
                if line_ids.total:
                    count += 1
                    temp_val.append(line_ids.total)
                else:
                    count += 1
                    temp_val.append(t1)
            temp_all.append(temp_val)
            print('temp_all:',temp_all)
            print('count:',count)
            print('len(temp_all)',len(temp_all))
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': temp_all,
            'total_count': count,
            'rule_ids': rule_ids,
            'company': company,
            'date_payment': date_payment,
            'date_today': date_today,

        }



