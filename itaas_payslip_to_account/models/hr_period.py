# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
import time
from odoo.exceptions import UserError

class Hr_period_account_journal(models.Model):
    _inherit = "hr.period"

    journal_id  = fields.Many2one('account.journal',string="Journal")
    move_id = fields.Many2one('account.move',string="Journal Entry")

    def action_to_account(self):
        print('action_to_account')
        check_department = []
        all_department = []
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        total_debit = 0
        total_credit = 0
        sum_total = 0
        if not  self.move_id:
            for line in self.payslip_ids:
                if line.state != 'done':
                    raise UserError(_('Payslip ยังไม่อยู่ใน state Done.'))
                else:
                    if line.department_id and line.department_id.id not in check_department:
                        check_department.append(line.department_id.id)
        else:
            raise UserError(_('รายการได้มีการ Post ไปแล้ว'))
        params = (tuple(check_department),self.id)
        print('params:',params)
        query = """SELECT aml.department_id,aml.salary_rule_id,sum(aml.total)
                    FROM hr_payslip_line AS aml 
                    JOIN hr_salary_rule r ON aml.salary_rule_id = r.id
                    JOIN hr_payslip k ON aml.slip_id = k.id
                    WHERE aml.department_id IS NOT NULL and aml.department_id IN %s and r.account_id IS NOT NULL and k.hr_period_id = %s
                    GROUP BY aml.department_id,aml.salary_rule_id
                    """
        self.env.cr.execute(query, params)
        res = self.env.cr.fetchall()
        print('res:',res)
        all_list = []
        for line in res:
            hr_rule = self.env['hr.salary.rule'].search([('id', '=', line[1])])
            if hr_rule not in all_list:
                all_list.append(hr_rule)
            hr_department = self.env['hr.department'].search([('id', '=', line[0])])
            credit = abs(line[2])
            sum_total += abs(credit)
            if hr_rule.credit:

                total_credit += abs(credit)
                all_department.append((0, 0, {
                    'account_id': hr_rule.account_id.id,
                    'department_id': hr_department.id,
                    'name': hr_rule.name,
                    'credit': credit,
                    'debit': 0,
                }))
            else:

                total_debit += abs(credit)
                all_department.append((0, 0, {
                    'account_id': hr_rule.account_id.id,
                    'department_id': hr_department.id,
                    'name': hr_rule.name,
                    'credit': 0,
                    'debit': credit,
                }))

        sum_total = total_debit - total_credit
        if len(all_list) > 1:
            all_department.append((0, 0, {
                'account_id': self.journal_id.default_credit_account_id.id,
                'name':self.journal_id.default_credit_account_id.name,
                'department_id': False,
                'credit': sum_total,
                'debit': 0,
            }))
        elif len(all_list) == 1:
            all_department.append((0, 0, {
                'account_id': self.journal_id.default_credit_account_id.id,
                'name':self.journal_id.default_credit_account_id.name,
                'department_id': False,
                'credit': 0,
                'debit': total_credit or total_debit,
            }))
        vals ={
            'date': self.date_payment,
            'journal_id': self.journal_id.id,
            'ref': self.name,
            'line_ids': all_department
        }
        account_move = account_move_obj.create(vals)
        self.move_id = account_move
        account_move.post()
        print('account_move:',account_move)




