#-*-coding: utf-8 -*-

import time
from datetime import datetime, date
from datetime import time as datetime_time
from datetime import timedelta
# from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
import pytz
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT

from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

from odoo.tools import float_compare, float_is_zero, float_round
import math

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))


def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)


class hr_holidays_status(models.Model):
    _inherit = 'hr.holidays.status'

    allow_hr = fields.Boolean(string="อนุญาติให้ลาเป็นชั่วโมง")


class hr_salary_rule(models.Model):
    _inherit = "hr.salary.rule"

    cal_tax = fields.Boolean(string="คำนวนภาษีหรือไม่")
    cal_sso = fields.Boolean(string="คำนวณประกันสังคมหรือไม่")
    account_diff = fields.Many2one('account.account', string='Diff Account')


class hr_payslip_line(models.Model):
    _inherit = "hr.payslip.line"

    cal_tax = fields.Boolean(string="คำนวนภาษีหรือไม่",related='salary_rule_id.cal_tax')
    date_from = fields.Date(related='slip_id.date_from', string='Date From')
    date_to = fields.Date(related='slip_id.date_to', string='Date To')
    number = fields.Char(related='slip_id.number', string='Reference')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validate'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], 'Status', select=True, readonly=True, copy=False,related='slip_id.state',store=True)
    date_payment = fields.Date(related='slip_id.date_payment', string='Date of Payment')


class hr_payslip(models.Model):
    _inherit = "hr.payslip"

    #net and summary net
    total_net = fields.Float(string='รายได้สุทธิ', copy=False)
    total_revenue_summary_net = fields.Float(string='รายได้สุทธิสะสม',related='contract_id.total_revenue_summary_net',copy=False)

    #revenue_for_tax and summary_revenue_summary_for_tax
    revenue_summary_for_tax = fields.Float(string='รายได้สำหรับภาษี',copy=False)
    total_revenue_summary_for_tax = fields.Float(string='รายได้สำหรับภาษีสะสม',related='contract_id.total_revenue_summary_for_tax',copy=False)

    #total tax paid and total sso paid
    total_tax_paid = fields.Float(string='ภาษีหักสะสม',related='contract_id.total_tax_paid',copy=False)
    total_sso_paid = fields.Float(string='ประกันสังคมสะสม', related='contract_id.total_sso_paid', copy=False)
    salary_month_net = fields.Float(string='เงินเดือนสุทธิ', copy=False)
    tax_paid = fields.Float(string='ภาษี หัก ณ ที่จ่าย', copy=False)
    revenue_summary_for_tax = fields.Float(string='รายได้สำหรับคำนวนภาษี', copy=False)

    ############Income
    overtime = fields.Float(string='Over Time',default='0.00')
    allow01 = fields.Float(default='0.00')
    allow02 = fields.Float(string='เบี้ยเลี้ยง',default='0.00',digits=dp.get_precision('Account'))
    allow03 = fields.Float(default='0.00')
    allow04 = fields.Float(default='0.00')
    allow05 = fields.Float(default='0.00')
    allow06 = fields.Float(default='0.00')
    allow07 = fields.Float(default='0.00')
    allow08 = fields.Float(default='0.00')
    allow09 = fields.Float(default='0.00')
    allow10 = fields.Float(default='0.00')
    allow11 = fields.Float(default='0.00')
    allow12 = fields.Float(default='0.00')
    allow13 = fields.Float(default='0.00')
    allow14 = fields.Float(string='ค่าตำแหน่ง', default='0.00')
    allow15 = fields.Float(string='ค่าวิชาชีพ', default='0.00')
    allow16 = fields.Float(string='ค่าการจัดการ', default='0.00')
    allow17 = fields.Float(string='ค่าบำรุงรักษารถยนต์', default='0.00')
    allow18 = fields.Float(string='เงินพิเศษ', default='0.00')
    allow19 = fields.Float(string='ชดเชยวันหยุด', default='0.00')
    allow20 = fields.Float(string='เกษียณ', default='0.00')

    # allow15 = fields.Float(string='ค่าเช่าบ้าน', default='0.00')
    # allow16 = fields.Float(string='ค่าเบี้ยกันดาร', default='0.00')
    # allow18 = fields.Float(string='รางวัล safety', default='0.00')
    # allow19 = fields.Float(string='ปรับเงินเดือนย้อนหลัง', default='0.00')
    # allow20 = fields.Float(string='คืนเงินกู้ยืม', default='0.00')
    # allow21 = fields.Float(string='เงินพิเศษ', default='0.00')
    # allow23 = fields.Float(string='ค่าเบี้ยประกันภัย', default='0.00')
    # allow25 = fields.Float(string='ทำงานนอกสถานที่', default='0.00')
    # allow34 = fields.Float(string='ค่าครองชีพ', default='0.00')
    # allow35 = fields.Float(string='คืนเงินที่หักเกิน', default='0.00')


    ###### Expense
    deduct01 = fields.Float(default='0.00',string="เข้างานสาย")
    deduct02 = fields.Float(default='0.00',compute='_get_tax', store="True",readonly=False,digits=dp.get_precision('Account'))
    deduct03 = fields.Float(default='0.00')
    deduct04 = fields.Float(default='0.00')
    deduct05 = fields.Float(default='0.00')
    deduct06 = fields.Float(default='0.00')
    deduct07 = fields.Float(default='0.00')
    deduct08 = fields.Float(default='0.00')
    deduct09 = fields.Float(default='0.00',compute='_get_sso',store="True",readonly=False,digits=dp.get_precision('Account'))
    deduct10 = fields.Float(default='0.00')
    deduct11 = fields.Float(default='0.00')
    deduct12 = fields.Float(default='0.00')
    deduct13 = fields.Float(default='0.00')
    deduct14 = fields.Float(default='0.00')
    deduct15 = fields.Float(default='0.00',string="ทำงานไม่ครบเดือน")
    deduct16 = fields.Float(default='0.00',string="ค่าผ่อนของ")
    deduct17 = fields.Float(default='0.00',string="ขาดงาน")

    # deduct17 = fields.Float(string='หักขาดงาน', default='0.00')
    # deduct18 = fields.Float(string='หักคืนที่บ.จ่ายเกิน', default='0.00')
    # deduct19 = fields.Float(string='Advance', default='0.00')
    # deduct20 = fields.Float(string='หักเงินค่าอุปกรณ์', default='0.00')
    # deduct21 = fields.Float(string='Bank', default='0.00')
    # deduct22 = fields.Float(string='ภงด 3', default='0.00')
    # deduct23 = fields.Float(string='หักบังคับคดี', default='0.00')
    # deduct24 = fields.Float(string='หักคืนที่โอนแล้ว', default='0.00')
    #
    # deduct25 = fields.Float(string='ค่าเดินทางไปทำงาน', default='0.00')
    # deduct26 = fields.Float(string='ค่าเดินทางไปฝึกอบรม', default='0.00')
    # deduct27 = fields.Float(string='เบี้ยเลี้ยง stand by', default='0.00')
    # deduct28 = fields.Float(string='เบี้ยเลี้ยงฝึกอบรม', default='0.00')
    # deduct29 = fields.Float(string='เงินสมทบงวดปัจจุบัน', default='0.00')
    # deduct30 = fields.Float(string='เงินสะสมงวดปัจจุบัน(พนักงาน)', default='0.00')

    total_working_day = fields.Integer(string="Working day", compute='_get_working_day', store=True)
    total_month_day = fields.Integer(string="Month day", compute='_get_working_day', store=True)
    sum_total_tax = fields.Float(string='Sum Total Tax')
    total_wage = fields.Float(string='Total Wage')
    sum_total_sso = fields.Float(string='Sum Total SSO')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validate'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], 'Status', select=True, readonly=True, copy=False)

    is_full_year = fields.Boolean(string='Full Year',default=False)
    is_manual_tax = fields.Boolean(string='Manual Tax')
    is_manual_sso = fields.Boolean(string='Manual SSO')
    # is_wht = fields.Boolean(related='contract_id.is_wht', string='Withholding tax', store=True)

    calculate_tax = fields.Text(string='How to calculate tax.')

    benefit_line_ids = fields.One2many(
        'hr.payslip.benefit.line',
        'payslip_id',
        'Employee Benefits',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    @api.multi
    def _search_benefits(self):
        """
        Search employee benefits to be added on the payslip

        This method is meant to be inherited in other modules
        in order to add benefits from other sources.
        """
        self.ensure_one()
        return self.contract_id.benefit_line_ids

    @api.multi
    def button_compute_benefits(self):
        self.compute_benefits()

    @api.one
    def compute_benefits(self):
        """
        Compute the employee benefits on the payslip.

        This method can be called from inside a salary rule.

        Exemple
        -------
        payslip.compute_benefits()

        This is required when the benefits are based on the value
        of one or more salary rules.

        The module hr_employee_benefit_percent implements that
        functionnality.
        """
        for benefit_line in self.benefit_line_ids:
            if benefit_line.source == 'contract':
                benefit_line.unlink()

        benefits = self._search_benefits()

        # Compute the amounts for each employee benefit
        benefits.compute_amounts(self)

        # If the method is called from a salary rule.
        # It is important to call refresh() so that the record set
        # will contain the benefits computed above.
        self.refresh()

    @api.depends('details_by_salary_rule_category')
    def update_details_rule_category(self):
        for payslip in self:
            sum_total_sso = 0
            if payslip.line_ids:
                sum_total_sso = payslip.total_wage
                for line in payslip.line_ids:
                    if line.salary_rule_id.cal_sso:
                        sum_total_sso += line.total
                payslip.sum_total_sso = sum_total_sso

    def calculate_revenue_tax(self):
        slip_line_pool = self.env['hr.payslip.line']
        contract = self.env['hr.contract']
        total_revenue_summary_net = 0.0
        total_revenue_summary_for_tax = 0.0
        total_tax_paid = 0.0
        salary_month_net = 0.0
        tax_paid = 0.0
        revenue_summary_for_tax = 0.0
        total_tax_one_paid = 0.0
        total_revenue_summary_for_tax_one = 0.0

        for payslip in self:

            if payslip.contract_id:
                total_revenue_summary_net = payslip.contract_id.total_revenue_summary_net
                total_revenue_summary_for_tax = payslip.contract_id.total_revenue_summary_for_tax
                total_tax_paid = payslip.contract_id.total_tax_paid
                total_sso_paid = payslip.contract_id.total_sso_paid
                total_tax_one_paid = payslip.contract_id.total_tax_one_paid
                total_revenue_summary_for_tax_one = payslip.total_revenue_summary_for_tax_one

            # print('total_revenue_summary_for_tax b : ', total_revenue_summary_for_tax)

            for line in payslip.line_ids:
                # print line
                if line['code'] == 'NET':
                    if not payslip.credit_note:
                        total_revenue_summary_net += line['amount']
                    else:
                        total_revenue_summary_net -= line['amount']
                    salary_month_net = line['amount']

                if line['code'] == 'tax':
                    if not payslip.credit_note:
                        total_tax_paid += abs(line['amount'])
                    else:
                        total_tax_paid -= abs(line['amount'])
                    tax_paid = abs(line['amount'])

                if line['code'] == 'sso':
                    if not payslip.credit_note:
                        total_sso_paid += abs(line['amount'])
                    else:
                        total_sso_paid -= abs(line['amount'])

                # print('total_revenue_summary_for_tax bc : ', total_revenue_summary_for_tax)
                # if line['salary_rule_id']:
                #     if line['salary_rule_id'].cal_tax:
                #         # print line['amount']
                #         if not payslip.credit_note:
                #             total_revenue_summary_for_tax += line['amount']
                #         else:
                #             total_revenue_summary_for_tax -= line['amount']
                #         revenue_summary_for_tax += line['amount']


            print('total_revenue_summary_for_tax l : ',total_revenue_summary_for_tax)

            if not payslip.credit_note:
                total_revenue_summary_for_tax += payslip.sum_total_tax
                total_revenue_summary_for_tax += payslip.get_summary_for_tax_onetime()
                total_tax_one_paid += payslip.tax_one_paid
                total_revenue_summary_for_tax_one += payslip.summary_for_tax_one
            else:
                total_revenue_summary_for_tax -= payslip.sum_total_tax
                total_revenue_summary_for_tax -= payslip.get_summary_for_tax_onetime()
                total_tax_one_paid -= payslip.tax_one_paid
                total_revenue_summary_for_tax_one -= payslip.summary_for_tax_one

            print('total_revenue_summary_for_tax : ', total_revenue_summary_for_tax)
            print('total_net : ', salary_month_net)
            print('revenue_summary_for_tax : ', revenue_summary_for_tax)
            print('total_tax_paid : ', total_tax_paid)
            print('total_sso_paid : ', total_sso_paid)
            print('total_tax_one_paid : ', total_tax_one_paid)

            self.write({'total_net': salary_month_net,
                        'total_revenue_summary_net': total_revenue_summary_net,
                        'revenue_summary_for_tax': revenue_summary_for_tax,
                        'total_revenue_summary_for_tax': total_revenue_summary_for_tax,
                        'total_tax_paid': total_tax_paid,
                        'total_sso_paid': total_sso_paid,
                        'total_tax_one_paid': total_tax_one_paid,
                        'total_revenue_summary_for_tax_one': total_revenue_summary_for_tax_one,
                        'tax_paid': tax_paid,
                        })
            contract.write({'total_revenue_summary_net': total_revenue_summary_net,
                            'total_revenue_summary_for_tax': total_revenue_summary_for_tax,
                            'total_tax_paid': total_tax_paid,
                            'total_sso_paid': total_sso_paid,
                            'revenue_summary_for_tax': revenue_summary_for_tax,
                            'total_tax_one_paid': total_tax_one_paid,
                            'total_revenue_summary_for_tax_one': total_revenue_summary_for_tax_one,
                            })

    def action_payslip_done(self):
        self.calculate_revenue_tax()
        return self.write({'state': 'done'})
        # return super(hr_payslip,self).action_payslip_done()

    def compute_sheet(self):
        # self.get_worked_day_lines(self.contract_id,self.date_from,self.date_to)
        ############# Still need this function or not due to only total_wage field concern and it will be update again by get_cal_public_holidays
        # self._get_update_ot()
        # self._get_update_total_wage()
        super(hr_payslip, self).compute_sheet()
        for payslip in self:
            payslip.update({'deduct02':payslip.deduct02,
                            'deduct02_man':payslip.deduct02,
                            'total_wage':60000,
                            'total_wage_man':payslip.total_wage,})
            print ('--Start compute_sheet----')
            print (payslip.total_wage)
            payslip.compute_get_worked_day_lines()
            print ('--AFTER---')
            print (payslip.total_wage)
            ############# also compute total_wage, overtime
            payslip.get_cal_public_holidays()
            print (payslip.total_wage)
            ########### CAL leave
            payslip.get_cal_leave()
            print (payslip.total_wage)
            ########## call benifit
            payslip.button_compute_benefits()
            print (payslip.total_wage)
            ###### summary for tax
            payslip.get_summary_for_tax()
            print (payslip.total_wage)
            ########## then update rule category and update total sso
            payslip.update_details_rule_category()
            print (payslip.total_wage)
            ########## this should be the end of message, sso requrie update_details_rule_category, tax require get_summary_for_tax
            payslip._get_sso()
            print (payslip.total_wage)
            payslip._get_tax()

            print (payslip.total_wage)
            print ('--End compute_sheet----')

        return True

    # compute agin after onchange_employee_id
    def compute_get_worked_day_lines(self):
        print("compute_get_worked_day_lines : ",self)
        for slip in self:
            contracts = slip.contract_id
            print("contracts : ", slip.contract_id)
            if contracts and slip.date_from and slip.date_to:
                worked_days_line_ids = self.get_worked_day_lines(contracts, slip.date_from, slip.date_to)
                print('worked_days_line_ids : ',worked_days_line_ids)
                if worked_days_line_ids:
                    for work in worked_days_line_ids:
                        worked_days_id = self.env['hr.payslip.worked_days'].search([('payslip_id', '=', slip.id),
                                                                                    ('code', '=', work['code']),
                                                                                    ('contract_id', '=', work['contract_id']),
                                                                                    ('sequence', '=', work['sequence'])],limit=1)
                        if worked_days_id:
                            worked_days_id.update({'number_of_days':work['number_of_days'],
                                                   'number_of_hours':work['number_of_hours'],})
                        else:
                            work['payslip_id'] = self.id
                            self.env['hr.payslip.worked_days'].create(work)

    # def _get_compute_benefits(self):
    #     print ('_get_compute_benefits===1')
    #     for slip in self:
    #         if slip.benefit_line_ids:
    #             for ben in slip.benefit_line_ids:
    #                 if ben.category_id.salary_rule_ids:
    #                     for rule in ben.category_id.salary_rule_ids:
    #                         for cat in slip.details_by_salary_rule_category:
    #                             if rule.code == cat.code:
    #                                 if slip.allow06:
    #                                     print('1====================1')
    #                                     cat.update({
    #                                         'amount': ben.employer_amount + slip.allow06,
    #                                         'total': ben.employer_amount + slip.allow06,
    #                                     })
    #                                 else:
    #                                     print('2====================2')
    #                                     cat.update({
    #                                         'amount': ben.employer_amount,
    #                                         'total': ben.employer_amount,
    #                                     })
    #
    #                         for line in slip.line_ids:
    #                             if rule.code == line.code:
    #                                 print (rule.code)
    #                                 print (line.code)
    #                                 print (line.id)
    #                                 if slip.allow06:
    #                                     print ('1====================1')
    #                                     line.update({
    #                                         'amount': ben.employer_amount + slip.allow06,
    #                                         'total': ben.employer_amount + slip.allow06,
    #                                     })
    #                                 else:
    #                                     print('2====================2')
    #                                     line.update({
    #                                         'amount': ben.employer_amount,
    #                                         'total': ben.employer_amount,
    #                                     })


    ############## REMOVE BY JA- 07/12/2019
    # def _get_update_total_wage(self):
    #     total_wage = 0
    #
    #     ot1 = self.worked_days_line_ids.filtered(lambda x: x.code == 'Overtime1')
    #     ot2 = self.worked_days_line_ids.filtered(lambda x: x.code == 'Overtime2')
    #     ot3 = self.worked_days_line_ids.filtered(lambda x: x.code == 'Overtime3')
    #     ot4 = self.worked_days_line_ids.filtered(lambda x: x.code == 'Overtime4')
    #
    #     if ot1:
    #         total_wage += ot1.number_of_days * self.contract_id.wage
    #     if ot2:
    #         total_wage += ot2.number_of_days * self.contract_id.wage * 1.25
    #     if ot3:
    #         total_wage += ot3.number_of_days * self.contract_id.wage * 1.5
    #     if ot4:
    #         total_wage += ot4.number_of_days * self.contract_id.wage * 3
    #
    #     print ('_get_update_total_wage')
    #     print (self.total_wage)
    #     print (total_wage)
    #     self.total_wage = total_wage
    #     print(self.total_wage)

    def validate_payroll(self):
        return self.write({'state': 'validate'})

    # cal_tax in [hr.salary.rule]
    @api.multi
    def get_summary_for_tax(self):
        # print('def get_summary_for_tax')
        sum_total_tax = self.contract_id.wage
        if self.is_manual_salary:
            sum_total_tax = self.total_wage_man
        # print("Start wage from contract : " + str(sum_total_tax))

        salary_ids = self.env['hr.salary.rule'].search([])
        if salary_ids:
            for rule in salary_ids:
                if rule.cal_tax:
                    # print("rule.code : " + str(rule.code))
                    if rule.code == 'allow01':
                        sum_total_tax += self.allow01
                    elif rule.code == 'allow02':
                        sum_total_tax += self.allow02
                    elif rule.code == 'allow03':
                        sum_total_tax += self.allow03
                    elif rule.code == 'allow04':
                        sum_total_tax += self.allow04
                    elif rule.code == 'allow05':
                        sum_total_tax += self.allow05
                    elif rule.code == 'allow06':
                        sum_total_tax += self.allow06
                    elif rule.code == 'allow07':
                        sum_total_tax += self.allow07
                    elif rule.code == 'allow08':
                        sum_total_tax += self.allow08
                    elif rule.code == 'allow11':
                        sum_total_tax += self.allow11
                    elif rule.code == 'allow12':
                        sum_total_tax += self.allow12
                    elif rule.code == 'allow13':
                        sum_total_tax += self.allow13
                    elif rule.code == 'allow14':
                        sum_total_tax += self.allow14
                    elif rule.code == 'allow15':
                        sum_total_tax += self.allow15
                    elif rule.code == 'allow16':
                        sum_total_tax += self.allow16
                    elif rule.code == 'allow17':
                        sum_total_tax += self.allow17
                    elif rule.code == 'allow18':
                        sum_total_tax += self.allow18
                    elif rule.code == 'allow19':
                        sum_total_tax += self.allow19
                    elif rule.code == 'allow20':
                        sum_total_tax += self.allow20

                    elif rule.code == 'OT':
                        sum_total_tax += self.overtime
                    elif rule.code == 'deduct01':
                        sum_total_tax -= self.deduct01
                    elif rule.code == 'deduct02':
                        sum_total_tax -= self.deduct02
                    elif rule.code == 'deduct03':
                        sum_total_tax -= self.deduct03
                    elif rule.code == 'deduct04':
                        sum_total_tax -= self.deduct04
                    elif rule.code == 'deduct05':
                        sum_total_tax -= self.deduct05
                    elif rule.code == 'deduct06':
                        sum_total_tax -= self.deduct06
                    elif rule.code == 'deduct07':
                        sum_total_tax -= self.deduct07
                    elif rule.code == 'deduct08':
                        sum_total_tax -= self.deduct08
                    elif rule.code == 'deduct09':
                        sum_total_tax -= self.deduct09
                    elif rule.code == 'deduct10':
                        sum_total_tax -= self.deduct10
                    elif rule.code == 'deduct11':
                        sum_total_tax -= self.deduct11
                    elif rule.code == 'deduct12':
                        sum_total_tax -= self.deduct12
                    elif rule.code == 'deduct13':
                        sum_total_tax -= self.deduct13
                    elif rule.code == 'deduct14':
                        sum_total_tax -= self.deduct14
                    elif rule.code == 'deduct15':
                        sum_total_tax -= self.deduct15
                    elif rule.code == 'deduct16':
                        sum_total_tax -= self.deduct16
                    elif rule.code == 'deduct17':
                        sum_total_tax -= self.deduct17

        self.update({'sum_total_tax' : sum_total_tax})
        # print("end sum_total_tax : " + str(self.sum_total_tax))

    # cal_tax_onetime in [hr.salary.rule]
    def get_summary_for_tax_onetime(self):
        salary_ids = self.env['hr.salary.rule'].search([])
        sum_total_tax_onetime = 0
        if salary_ids:
            for rule in salary_ids:
                if rule.cal_tax_onetime:
                    if rule.code == 'allow01':
                        sum_total_tax_onetime += self.allow01
                    elif rule.code == 'allow02':
                        sum_total_tax_onetime += self.allow02
                    elif rule.code == 'allow03':
                        sum_total_tax_onetime += self.allow03
                    elif rule.code == 'allow04':
                        sum_total_tax_onetime += self.allow04
                    elif rule.code == 'allow05':
                        sum_total_tax_onetime += self.allow05
                    elif rule.code == 'allow06':
                        sum_total_tax_onetime += self.allow06
                    elif rule.code == 'allow07':
                        sum_total_tax_onetime += self.allow07
                    elif rule.code == 'allow08':
                        sum_total_tax_onetime += self.allow08
                    elif rule.code == 'allow11':
                        sum_total_tax_onetime += self.allow11
                    elif rule.code == 'allow12':
                        sum_total_tax_onetime += self.allow12
                    elif rule.code == 'allow13':
                        sum_total_tax_onetime += self.allow13
                    elif rule.code == 'allow14':
                        sum_total_tax_onetime += self.allow14
                    elif rule.code == 'allow15':
                        sum_total_tax_onetime += self.allow15
                    elif rule.code == 'allow16':
                        sum_total_tax_onetime += self.allow16
                    elif rule.code == 'allow17':
                        sum_total_tax_onetime += self.allow17
                    elif rule.code == 'allow18':
                        sum_total_tax_onetime += self.allow18
                    elif rule.code == 'allow19':
                        sum_total_tax_onetime += self.allow19
                    elif rule.code == 'allow20':
                        sum_total_tax_onetime += self.allow20

                    elif rule.code == 'OT':
                        sum_total_tax_onetime += self.overtime
                    elif rule.code == 'deduct01':
                        sum_total_tax_onetime -= self.deduct01
                    elif rule.code == 'deduct02':
                        sum_total_tax_onetime -= self.deduct02
                    elif rule.code == 'deduct03':
                        sum_total_tax_onetime -= self.deduct03
                    elif rule.code == 'deduct04':
                        sum_total_tax_onetime -= self.deduct04
                    elif rule.code == 'deduct05':
                        sum_total_tax_onetime -= self.deduct05
                    elif rule.code == 'deduct06':
                        sum_total_tax_onetime -= self.deduct06
                    elif rule.code == 'deduct07':
                        sum_total_tax_onetime -= self.deduct07
                    elif rule.code == 'deduct08':
                        sum_total_tax_onetime -= self.deduct08
                    elif rule.code == 'deduct09':
                        sum_total_tax_onetime -= self.deduct09
                    elif rule.code == 'deduct10':
                        sum_total_tax_onetime -= self.deduct10
                    elif rule.code == 'deduct11':
                        sum_total_tax_onetime -= self.deduct11
                    elif rule.code == 'deduct12':
                        sum_total_tax_onetime -= self.deduct12
                    elif rule.code == 'deduct13':
                        sum_total_tax_onetime -= self.deduct13
                    elif rule.code == 'deduct14':
                        sum_total_tax_onetime -= self.deduct14
                    elif rule.code == 'deduct15':
                        sum_total_tax_onetime -= self.deduct15
                    elif rule.code == 'deduct16':
                        sum_total_tax_onetime -= self.deduct16
                    elif rule.code == 'deduct17':
                        sum_total_tax_onetime -= self.deduct17
        return sum_total_tax_onetime

    # Hour working
    def get_hour_actual(self,slip):
        # Contract daily working schedule [0] may be Monday----------------------------------
        str_time_from = str(slip.contract_id.resource_calendar_id.attendance_ids[0].hour_from)
        str_time_to = str(slip.contract_id.resource_calendar_id.attendance_ids[0].hour_to)
        # Split hour only
        str_hour_form = str_time_from.split('.')[0]
        str_hour_form = int(str_hour_form)
        str_hour_to = str_time_to.split('.')[0]
        str_hour_to = int(str_hour_to)
        # hour working -1 for break -----------------------------------------------------------
        str_hour_actual = (str_hour_to - str_hour_form) - 1

        return str_hour_actual

    # hour working from attendance check_out - check_in
    def get_actual_hr(self, check_out , check_in):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        tz = pytz.timezone('Asia/Bangkok')
        # hour working from attendance check_out - check_in -----------------------------------
        actual_hr = pytz.utc.localize(
            datetime.strptime(check_out, DATETIME_FORMAT)).astimezone(
            tz) - pytz.utc.localize(
            datetime.strptime(check_in, DATETIME_FORMAT)).astimezone(
            tz)
        # hour working -1 for break -----------------------------------------------------------
        actual_hr = actual_hr - timedelta(hours=1)

        return actual_hr

    def convert_tomezone_date_from(self, date_from):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        date_from = user_tz.localize(fields.Datetime.from_string(date_from))
        date_from = date_from.astimezone(pytz.timezone('UTC'))
        # date_from = fields.Datetime.to_string(date_from)
        return date_from

    def convert_tomezone_date_to(self, date_to):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        date_to = user_tz.localize(fields.Datetime.from_string(date_to))
        date_to = date_to + timedelta(days=1, seconds=-1)
        date_to = date_to.astimezone(pytz.timezone('UTC'))
        # date_to = fields.Datetime.to_string(date_to)
        return date_to

    # Search attendance from date_from to date_to
    def get_search_attendance(self, slip, date_from, date_to):
        # print("def get_search_attendance")
        date_from = self.convert_tomezone_date_from(date_from)
        date_to = self.convert_tomezone_date_to(date_to)
        att_ids = self.env['hr.attendance'].search([('employee_id', '=', slip.employee_id.id),
                                                    ('check_in', '>=', str(date_from)),('check_in', '<=', str(date_to))])

        return att_ids

    # Search public_holidays from date_from to date_to for contract_id
    def get_public_holidays(self, slip, contract_id):
        # print("def get_public_holidays")
        holidays_public = contract_id.public_holiday_type.line_ids
        date_from = self.date_from
        date_to = self.date_to

        holidays_public_date = []
        holidays_public_ids = holidays_public.filtered(lambda x: x.date >= date_from and x.date <= date_to)
        for date_h in holidays_public_ids:
            holidays_public_date.append(date_h.date)

        return holidays_public_date

    def get_search_one_date_attendance(self, employee, date_from, date_to):
        # print("search attendance on date : " + str(date_from)+ " - " +str(date_to))
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        date_from = user_tz.localize(date_from)
        date_time_from = date_from.astimezone(pytz.timezone('UTC'))

        date_to = date_to + timedelta(seconds=-1)
        date_time_to = user_tz.localize(date_to)
        date_time_to = date_time_to.astimezone(pytz.timezone('UTC'))

        start_time_of_the_day = date_time_from.strftime(DATETIME_FORMAT)
        finish_time_of_the_day = date_time_to.strftime(DATETIME_FORMAT)
        # print("start_time_of_the_day : ",start_time_of_the_day)
        # print("finish_time_of_the_day : ",finish_time_of_the_day)

        attend_ids = self.env['hr.attendance'].search([('employee_id', '=', employee),
                                                       ('check_in', '>=', str(start_time_of_the_day)),
                                                       ('check_in', '<=', str(finish_time_of_the_day))],
                                                      order='check_in asc')

        # print('result search attendance ', len(attend_ids), ' : ', attend_ids)
        return attend_ids

    @api.multi
    def get_cal_public_holidays(self):
        print ('START-- def get_cal_public_holidays')
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        tz = pytz.timezone('Asia/Bangkok')
        ot_overtime1 = 0
        for slip in self:
            # if is_manual_salary
            overtime_man = slip.overtime
            allow18_man = slip.allow18
            overtime = 0.0

            # Search attendance from date_from to date_to-----------------------------
            att_ids = self.get_search_attendance(slip, slip.date_from, slip.date_to)
            # print("hr.attendance "+ str(len(att_ids)) +" : " + str(att_ids))

            attendance_s = []
            ot_overtime = total_wage = 0

            ############ Only use for Daily
            t_total_wage = ot_time_total = is_num = 0
            print ('--Before att_ids')
            print (slip.total_wage)
            if att_ids:
                days = 0
                for att in att_ids:
                    date_to = strToDate(att.check_in)
                    check_in = datetime(date_to.year, date_to.month, date_to.day).strftime('%Y-%m-%d') or False
                    attendance_s.append(check_in)

                    if slip.contract_id.wage_type == 'daily':
                        # Hour working ------------------------------------------------------------------------
                        str_hour_actual = self.get_hour_actual(slip)
                        # Rate from Overtime Structure --------------------------------------------------------
                        str_rate = float(slip.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[0].rate)
                        # hour working from attendance check_out - check_in -----------------------------------
                        actual_hr = self.get_actual_hr(att.check_out ,att.check_in)
                        float_actual_hr = slip.get_float_from_time(str(actual_hr))

                        # compare hour working from attendance with hour working working schedule--------------
                        if int(float_actual_hr) > str_hour_actual:
                            ot_time = int(float_actual_hr) - str_hour_actual
                            ot_time_total += ot_time
                            ovtime_wage_up = round(((slip.contract_id.wage / str_hour_actual) * str_rate))
                            ot_overtime += (ovtime_wage_up * ot_time)
                            days += 1
                        elif int(float_actual_hr) == str_hour_actual:
                            days += 1
                        elif int(float_actual_hr) < str_hour_actual:
                            t_total_wage += round(((slip.contract_id.wage * int(float_actual_hr))/str_hour_actual))

                        # is_num += 1
                        # print("No. : " + str(is_num))
                        # print("overtime hour(ot_time) : " + str(ot_time))
                        # print("days : " + str(days))
                        # print("overtime wage(ot_overtime) : " + str(ot_overtime))
                        # print("working late(t_total_wage) : " + str(t_total_wage))

                # print ('--in ATT IDS')
                # print (total_wage)
                # print (slip.contract_id.wage)
                # print (days)
                total_wage += total_wage + (slip.contract_id.wage*days)

            print ('--After att_ids')
            print (total_wage)
            # print("total overtime wage(ot_overtime) end : " + str(ot_overtime))
            # print("total overtime hour(ot_time) end : " + str(ot_time_total))

            if slip.contract_id.wage_type == 'monthly':
                # print('Contract monthly overtime_method = ' + str(slip.contract_id.overtime_structure_id.overtime_method))
                if slip.contract_id.overtime_structure_id.overtime_method == 'ov_attendance':
                    date_from = datetime.strptime(slip.date_from, "%Y-%m-%d").date()
                    date_to = datetime.strptime(slip.date_to, "%Y-%m-%d").date()
                    num = 0
                    date_s = []
                    att_date_s = []

                    att_ids = self.get_search_attendance(slip, slip.date_from, slip.date_to)
                    # print("att_ids hr.attendance " + str(len(att_ids)) + " : " + str(att_ids))

                    if att_ids:
                        for att_s in att_ids:
                            att_date_s.append(att_s)

                    if slip.contract_id.resource_calendar_id.shift.employee_working_schedule_ids:
                        for working in slip.contract_id.resource_calendar_id.shift.employee_working_schedule_ids:
                            if working.date >= str(date_from) and working.date <= str(date_to):
                                date_s.append(working.date)

                    if att_date_s:
                        for att_d in att_date_s:
                            date_to = strToDate(att_d.check_in)
                            check_in = datetime(date_to.year, date_to.month, date_to.day).strftime(
                                '%Y-%m-%d') or False

                            if check_in not in date_s:
                                num += 1

                    if slip.contract_id.overtime_structure_id.is_check_manager:
                        if att_ids:
                            for att in att_ids:
                                str_time_from = str(slip.contract_id.resource_calendar_id.attendance_ids[0].hour_from)
                                str_time_to = str(slip.contract_id.resource_calendar_id.attendance_ids[0].hour_to)
                                str_hour_form = str_time_from.split('.')[0]
                                str_hour_form = int(str_hour_form)
                                str_hour_to = str_time_to.split('.')[0]
                                str_hour_to = int(str_hour_to)
                                str_hour_actual = (str_hour_to - str_hour_form) - 1
                                str_rate = float(
                                    slip.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[0].rate)

                                check_date = datetime.strptime(att.check_in, "%Y-%m-%d  %H:%M:%S").date()
                                hour_from_s = str(str_time_from).split(".")
                                h = hour_from_s[0]
                                m = hour_from_s[1]
                                if len(str(h)) < 2:
                                    h = '0' + str(h)
                                if len(str(m)) < 2:
                                    m = str(m) + '0'
                                start_time = datetime.strptime(str(h) + ':' + str(m) + ':' + '00', '%H:%M:%S')
                                start_time = start_time.time()
                                start_time_of_date = tz.localize(datetime.combine(check_date, start_time))
                                start_time_of_the_day = tz.localize(datetime.combine(date_from, start_time))

                                actual_hr = pytz.utc.localize(
                                    datetime.strptime(att.check_out, DATETIME_FORMAT)).astimezone(
                                    tz) - start_time_of_date

                                actual_hr = actual_hr - timedelta(hours=1)
                                float_actual_hr = slip.get_float_from_time(str(actual_hr))
                                if int(float_actual_hr) > str_hour_actual:
                                    ot_time = int(float_actual_hr) - str_hour_actual

                                    if ot_time > slip.contract_id.overtime_structure_id.ot_hour:
                                        ot_time = slip.contract_id.overtime_structure_id.ot_hour
                                    else:
                                        ot_time = ot_time
                                    ot_overtime += (((
                                            ((slip.contract_id.wage / str_hour_actual) / 30) * str_rate)) * ot_time)

                            num = 0
                            for line in slip.contract_id.public_holiday_type.line_ids:
                                if line.date in attendance_s:
                                    num += 1

                            overtime = round(((slip.contract_id.wage / 30) * num), 2)
                    total_wage = slip.contract_id.wage

                    if slip.is_manual_salary:
                        total_wage = slip.total_wage_man
                        ot_overtime = overtime_man
                        overtime = allow18_man

                    slip.update({
                        'overtime': round(ot_overtime),
                        'total_wage': total_wage,
                        'allow18': overtime,
                    })
                else:
                    ot_ids = self.env['hr.overtime'].search(
                        [('employee_id', '=', slip.employee_id.id), ('from_date', '>=', slip.date_from),
                         ('to_date', '<=', slip.date_to), ('state', '=', 'approve')])
                    # print("hr.overtime " + str(len(ot_ids)) + " : " + str(ot_ids))

                    ot_time = 0.00
                    for ot in ot_ids:
                        # print ot.name
                        if not ot.approve_ot_time:
                            # print "OT-11111111111"
                            ot_time += ot.cal_ot(False)
                        else:
                            # print "OT-2222222222"
                            ot_time += ot.approve_ot_time

                    total_wage = slip.contract_id.wage

                    if ot_time:
                        ot_overtime1 = ((total_wage / 30) / 8) * ot_time

                    if slip.is_manual_salary:
                        total_wage = slip.total_wage_man
                        ot_overtime1 = overtime_man

                    slip.update({
                        'overtime': round(ot_overtime1),
                        'total_wage': total_wage,
                    })

            else:
                print ('--After att_ids before public_holiday_type')
                print (total_wage)
                num = 0
                num1 = 0
                num2 = 0
                for line in slip.contract_id.public_holiday_type.line_ids:
                    if line.is_pay_holiday:
                        if line.date in attendance_s:
                            num2 += 1
                        else:
                            num1 += 1
                    # else:
                    #     if line.date in attendance_s:
                    #         num += 1

                    # if line.is_pay_holiday:
                    #     num1 += 1
                    # if line.date in attendance_s:
                    #     num += 1
                overtime = round(((slip.contract_id.wage * 1) * num), 2)

                # total_wage = ((total_wage + t_total_wage) - (slip.contract_id.wage * num)) + round(overtime)
                print ('--t_total_wage')
                print (total_wage)
                print (t_total_wage)
                total_wage = (total_wage + t_total_wage)
                print ('--After public_holiday_type')
                print (total_wage)
                # allow18 = (slip.contract_id.wage * num2) + round(overtime) + (slip.contract_id.wage * num1)
                allow18 = (slip.contract_id.wage * num2) + (slip.contract_id.wage * num1)

                if slip.is_manual_salary:
                    total_wage = slip.total_wage_man
                    ot_overtime = overtime_man
                    allow18 = allow18_man

                slip.update({
                    'overtime': round(ot_overtime),
                    'total_wage': total_wage,
                    'allow18': allow18,
                })
            # print('END-- def get_cal_public_holidays')

            # print("overtime : " + str(slip.overtime))
            # print('END-- def get_cal_public_holidays')

    @api.multi
    def get_cal_leave(self):
        # print('def get_cal_leave')
        deduct17 = 0.0
        if self.contract_id.wage_type == 'monthly' and not self.contract_id.is_manager:
            worked_days_id = self.env['hr.payslip.worked_days'].search([('payslip_id', '=', self.id),
                                                                        ('code', '=', 'Absent01')], limit=1)
            if worked_days_id:
                if worked_days_id.number_of_days:
                    # print("wage : " + str(self.contract_id.wage / 30))
                    deduct17 = (self.contract_id.wage / 30) * (worked_days_id.number_of_days)
                # print("deduct17 : " +str(deduct17))
        self.update({
            'deduct17': round(deduct17)
        })

    @api.multi
    def get_cal_leave_old(self):
        # print('def get_cal_leave')
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        for payslip in self:
            date_from = self.convert_tomezone_date_from(payslip.date_from)
            date_to = self.convert_tomezone_date_to(payslip.date_to)

            if payslip.contract_id.wage_type == 'monthly' and not payslip.contract_id.is_manager:

                # วันลา
                # leave_ids = self.env['hr.holidays'].search(
                #     [('employee_id', '=', payslip.employee_id.id),
                #      ('date_from', '>=', str(date_from)), ('date_to', '<=', str(date_to)),
                #      ('state', '=', 'validate'),
                #      ('holiday_type', '=', 'employee'), ('type', '=', 'remove')])

                leave_domain = [('state', '=', 'validate'),
                                ('employee_id', '=', payslip.employee_id.id),
                                ('type', '=', 'remove'),
                                '|', ('date_from', '>=', str(date_from)), ('date_to', '>=', str(date_from)),
                                '|', ('date_from', '<=', str(date_to)), ('date_to', '<=', str(date_to)), ]
                leave_ids = self.env['hr.holidays'].search(leave_domain)
                # print("hr.holidays " + str(len(leave_ids)) + " : " + str(leave_ids))

                num_leave = 0
                leave_date = []
                if leave_ids:
                    for leave in leave_ids:
                        leave_day = pytz.utc.localize(
                            datetime.strptime(leave.date_from, "%Y-%m-%d  %H:%M:%S")).astimezone(user_tz)
                        leave_day = leave_day.strftime('%Y-%m-%d')
                        leave_date.append(leave_day)
                        num_leave += 1
                    # print("leave_date " + str(len(leave_date)) + " : " + str(leave_date))

                num = 0
                working_date = []
                att_date = []

                att_ids = self.get_search_attendance(payslip, payslip.date_from, payslip.date_to)
                # print("hr.attendance " + str(len(att_ids)) + " : " + str(att_ids))

                # attendance to date list
                if att_ids:
                    for att_s in att_ids:
                        check_date = pytz.utc.localize(
                            datetime.strptime(att_s.check_in, "%Y-%m-%d  %H:%M:%S")).astimezone(user_tz)
                        check_date = check_date.strftime('%Y-%m-%d')
                        att_date.append(check_date)
                # print("att_date " + str(len(att_date)) + " : " + str(att_date))

                if payslip.contract_id.resource_calendar_id.shift.employee_working_schedule_ids:
                    # working_schedule_ids = self.env['employee.working.schedule'].search(
                    #     [('employee_shift_id', '=', shift_id.id),
                    #      ('date', '>=', payslip.date_from), ('date', '<=', payslip.date_to)])
                    working_day = payslip.contract_id.resource_calendar_id.shift.employee_working_schedule_ids.filtered(
                        lambda x: x.date >= payslip.date_from and x.date <= payslip.date_to)
                    for working in working_day:
                        working_date.append(working.date)
                    # working_date = working_day.ids

                public_holidays = self.get_public_holidays(payslip, payslip.contract_id)
                # print("public_holidays " + str(len(public_holidays)) + " : " + str(public_holidays))
                # print("working_date " + str(len(working_date)) + " : " + str(working_date))

                if working_date or leave_date :
                    for date in working_date:
                        date_str = str(date)
                        if date_str not in att_date and date_str not in leave_date and date_str not in public_holidays:
                            num += 1

                # print('num_leave', num_leave)
                # print('num', num)
                # if num_leave and num:
                #     deduct17 = (payslip.contract_id.wage / 30) * (num_leave+num)
                # elif num_leave:
                #     deduct17 = (payslip.contract_id.wage / 30) * (num_leave)
                if num:
                    deduct17 = (payslip.contract_id.wage / 30) * (num)
                else:
                    deduct17 = 0

                # print("deduct17 : " +str(deduct17))
                payslip.update({
                    'deduct17': round(deduct17)
                })

    def set_hr_period_id(self):
        print("set_hr_period_id ")
        if self.hr_period_id:
            print("hr_period_id :",self.hr_period_id)
            # dates must be updated together to prevent constraint
            self.date_from = self.hr_period_id.date_start
            self.date_to = self.hr_period_id.date_end
            self.date_payment = self.hr_period_id.date_payment
        else:
            self.date_payment = self.date_to

    def get_total_working_day(self,date_from,date_to,total_month_day):
        print('def get_total_working_day')
        print('total_month_day : ',total_month_day)
        date_from = datetime.strptime(date_from, "%Y-%m-%d")
        month = date_from.month
        month_next = date_from.month
        day_of_week_ids = []
        date_from = date_from - timedelta(days=1)
        for day in range(1, total_month_day + 1, 1):
            if month == month_next:
                date = date_from + timedelta(days=day)
                # print('date + : ', date)
                day_of_week = int(date.strftime('%w')) - 1
                if day_of_week == -1 :
                    day_of_week = 6
                day_of_week_ids.append(day_of_week)
                month_next = date.month
        # print "day_of_week ",len(day_of_week_ids)," : ",day_of_week_ids
        working_hours = self.contract_id.resource_calendar_id.attendance_ids
        num_working = 0
        if working_hours:
            for work in working_hours:
                num_working += day_of_week_ids.count(int(work.dayofweek))

        return num_working

    @api.depends('employee_id', 'contract_id', 'date_from', 'date_to', 'hr_period_id')
    def _get_working_day(self):
        print('def _get_working_day')
        print('contract_id : ',self.contract_id)
        print('date_from : ',self.date_from)
        print('date_to : ',self.date_to)

        if self.employee_id and self.contract_id and self.hr_period_id:
            self.set_hr_period_id()
            for payslip in self:

                # check contract start
                if payslip.contract_id.date_start and payslip.contract_id.date_start > payslip.date_from:
                    start = datetime.strptime(payslip.contract_id.date_start, "%Y-%m-%d")
                else:
                    start = datetime.strptime(payslip.date_from, "%Y-%m-%d")
                # start = datetime.strptime(payslip.date_from, "%Y-%m-%d")

                # check contract end
                if payslip.contract_id.date_end and payslip.contract_id.date_end < payslip.date_to:
                    end = datetime.strptime(payslip.contract_id.date_end, "%Y-%m-%d")
                else:
                    end = datetime.strptime(payslip.date_to, "%Y-%m-%d")
                # end = datetime.strptime(payslip.date_to, "%Y-%m-%d")

                # print "START END"
                # print "start : ",start
                # print "end : ",end
                total_working_day = (end - start).days + 1
                total_month_day = (datetime.strptime(payslip.date_to, "%Y-%m-%d") - datetime.strptime(payslip.date_from, "%Y-%m-%d")).days +1
                num_working = self.get_total_working_day(payslip.date_from, payslip.date_to, total_month_day)

                # print 'total_working_day: '+str(total_working_day)
                # print 'total_month_day: '+str(total_month_day)

                if payslip.contract_id.wage_type == 'monthly':
                    total_working_day = num_working

                payslip.total_working_day = total_working_day
                payslip.total_month_day = total_month_day

    @api.depends('employee_id', 'contract_id', 'date_from', 'date_to')
    def _get_working_day_old(self):
        # check contract start
        # print self.employee_id
        # print self.contract_id
        # print self.date_from
        # print self.date_to
        for payslip in self:
            if payslip.contract_id.date_start and payslip.contract_id.date_start > payslip.date_from:
                # print "111111111"
                start = datetime.strptime(payslip.contract_id.date_start, "%Y-%m-%d")
            else :
                # print "22222"
                # print "payslip.date_from"
                # if payslip.
                # print payslip.date_from
                start = datetime.strptime(payslip.date_from, "%Y-%m-%d")

            # check contract end
            if payslip.contract_id.date_end and payslip.contract_id.date_end < payslip.date_to:
                end = datetime.strptime(payslip.contract_id.date_end, "%Y-%m-%d")
            else:
                end = datetime.strptime(payslip.date_to, "%Y-%m-%d")

            # print start
            # print end
            total_working_day = (end - start).days
            # print total_working_day
            total_month_day = (
                    datetime.strptime(payslip.date_to, "%Y-%m-%d") - datetime.strptime(payslip.date_from, "%Y-%m-%d")).days

            if total_month_day > 30:
                total_month_day = 30
            else:
                if total_working_day == total_month_day:
                    total_working_day = 30
                    total_month_day = 30
                else:
                    total_working_day += 1
                    total_month_day = 30

            if total_working_day > 30:
                total_working_day = 30

            shift_id = payslip.contract_id.resource_calendar_id.shift
            working_schedule_ids = self.env['employee.working.schedule'].search([('employee_shift_id','=',shift_id.id),
                                                                                 ('date','>=',payslip.date_from),('date','<=',payslip.date_to)])
            payslip.total_working_day = len(working_schedule_ids)
            payslip.total_month_day = total_month_day

            # payslip.total_working_day = 30
            # payslip.total_month_day = 30

    @api.depends('worked_days_line_ids')
    def _get_update_ot(self):
        # print('def _get_update_ot')
        precision = self.env['decimal.precision'].precision_get('account')
        for payslip in self:
            total_ot = 0
            working_hr = 0
            i = 0
            working_hr_id = payslip.contract_id.resource_calendar_id.attendance_ids
            for line in working_hr_id:
                i += 1
                working_hr += line.hour_to - line.hour_from - payslip.contract_id.resource_calendar_id.break_time

            if i != 0:
                working_hr = working_hr / i
            # print working_hr

            if payslip.worked_days_line_ids:
                for worked_day_line in payslip.worked_days_line_ids:
                    if worked_day_line.code == 'Overtime1' or worked_day_line.code == 'Overtime2' or worked_day_line.code == 'Overtime3' or worked_day_line.code == 'Overtime4':
                        total_ot += worked_day_line.number_of_hours

            if working_hr != 0:
                # print "INFO---"
                # print total_ot
                # print working_hr
                # print payslip.contract_id.wage
                total_ot = (total_ot / working_hr) * (payslip.contract_id.wage/30)

            ############### no need to compute OT here ##########
            # print "total_ot"
            # print total_ot
            # print round(total_ot,0)
            # payslip.overtime = round(total_ot,0)

    @api.depends('worked_days_line_ids')
    def _get_payment_holiday(self):
        for payslip in self:
            if payslip.worked_days_line_ids:
                holiday_days = payslip.worked_days_line_ids.filtered(lambda x: x.code == 'Holiday01')
                if holiday_days:
                    payslip.allow04 = holiday_days.number_of_days * payslip.contract_id.wage

    ################# use
    @api.depends('employee_id', 'contract_id', 'date_from', 'date_to', 'total_working_day', 'total_month_day')
    def _get_sso(self):
        # print ('def _get_sso')
        if self.date_payment:
            date_payment = datetime.strptime(self.date_payment, "%Y-%m-%d").date()
            date_year = date_payment.year
        else:
            date_year = datetime.today().year

        precision = self.env['decimal.precision'].precision_get('account')
        sso_id = self.env['social.security.line'].search([('year', '=', date_year)], limit=1)
        # print("Year Social Security : " + str(date_year) + " Found : " + str(len(sso_id)))
        sso_rate = self.env.user.company_id.default_sso_rate * 0.01
        maximum_sso = self.env.user.company_id.default_maximum_sso

        minimum_rate = maximum_rate = 0.0
        if sso_id:
            minimum_rate = sso_id.minimum_rate
            maximum_rate = sso_id.maximum_rate

        for payslip in self:
            result = 0
            manual_sso = payslip.deduct09
            if not payslip.is_manual_sso:
                # print("wage type : " + str(payslip.contract_id.wage_type))
                if payslip.contract_id.wage_type == 'daily':

                    if payslip.sum_total_sso:
                        wage = payslip.sum_total_sso
                        if wage > 0 and wage <= minimum_rate:
                            result = minimum_rate * sso_rate
                        elif wage > minimum_rate:
                            result = wage * sso_rate
                            if result > maximum_rate * sso_rate:
                                result = maximum_rate * sso_rate
                            else:
                                result = wage * sso_rate
                        elif wage == 0:
                            result = 0
                else:
                    wage = payslip.sum_total_sso
                    if wage > 0 and wage <= minimum_rate:
                        # print('if wage > 0 and wage <= minimum_rate')
                        result = minimum_rate * sso_rate
                    elif wage > minimum_rate:
                        # print('elif wage > minimum_rate')
                        result = wage * sso_rate
                        if result > maximum_rate * sso_rate:
                            result = maximum_rate * sso_rate
                        else:
                            result = wage * sso_rate
                        # print("result : " + str(result))
                    elif wage == 0:
                        # print("elif wage == 0")
                        result = 0

                if payslip.contract_id.exclude_sso:
                    result = 0
                elif result > maximum_sso:
                    result = maximum_sso
                else:
                    result = float_round(result, 0)

                    # Edit by Book less than 0.5 down
                    # new_round = round(result, 0)
                    # if float_compare(new_round, result, precision_digits=precision) >= 0:
                    #     result = new_round
                    # else:
                    #     result = new_round + 1
                # print ('result sso : ' + str(result))
                payslip.deduct09 = abs(float_round(result, 0))
            else:
                payslip.update({'deduct09': manual_sso})

    ################# use
    @api.depends('employee_id', 'contract_id', 'date_from', 'date_to', 'allow08', 'allow10', 'allow13', 'allow09',
                 'allow11', 'overtime', 'total_working_day', 'total_month_day','sum_total_tax')
    def _get_tax(self):
        # print('def _get_tax')
        precision = self.env['decimal.precision'].precision_get('account')
        if self.date_payment:
            date_payment = datetime.strptime(self.date_payment, "%Y-%m-%d").date()
            date_year = date_payment.year
        else:
            date_year = datetime.today().year

        tax_id = self.env['personal.income.tax'].search([('year', '=', date_year)], limit=1)
        # print("Year Personal Tax: " + str(date_year) + " Found : " + str(len(tax_id)))
        tax_deduct3 = 0.0

        for payslip in self:
            tax_deduct1 = tax_deduct2 = tax_deduct3 = tax_deduct4 = result1 = total_ot = 0
            result_tax_onetime = summary_for_tax_onetime = tax_revenue = 0.0
            calculate_tax = ""
            month = 12

            # print("deduct09 : " + str(payslip.deduct09))
            # print("deduct02 : " + str(payslip.deduct02))
            manual_tax = payslip.deduct02_man
            tax_one_revenue = payslip.total_revenue_summary_for_tax_one
            total_revenue_sso = payslip.total_sso_paid

            if not payslip.is_manual_tax:
                tax_revenue = payslip.contract_id.total_tax_paid

                if payslip.date_payment and payslip.sum_total_tax:
                    # print('if payslip.date_payment and payslip.sum_total_tax (1)')
                    curr_date = datetime.now()
                    # print payslip.contract_id.date_start
                    # print datetime(curr_date.year,01,01).date()

                    ###########JA-08/07/2020 #############
                    # Remove this condition as per user request #
                    # original #
                    # if strToDate(payslip.contract_id.date_start) <= datetime(curr_date.year,1,1).date() and not payslip.is_full_year:
                    # new # only check if not full year, this mean to use actual month to cal #
                    if not payslip.is_full_year:
                        # print('if strToDate(payslip.contract_id.date_start) <= datetime(curr_date.year,1,1).date() and not payslip.is_full_year (1.2)')
                        # ทำงานไม่ครบปีก็คิดตามปกติ-----------------------------------------------------------------------
                        # if payslip.contract_id.total_revenue_summary_for_tax:
                        # print('if payslip.contract_id.total_revenue_summary_for_tax (1.2.1)')
                        date = datetime.strptime(payslip.date_payment, "%Y-%m-%d").date()
                        date_month = date.month
                        month = 1
                        for x in range(date_month, 12, 1):
                            month += 1

                        total_revenue = payslip.contract_id.total_revenue_summary_for_tax
                        base_tax_receive = payslip.sum_total_tax
                        result1 = total_revenue + (base_tax_receive * month)

                        # print('total_revenue_sso : ', total_revenue_sso)
                        # print('deduct09 : ', payslip.deduct09)
                        tax_deduct3 = total_revenue_sso + (payslip.deduct09 * month)

                        summary_for_tax_onetime = payslip.get_summary_for_tax_onetime()
                        if summary_for_tax_onetime <= 0:
                            tax_one_revenue = 0
                        result_tax_onetime = result1 + summary_for_tax_onetime

                        # print('เดือนที่เหลือ : ',i)
                        # print('ยอดรวมภาษีสะสม : ',base_tax_receive)

                        calculate_tax += "ยอดรวมภาษีสะสม = " + str("{0:,.2f}".format(total_revenue)) + \
                                         "+" + "(" + "ยอดรวมภาษีสะสม/เดือน = " + str("{0:,.2f}".format(base_tax_receive)) + \
                                         "*" + "เดือนที่เหลือ = "  + str(month) + ")" + "\n"
                        # ทำงานไม่ครบปีก็คิดตามปกติ-----------------------------------------------------------------------
                        # else:
                        #     # print('else payslip.contract_id.total_revenue_summary_for_tax (1.2.2)')
                        #     base_tax_receive = payslip.sum_total_tax
                        #     result1 = base_tax_receive * month
                        #     tax_deduct3 = payslip.deduct09 * month
                        #     summary_for_tax_onetime = payslip.get_summary_for_tax_onetime()
                        #     if summary_for_tax_onetime <= 0:
                        #         tax_one_revenue = 0
                        #     result_tax_onetime = result1 + summary_for_tax_onetime
                        #
                        #     calculate_tax += "ยอดรวมภาษีสะสม/เดือน = " + str("{0:,.2f}".format(base_tax_receive)
                        #                                                      ) + "เดือนที่เหลือ = " + str(month) + "\n"
                        # ----------------------------------------------------------------------------------------------
                    else:
                        # print('not tax full year')
                        base_tax_receive = payslip.sum_total_tax
                        result1 = base_tax_receive * month
                        tax_deduct3 = payslip.deduct09 * month
                        summary_for_tax_onetime = payslip.get_summary_for_tax_onetime()
                        if summary_for_tax_onetime <= 0:
                            tax_one_revenue = 0
                        result_tax_onetime = result1 + summary_for_tax_onetime

                        calculate_tax += "ยอดรวมภาษีสะสม/เดือน = " + str("{0:,.2f}".format(base_tax_receive)
                                                                         ) + "เดือนที่เหลือ = " + str(month) + "\n"
                else:
                    # print('else payslip.date_payment and payslip.sum_total_tax (2)')
                    base_tax_receive = payslip.sum_total_tax
                    result1 = base_tax_receive * month
                    summary_for_tax_onetime = payslip.get_summary_for_tax_onetime()
                    if summary_for_tax_onetime <= 0:
                        tax_one_revenue = 0
                    result_tax_onetime = result1 + summary_for_tax_onetime + tax_one_revenue

                    calculate_tax += "ยอดรวมภาษีสะสม/เดือน = " + str("{0:,.2f}".format(base_tax_receive)
                                                                     ) + "เดือนที่เหลือ = " + str(month) + "\n"

                calculate_tax += "รายได้คงที่นับจากงวดปัจจุบันถึงสิ้นปี = " + str("{0:,.2f}".format(result1)) + "\n"
                # ----------------------------------------------------------------
                tax_deduct1 = result1 * 0.5
                # print('tax_deduct3 : ', tax_deduct3)
                # print('result1 : ', result1)
                # print('summary_for_tax_onetime : ', summary_for_tax_onetime)
                # print('tax_one_revenue : ', tax_one_revenue)
                # print('result_tax_onetime : ', result_tax_onetime)

                # ค่าลดหย่อน 60,000
                if payslip.contract_id.hr_tax_deduction_ids:
                    for deduct in payslip.contract_id.hr_tax_deduction_ids:
                        tax_deduct2 += deduct.amount
                tax_deduct2 += 60000

                # 50% of net net max 100,000
                if tax_deduct1 > 100000:
                    tax_deduct1 = 100000

                # 5% of net max 90000
                if not payslip.contract_id.exclude_sso and tax_deduct3 > 9000:
                    tax_deduct3 = 9000
                elif payslip.contract_id.exclude_sso:
                    tax_deduct3 = 0

                tax_deduct4 = payslip.deduct06 * 12

                calculate_tax += "หักค่าใช้จ่าย = " + str("{0:,.2f}".format(tax_deduct1)) + "\n"
                calculate_tax += "หักค่าลดหย่อน = " + str("{0:,.2f}".format(tax_deduct2)) + "\n"
                calculate_tax += "หักประกันสังคม = " + str("{0:,.2f}".format(tax_deduct3)) + "\n"
                #----------------------------------------------------------------

                result_base = self.get_tax_deduct(payslip, result1, tax_deduct3)
                result_one  = self.get_tax_deduct(payslip, result_tax_onetime ,tax_deduct3)
                net_base_tax = net_one_tax = net_diff_tax = origin_net_base_tax = 0

                if tax_id:
                    origin_net_base_tax = self.get_personal_tax(payslip, tax_id, result_base)

                    net_one_tax = self.get_personal_tax(payslip, tax_id, result_one)
                    net_diff_tax = abs(origin_net_base_tax - net_one_tax)
                    # หักภาษีที่เสียแล้ว
                    net_base_tax = origin_net_base_tax - tax_revenue
                    if net_base_tax < 0.0 :
                        net_base_tax = 0.0

                result_base_tax = net_base_tax / month
                result = result_base_tax + net_diff_tax

                if tax_revenue > 0:
                    calculate_tax += "ยอดภาษีที่คำนวณได้ = " + str("{0:,.2f}".format(origin_net_base_tax)) + "\n"
                    calculate_tax += "หักภาษีที่เสียแล้ว = " + str("{0:,.2f}".format(tax_revenue))+"\n"
                calculate_tax += "ยอดที่ได้" + str("{0:,.2f}".format(net_base_tax)) + " นำไปหารเดือนทั้งปี คือ " + str(month) + \
                                 " เดือน เป็นจำนวน " + str("{0:,.2f}".format(result_base_tax)) +"\n"

                # print('net_diff_tax : ',net_diff_tax)
                if net_diff_tax > 0 :
                    calculate_tax += "รายได้ไม่คงที่ = " + str("{0:,.2f}".format(summary_for_tax_onetime)) + "\n"
                    calculate_tax += "ภาษีจากรายได้ไม่คงที่ = " + str("{0:,.2f}".format(net_diff_tax)) + "\n"
                result = float_round(result, 0)
                # print('result tax : ' + str(result))

                payslip.deduct02 = abs(result)
                payslip.summary_for_tax_one = abs(summary_for_tax_onetime)
                payslip.tax_one_paid = float_round(abs(net_diff_tax), 0)

                calculate_tax += "ที่ต้องเสียภาษี คือ " + str("{0:,.2f}".format(result)) + "\n"
                calculate_tax += "รวมยอดที่ต้องนำไปคำนวณภาษี = " + str("{0:,.2f}".format(result)) + "\n"
            else:
                calculate_tax += "ทำการระบุเอง = " + str("{0:,.2f}".format(manual_tax))
                payslip.update({'deduct02': manual_tax})

            payslip.update({'calculate_tax': calculate_tax})

    def get_tax_deduct(self, payslip, result, tax_deduct3):
        tax_deduct1 = tax_deduct2 = tax_deduct4 = 0
        tax_deduct1 = result * 0.5

        # ค่าลดหย่อน 60,000
        if payslip.contract_id.hr_tax_deduction_ids:
            for deduct in payslip.contract_id.hr_tax_deduction_ids:
                tax_deduct2 += deduct.amount

        tax_deduct2 += 60000

        # 50% of net net max 100,000
        if tax_deduct1 > 100000:
            tax_deduct1 = 100000

        # 5% of net max 90000
        if not payslip.contract_id.exclude_sso and tax_deduct3 > 9000:
            tax_deduct3 = 9000
        elif payslip.contract_id.exclude_sso:
            tax_deduct3 = 0

        tax_deduct4 = payslip.deduct06 * 12
        result_tax = result - tax_deduct1 - tax_deduct2 - tax_deduct3 - tax_deduct4

        return result_tax

    def get_personal_tax(self,payslip, tax_id, result):
        # print("def get_personal_tax")
        # print("result : " + str(result))
        net_tax = i = 0
        step_1 = step_1_rate = step_2 = step_2_rate = 0
        step_3 = step_3_rate = step_4 = step_4_rate = 0
        step_5 = step_5_rate = step_6 = step_6_rate = 0
        step_7 = step_7_rate = step_8 = step_8_rate = 0

        for tax_line in tax_id.personal_tax_line_ids.sorted(key=lambda r: r.rate_no):
            i += 1
            if i == 1:
                step_1 = (tax_line.maximum_rate)
            elif i == 2:
                step_2 = (tax_line.minimum_rate - 1)
                step_2_rate = tax_line.tax_rate / 100
            elif i == 3:
                step_3 = (tax_line.minimum_rate - 1)
                step_3_rate = tax_line.tax_rate / 100
            elif i == 4:
                step_4 = (tax_line.minimum_rate - 1)
                step_4_rate = tax_line.tax_rate / 100
            elif i == 5:
                step_5 = (tax_line.minimum_rate - 1)
                step_5_rate = tax_line.tax_rate / 100
            elif i == 6:
                step_6 = (tax_line.minimum_rate - 1)
                step_6_rate = tax_line.tax_rate / 100
            elif i == 7:
                step_7 = (tax_line.minimum_rate - 1)
                step_7_rate = tax_line.tax_rate / 100
            elif i == 8:
                step_8 = (tax_line.minimum_rate - 1)
                step_8_rate = tax_line.tax_rate / 100

        if result > step_8:
            # print('if result > step_8')
            net_tax = (result - step_8) * step_8_rate
            result = step_8
            # print("result8 : " + str(result))
            # print("net_tax : " + str(net_tax))
            # print("step_8 : " + str(step_8))

        if result > step_7:
            # print('if result > step_7')
            net_tax += (result - step_7) * step_7_rate
            result = step_7
            # print("result7 : " + str(result))
            # print("net_tax : " + str(net_tax))
            # print("step_7 : " + str(step_7))

        if result > step_6:
            # print('if result > step_6')
            net_tax += (result - step_6) * step_6_rate
            result = step_6
            # print("result6 : " + str(result))
            # print("net_tax : " + str(net_tax))
            # print("step_6 : " + str(step_6))

        if result > step_5:
            # print('if result > step_5')
            net_tax += (result - step_5) * step_5_rate
            result = step_5
            # print("result5 : " + str(result))
            # print("net_tax : " + str(net_tax))
            # print("step_5 : " + str(step_5))

        if result > step_4:
            # print('if result > step_4')
            net_tax += (result - step_4) * step_4_rate
            result = step_4
            # print("result4 : " + str(result))
            # print("net_tax : " + str(net_tax))
            # print("step_4 : " + str(step_4))

        if result > step_3:
            # print('if result > step_3')
            net_tax += (result - step_3) * step_3_rate
            result = step_3
            # print("result3 : " + str(result))
            # print("net_tax : " + str(net_tax))
            # print("step_3 : " + str(step_3))

        if result > step_2:
            # print('if result > step_2')
            net_tax += (result - step_2) * step_2_rate
            # print("result2 : " + str(result))
            # print("net_tax : " + str(net_tax))
            # print("step_2 : " + str(step_2))

        # print('net_tax : ' + str(net_tax))
        return net_tax

    @api.depends('employee_id', 'contract_id', 'date_from', 'date_to')
    def _get_allowance(self):
        for payslip in self:
            result = 0
            result1 = 0
            domain = [
                ('state', '=', 'validate'),
                ('employee_id', '=', payslip.employee_id.id),
                ('type', '=', 'remove'),
                ('date_from', '>=', payslip.date_from),
                ('date_to', '<=', payslip.date_to),
                ('allow_money_flag','=',True),
            ]
            holiday_allowance_ids = self.env['hr.holidays'].search(domain)
            if holiday_allowance_ids:
                for holiday in holiday_allowance_ids:
                    # print holiday.date_from
                    # print holiday.holiday_status_id.allow_money_amount
                    if holiday.holiday_status_id.group_leave == 'group1' or holiday.holiday_status_id.group_leave == 'group4':
                        result = result + holiday.holiday_status_id.allow_money_amount
                    else:
                        result1 = result1 + holiday.holiday_status_id.allow_money_amount
            payslip.allow02 = round(result,0)
            payslip.allow04 = round(result1, 0)

    @api.multi
    def get_pays_since_beginning(self, pays_per_year):
        """
        Get the number of pay periods since the beginning of the year.
        """
        self.ensure_one()

        date_from = fields.Date.from_string(self.date_from)

        year_start = date(date_from.year, 1, 1)
        year_end = date(date_from.year, 12, 31)

        days_past = float((date_from - year_start).days)
        days_total = (year_end - year_start).days

        return round((days_past / days_total) * pays_per_year, 0) + 1

    ####### function to check leave
    def was_on_leave(self, employee_id, datetime_day, datetime_next_day):
        # print("def was_on_leave")
        res = False
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        date_from = user_tz.localize(datetime_day)
        date_time_from = date_from.astimezone(pytz.timezone('UTC'))

        date_to = datetime_day + timedelta(days=1, seconds=-1)
        date_time_to = user_tz.localize(date_to)
        date_time_to = date_time_to.astimezone(pytz.timezone('UTC'))

        date_time_from = date_time_from.strftime(DATETIME_FORMAT)
        date_time_to = date_time_to.strftime(DATETIME_FORMAT)

        # leave_domain = [('state', '=', 'validate'),
        #                 ('employee_id', '=', employee_id),
        #                 ('type', '=', 'remove'),
        #                 ('date_from', '>=', date_time_from),('date_to', '<=', date_time_to)]

        leave_domain = [('state', '=', 'validate'),
                        ('employee_id', '=', employee_id),
                        ('type', '=', 'remove'),
                        '|', ('date_from', '>=', date_time_from), ('date_to', '>=', date_time_from),
                        '|', ('date_from', '<=', date_time_to), ('date_to', '<=', date_time_to),]
        # print('leave_domain: ',leave_domain)

        leave_ids = self.env['hr.holidays'].search(leave_domain)
        if leave_ids:
            res = leave_ids
        return res

    ########function to check absent
    def was_on_absent(self, employee_id, datetime_day, datetime_next_day):
        attend_ids = self.get_search_one_date_attendance(employee_id, datetime_day, datetime_next_day)
        res = False if attend_ids else "absent"
        return res

    def get_working_hr(self,employee_id, datetime_day, datetime_next_day):
        # print("def get_working_hr")
        attend_ids = self.get_search_one_date_attendance(employee_id, datetime_day, datetime_next_day)
        if attend_ids:
            if len(attend_ids) == 1:
                if attend_ids[0].employee_id.contract_id.wage_type == 'monthly':
                    check_date = datetime.strptime(attend_ids.check_in, "%Y-%m-%d  %H:%M:%S").date()
                    date_ss = []
                    for work in attend_ids[0].employee_id.contract_id.resource_calendar_id.shift.employee_working_schedule_ids:
                        date_ss.append(work.date)
                    if str(check_date) in date_ss:
                        for working in attend_ids[0].employee_id.contract_id.resource_calendar_id.shift.employee_working_schedule_ids:
                            if str(working.date) == str(check_date):
                                if len(attend_ids[0].employee_id.contract_id.resource_calendar_id.attendance_ids) > 1:
                                    for calendar in attend_ids[0].employee_id.contract_id.resource_calendar_id.attendance_ids:
                                        if calendar.dayofweek == '0':
                                            week = 'Monday'
                                        elif calendar.dayofweek == '1':
                                            week = 'Tuesday'
                                        elif calendar.dayofweek == '2':
                                            week = 'Wednesday'
                                        elif calendar.dayofweek == '3':
                                            week = 'Thursday'
                                        elif calendar.dayofweek == '4':
                                            week = 'Friday'
                                        elif calendar.dayofweek == '5':
                                            week = 'Saturday'
                                        elif calendar.dayofweek == '6':
                                            week = 'Sunday'

                                        work_id = self.env['employee.working.schedule'].search([('id','=',working.id)])

                                        if week == work_id.day:
                                            hour_from_s = str(calendar.hour_from).split(".")
                                            h = hour_from_s[0]
                                            m = hour_from_s[1]
                                            if len(str(h)) < 2:
                                                h = '0' + str(h)
                                            if len(str(m)) < 2:
                                                m = str(m) + '0'

                                            hour_from_s1 = str(calendar.hour_to).split(".")
                                            h1 = hour_from_s1[0]
                                            m1 = hour_from_s1[1]
                                            if len(str(h1)) < 2:
                                                h1 = '0' + str(h1)
                                            if len(str(m1)) < 2:
                                                m1 = str(m1) + '0'

                                            start_time = datetime.strptime(str(h)+':'+str(m)+':'+'00', '%H:%M:%S')
                                            finish_time = datetime.strptime(str(h1)+':'+str(m1)+':'+'00', '%H:%M:%S')
                                            start_time = start_time.time()
                                            finish_time = finish_time.time()

                                            # start_time_of_date = tz.localize(datetime.combine(check_date, start_time))
                                            # finish_time_of_date = tz.localize(datetime.combine(check_date, finish_time))

                                            start_time_of_date = datetime.strptime(str(check_date) + ' ' + str(start_time), '%Y-%m-%d %H:%M:%S')
                                            finish_time_of_date = datetime.strptime(str(check_date) + ' ' + str(finish_time), '%Y-%m-%d %H:%M:%S')

                                            no_hr = finish_time_of_date - start_time_of_date

                                else:
                                    calendar = attend_ids[0].employee_id.contract_id.resource_calendar_id.attendance_ids[0]
                                    if calendar.dayofweek == '0':
                                        week = 'Monday'
                                    elif calendar.dayofweek == '1':
                                        week = 'Tuesday'
                                    elif calendar.dayofweek == '2':
                                        week = 'Wednesday'
                                    elif calendar.dayofweek == '3':
                                        week = 'Thursday'
                                    elif calendar.dayofweek == '4':
                                        week = 'Friday'
                                    elif calendar.dayofweek == '5':
                                        week = 'Saturday'
                                    elif calendar.dayofweek == '6':
                                        week = 'Sunday'

                                    work_id = self.env['employee.working.schedule'].search([('id', '=', working.id)])

                                    if week == work_id.day:
                                        hour_from_s = str(calendar.hour_from).split(".")
                                        h = hour_from_s[0]
                                        m = hour_from_s[1]
                                        if len(str(h)) < 2:
                                            h = '0' + str(h)
                                        if len(str(m)) < 2:
                                            m = str(m) + '0'

                                        hour_from_s1 = str(calendar.hour_to).split(".")
                                        h1 = hour_from_s1[0]
                                        m1 = hour_from_s1[1]
                                        if len(str(h1)) < 2:
                                            h1 = '0' + str(h1)
                                        if len(str(m1)) < 2:
                                            m1 = str(m1) + '0'

                                        start_time = datetime.strptime(str(h) + ':' + str(m) + ':' + '00', '%H:%M:%S')
                                        finish_time = datetime.strptime(str(h1) + ':' + str(m1) + ':' + '00', '%H:%M:%S')
                                        start_time = start_time.time()
                                        finish_time = finish_time.time()
                                        # start_time_of_date = tz.localize(datetime.combine(check_date, start_time))
                                        # finish_time_of_date = tz.localize(datetime.combine(check_date, finish_time))

                                        start_time_of_date = datetime.strptime(str(check_date) + ' ' + str(start_time),
                                                                               '%Y-%m-%d %H:%M:%S')
                                        finish_time_of_date = datetime.strptime(str(check_date) + ' ' + str(finish_time),
                                                                                '%Y-%m-%d %H:%M:%S')

                                        no_hr = finish_time_of_date - start_time_of_date
                    else:
                        no_hr = 0
                else:
                    no_hr = datetime.strptime(attend_ids.check_out, '%Y-%m-%d %H:%M:%S') - datetime.strptime(attend_ids.check_in, '%Y-%m-%d %H:%M:%S')
            else:
                no_hr = datetime.strptime(attend_ids[len(attend_ids)-1].check_out, '%Y-%m-%d %H:%M:%S') - datetime.strptime(attend_ids[0].check_in, '%Y-%m-%d %H:%M:%S')
        else:
            no_hr = 0

        return no_hr

    def get_late_hr(self,employee, datetime_day, datetime_next_day):
        # print("def get_late_hr")
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')

        attend_ids = self.get_search_one_date_attendance(employee.id, datetime_day, datetime_next_day)
        # print("attend_ids : ",len(attend_ids))
        if attend_ids:
            if len(attend_ids) == 1:
                if employee.contract_id.wage_type == 'monthly':
                    # check_date = datetime.strptime(attend_ids.check_in, "%Y-%m-%d  %H:%M:%S").date()
                    check_date = pytz.utc.localize(
                        datetime.strptime(attend_ids.check_in, "%Y-%m-%d  %H:%M:%S")).astimezone(user_tz)
                    check_date = check_date.date()
                    # print("check_date : ", check_date)

                    date_ss = []
                    shift_id = self.contract_id.resource_calendar_id.shift
                    working_schedule_ids = self.env['employee.working.schedule'].search(
                        [('employee_shift_id', '=', shift_id.id),
                         ('date', '>=', check_date), ('date', '<=', check_date)])
                    for work in working_schedule_ids:
                        date_ss.append(work.date)
                    attendance_ids = self.contract_id.resource_calendar_id.attendance_ids

                    if str(check_date) in date_ss:
                        for working in working_schedule_ids:
                            working_day = datetime.strptime(working.date, "%Y-%m-%d").strftime('%w')
                            working_day = int(working_day) - 1
                            if str(working.date) == str(check_date):
                                if len(attendance_ids) > 1:
                                    calendar = attendance_ids.filtered(lambda x: x.dayofweek == str(working_day))
                                    hour_from = calendar.hour_from
                                    first_sign_in_of_day = pytz.utc.localize(
                                        datetime.strptime(attend_ids.check_in, "%Y-%m-%d %H:%M:%S")).astimezone(user_tz)
                                    first_sign = self.get_float_from_time_late(first_sign_in_of_day.strftime("%H:%M:%S"))

                                    if first_sign > hour_from:
                                        no_hr = first_sign - hour_from
                                        no_hr = self.get_time_from_float(no_hr)
                                    else:
                                        no_hr = 0
                                else:
                                    calendar = attendance_ids.filtered(lambda x: x.dayofweek == str(working_day))
                                    hour_from_s = str(calendar.hour_from).split(".")
                                    h = hour_from_s[0]
                                    m = hour_from_s[1]
                                    if len(str(h)) < 2:
                                        h = '0' + str(h)
                                    if len(str(m)) < 2:
                                        m = str(m) + '0'

                                    hour_from_s1 = str(calendar.hour_to).split(".")
                                    h1 = hour_from_s1[0]
                                    m1 = hour_from_s1[1]
                                    if len(str(h1)) < 2:
                                        h1 = '0' + str(h1)
                                    if len(str(m1)) < 2:
                                        m1 = str(m1) + '0'

                                    start_time = datetime.strptime(str(h) + ':' + str(m) + ':' + '00', '%H:%M:%S')
                                    finish_time = datetime.strptime(str(h1) + ':' + str(m1) + ':' + '00',
                                                                    '%H:%M:%S')
                                    start_time = start_time.time()
                                    finish_time = finish_time.time()
                                    # start_time_of_date = tz.localize(datetime.combine(check_date, start_time))
                                    # finish_time_of_date = tz.localize(datetime.combine(check_date, finish_time))

                                    start_time_of_date = tz.localize(datetime.combine(check_date, start_time))
                                    first_sign_in_of_day = pytz.utc.localize(
                                        datetime.strptime(attend_ids.check_in, "%Y-%m-%d  %H:%M:%S")).astimezone(
                                        user_tz)

                                    # start_time_of_date = datetime.strptime(str(check_date) + ' ' + str(start_time),
                                    #                                        '%Y-%m-%d %H:%M:%S')
                                    finish_time_of_date = datetime.strptime(
                                        str(check_date) + ' ' + str(finish_time),
                                        '%Y-%m-%d %H:%M:%S')
                                    if first_sign_in_of_day > start_time_of_date:
                                        no_hr = first_sign_in_of_day - start_time_of_date
                                    else:
                                        no_hr = 0
                    else:
                        no_hr = 0
                else:
                    no_hr = 0
            else:
                no_hr = 0
        else:
            no_hr = 0

        return no_hr

    ##########function to check public holiday####3
    def was_on_holiday(self,employee_id, datetime_day):
        res = False
        day = datetime_day.strftime("%Y-%m-%d")
        # holiday_ids = self.env['hr.holidays.public'].get_holidays_lines(day, day, employee_id.address_id.id)

        # holiday_id = self.env['hr.holidays.public.line'].search([('date', '=', day)],limit=1)
        # print holiday_id

        contract_id = self.env['hr.contract'].search([('employee_id','=',employee_id.id)], limit=1)
        if contract_id.public_holiday_type.line_ids:
            for holiday_id in contract_id.public_holiday_type.line_ids:
                if holiday_id.date == day:
                    res = holiday_id.name
        return res
        # if holiday_id:
        # print "วันหยุด"
        # print datetime_day
        # res = holiday_id.name
        # print res
        # return res

    def was_on_woking(self,contract, datetime_day):
        # print("def was_on_woking")
        res = False
        day = datetime_day.strftime("%Y-%m-%d")
        if contract.resource_calendar_id.shift:
            if contract.resource_calendar_id.shift.employee_working_schedule_ids.filtered(lambda x: x.date == day):
                res = day
        return res

    @api.multi
    def check_contract_start_end(self,contract_id, day_from, day_to, date_from, date_to):
        nb_of_days = (day_to - day_from).days + 1
        # check contract start
        if contract_id.date_start and contract_id.date_start > date_from:
            start = (datetime.strptime(contract_id.date_start, "%Y-%m-%d") - day_from).days
        else:
            start = 0

        # check contract end
        if contract_id.date_end and contract_id.date_end < date_to:

            nb_of_days = nb_of_days - (day_to - datetime.strptime(contract_id.date_end, "%Y-%m-%d")).days
        else:
            nb_of_days = (day_to - day_from).days + 1

        return start, nb_of_days

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        print('get_worked_day_lines : ',contract_ids, date_from, date_to)
        res = []
        res_get_working_day = self.get_working_day_info(contract_ids, date_from, date_to)
        ot1, ot2, ot3, ot4 = self.get_over_time_info()
        res = res + res_get_working_day + [ot1] + [ot2] + [ot3] + [ot4]
        total_wage = 0.0

        if ot1:
            total_wage += ot1['number_of_days'] * self.contract_id.wage
        if ot2:
            total_wage += ot2['number_of_days'] * self.contract_id.wage * 1.25
        if ot3:
            total_wage += ot3['number_of_days'] * self.contract_id.wage * 1.5
        if ot4:
            total_wage += ot4['number_of_days'] * self.contract_id.wage * 3

        print('total_wage + ot : ',total_wage)

        self.total_wage = total_wage
        return res

    def get_working_day_info(self, contracts, date_from, date_to):
        print("def get_working_day_info : ",contracts, date_from, date_to)
        res = []
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            print("contract : " + str(contract.id))
            day_from = datetime.combine(fields.Date.from_string(date_from), datetime_time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), datetime_time.max)
            print('day_from : ', day_from)
            print('day_to : ', day_to)
            employee_id = contract.employee_id.id
            employee = contract.employee_id
            print("Get Working Day info : " + str(employee.name))

            attendances = {
                'name': _("ทำงานปรกติ"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }

            weekend = {
                'name': _("วันหยุดประจำสัปดาห์"),
                'sequence': 1,
                'code': 'Weekend01',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }

            absents = {
                'name': _("ขาดงาน"),
                'sequence': 10,
                'code': 'Absent01',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }

            holidays = {
                'name': _("วันหยุดประจำปี/วันหยุดบริษัท"),
                'sequence': 5,
                'code': 'Holiday01',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }

            late = {
                'name': 'Late',
                'sequence': 12,
                'code': 'Late',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }

            leaves = {}

            # start = 0
            # day_from = datetime.strptime(self.date_from, "%Y-%m-%d")
            # day_to = datetime.strptime(self.date_to, "%Y-%m-%d")
            # print('day_from : ', day_from)
            # print('day_to : ', day_to)

            start, nb_of_days = self.check_contract_start_end(contract, day_from, day_to, date_from, date_to)
            weekend_day = 0

            for day in range(start, nb_of_days):

                datetime_day = day_from + timedelta(days=day)
                datetime_next_day = day_from + timedelta(days=day + 1)
                # print("DAY : ", datetime_day, "------------------------------------------------------------")
                # print('Datetime Day : ', datetime_day)
                # print('Datetime Next Day : ', datetime_next_day)

                working_hours_on_day = self.contract_id.working_hours_on_day(datetime_day)
                # if self.contract_id.resource_calendar_id.break_time and working_hours_on_day:
                #     working_hours_on_day = working_hours_on_day - self.contract_id.resource_calendar_id.break_time
                # print('Working hours on day: ', working_hours_on_day)

                # Attendance in day
                attend_ids = self.get_search_one_date_attendance(employee_id, datetime_day, datetime_next_day)

                leave_type = self.was_on_leave(employee_id, datetime_day, datetime_next_day)
                absent_type = self.was_on_absent(employee_id, datetime_day, datetime_next_day)
                public_holiday_type = self.was_on_holiday(employee, datetime_day)
                public_working_type = self.was_on_woking(contract, datetime_day)

                # print("leave type : " + str(leave_type))
                # print("absent type : " + str(absent_type))
                # print("public holiday type : " + str(public_holiday_type))
                # print("public working type : " + str(public_working_type))

                if working_hours_on_day:
                    allow_hr = self.get_working_hr(employee_id, datetime_day, datetime_next_day)
                    late_hr = self.get_late_hr(employee, datetime_day, datetime_next_day)
                    # print("late_hr : " + str(late_hr))
                    # print("allow_hr : " + str(allow_hr))

                    if late_hr and allow_hr:
                        late['number_of_days'] += self.get_float_from_time_late(str(late_hr)) / self.get_float_from_time(str(allow_hr))
                        late['number_of_hours'] += self.get_float_from_time_late(str(late_hr))

                    if leave_type:
                        # show time record is hour if leave allow hour.
                        # leave_type more than one by day
                        for leave_type_line in leave_type:
                            if leave_type_line.holiday_status_id.allow_hr:
                                number_of_days = leave_type_line.number_of_days_temp
                                if number_of_days > 1:
                                    number_of_days = 1
                                if leave_type_line.leave_time == 0:
                                    number_of_hours = working_hours_on_day
                                else:
                                    number_of_hours = leave_type_line.leave_time
                            else:
                                number_of_days = 1.0
                                number_of_hours = working_hours_on_day

                            # print('number_of_days: ',number_of_days)
                            # print('number_of_hours: ',number_of_hours)
                            # print('leave_type_line : ', leave_type_line.holiday_status_id.name)

                            if leave_type_line.holiday_status_id.name in leaves:
                                # print "leave exist"
                                # print day
                                # print leave_type
                                # print leave_type_line.name
                                leaves[leave_type_line.holiday_status_id.name]['number_of_days'] += number_of_days
                                leaves[leave_type_line.holiday_status_id.name]['number_of_hours'] += number_of_days * working_hours_on_day
                                # print leaves[leave_type_line.holiday_status_id.name]['number_of_days']
                                # print leaves[leave_type_line.holiday_status_id.name]['number_of_hours']
                            else:
                                leaves[leave_type_line.holiday_status_id.name] = {
                                    'name': leave_type_line.holiday_status_id.name,
                                    'sequence': 5,
                                    'code': leave_type_line.holiday_status_id.name,
                                    'number_of_days': number_of_days,
                                    'number_of_hours': number_of_days * working_hours_on_day,
                                    'contract_id': contract.id,
                                }

                        # over_leave = leave_type_line.holiday_status_id.limit
                        # print over_leave
                        # print number_of_hours
                        # if over_leave:
                        #     # print "11"
                        #     over_holidays['number_of_days'] += number_of_days
                        #     over_holidays['number_of_hours'] += number_of_hours

                    elif not leave_type and not absent_type:
                        no_hr = allow_hr
                        ########### compare actual no_hr and normal working day
                        if no_hr and self.get_float_from_time(str(no_hr)) < working_hours_on_day:
                            # print("ACTUAL")
                            attendances['number_of_days'] += self.get_float_from_time(str(no_hr)) / working_hours_on_day
                            attendances['number_of_hours'] += self.get_float_from_time(str(no_hr))
                        else:
                            # print("ORIGINAL")
                            attendances['number_of_days'] += 1.0
                            attendances['number_of_hours'] += working_hours_on_day
                    else:
                        # print("public_holiday, weekend, absents")
                        if public_holiday_type:
                            # print("public holiday type : " + str(public_holiday_type))
                            holidays['number_of_days'] += 1.0
                            holidays['number_of_hours'] += working_hours_on_day
                        elif absent_type and public_working_type:
                            # print("absents day : " + str(day_from + timedelta(days=day)))
                            absents['number_of_days'] += 1.0
                            absents['number_of_hours'] += working_hours_on_day
                        else:
                            # print("weekend day : " + str(day_from + timedelta(days=day)))
                            weekend['number_of_days'] += 1.0
                            weekend['number_of_hours'] += working_hours_on_day
                else:
                    # print("else for weekend day")
                    weekend_day =+ 1
                    if not absent_type:
                        # print "working not working day"
                        attendances['number_of_days'] += 1.0
                        attendances['number_of_hours'] += working_hours_on_day
                    else:
                        weekend['number_of_days'] += 1.0
                        weekend['number_of_hours'] += working_hours_on_day

            leaves = [value for key, value in leaves.items()]

            #########Assign total wage to eimplyee by consider wage type daily or monthly
            total_wage = 0
            if self.contract_id.wage_type == 'monthly' and self.contract_id.schedule_pay == 'monthly':
                total_wage = self.contract_id.wage
            elif self.contract_id.wage_type == 'monthly' and self.contract_id.schedule_pay == 'weekly':
                total_wage = self.contract_id.wage / 4
            elif self.contract_id.wage_type == 'daily':
                total_wage = self.contract_id.wage * attendances['number_of_days']

            print ('--TOTAL WAGE: ', total_wage)
            print ('attendances : ', attendances)
            print ('--------------')
            self.total_wage = total_wage

            res += [attendances] + leaves + [absents]+ [weekend]+ [holidays] + [late]
            # print('res : ' + str(res))
        return res

    def get_number_of_day_of_month(self,date_from,date_to):
        # print('def get_number_of_day_of_month')
        day_from = datetime.strptime(date_from, "%Y-%m-%d")
        day_to = datetime.strptime(date_to, "%Y-%m-%d")
        nb_of_days = (day_to - day_from).days + 1
        # print('nb_of_days : ' + str(nb_of_days))
        return nb_of_days

    def get_number_of_hour_of_the_day(self, cr, uid, date_in, working_hours_id, context):
        working_hr_a_day = 0.0
        if type(date_in) is datetime:
            working_hours = self.pool.get('resource.calendar').browse(cr, uid, working_hours_id, context=context)
            for line in working_hours.attendance_ids:
                # all assign to hour
                if int(line.dayofweek) == date_in.weekday():
                    working_hr_a_day += line.hour_to - line.hour_from

        return working_hr_a_day

    def is_in_working_schedule(self,date_in, working_hours_id):
        found = False
        # print date_in
        # print type(date_in)
        if type(date_in) is date:
            working_hours = working_hours_id
            for line in working_hours.attendance_ids:
                if int(line.dayofweek) == date_in.weekday():
                    found = True
                    break
        # else:
        # print "ELSE"
        # print "FOUND:"
        # print found
        return found

    # float convert to time ####################
    def get_time_from_float(self,float_time):
        # print('def get_time_from_float ( ' + str(float_time) + ' )')
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        TIME_FORMAT = "%H:%M:%S"
        str_time = str(float_time)
        str_hour = str_time.split('.')[0]
        str_minute = ("%2d" % int(str(float("0." + str_time.split('.')[1]) * 60).split('.')[0])).replace(' ','0')
        str_ret_time = str_hour + ":" + str_minute + ":00"
        str_ret_time = datetime.strptime(str_ret_time, TIME_FORMAT).time()
        return str_ret_time

    # time convert to float and round up time 00 , 30
    def get_float_from_time(self,time_type):
        # print('def get_float_from_time ( ' +str(time_type) +' )')
        signOnP = [int(n) for n in time_type.split(":")]
        # if signOnP < 30 then it will 00,
        # if more then 30 then it will 30
        signOnP[1] = 0 if signOnP[1] < 30 else 30
        signOnH = signOnP[0] + signOnP[1] / 60.0
        return signOnH

    # float convert to time late ###################
    def get_float_from_time_late(self,time_type):
        # print('def get_float_from_time_late ( ' + str(time_type) + ' )')
        signOnP = [int(n) for n in time_type.split(":")]
        signOnH = signOnP[0] + signOnP[1] / 60.0
        return signOnH

    def get_over_time_info(self):
        # print('def get_over_time_info')
        # Common Variable
        val_overtime = 0.0
        val_overtime1 = 0.0
        val_overtime2 = 0.0
        val_overtime3 = 0.0
        val_overtime4 = 0.0
        val_overtime5 = 0.0
        val_overtime6 = 0.0
        val_overtime7 = 0.0
        val_overtime1_hr = 0.0
        overtime1 = {}
        overtime2 = {}
        overtime3 = {}
        overtime4 = {}
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        TIME_FORMAT = "%H:%M:%S"

        tz_base = pytz.timezone('UTC')
        tz = pytz.timezone('Asia/Bangkok')

        working_hr = 8.0
        ############ check working our actual############
        if not self.contract_id.resource_calendar_id.break_time:
            working_actual_hours_on_day = working_hr + 1
        else:
            working_actual_hours_on_day =  working_hr
        ############ check working our actual############

        nb_of_days = 0
        sign_in_date = ""
        sign_in_attendance_time = timedelta(hours=00, minutes=00, seconds=00)
        sign_out_date = ""
        sign_out_attendance_time = timedelta(hours=00, minutes=00, seconds=00)

        # print("Overtime structure : " + str(self.employee_id.contract_id.overtime_structure_id.overtime_method))
        if self.employee_id.contract_id.overtime_structure_id.overtime_method == 'ov_request':

            ot_ids = self.env['hr.overtime'].search([('employee_id','=',self.employee_id.id),
                                                     ('from_date','>=',self.date_from),
                                                     ('to_date','<=',self.date_to),('state','=','approve')])

            for ot in ot_ids:
                # print ot.name
                if not ot.approve_ot_time:
                    ot_time = ot.cal_ot(False)
                else:
                    ot_time = ot.approve_ot_time

                if ot.type == 'working_day':
                    val_overtime1 += ot_time
                elif ot.type == 'weekend':
                    val_overtime2 += ot_time
                elif ot.type == 'day_off_charge_daily':
                    val_overtime3 += ot_time
                elif ot.type == 'day_off_charge_monthly':
                    val_overtime4 += ot_time

            overtime1 = {
                'name': 'โอทีวันทำงานปกติ',
                'sequence': 11,
                'code': 'Overtime1',
                'number_of_days': val_overtime1 / working_hr,
                'number_of_hours': val_overtime1,
                'contract_id': self.contract_id.id,
            }

            overtime2 = {
                'name': 'โอทีวันหยุด',
                'sequence': 12,
                'code': 'Overtime2',
                'number_of_days': val_overtime2 / working_hr,
                'number_of_hours': val_overtime2,
                'contract_id': self.contract_id.id,
            }

            overtime3 = {
                'name': 'ค่าจ้างทำงานวันหยุด (รายวัน)',
                'sequence': 13,
                'code': 'Overtime3',
                'number_of_days': val_overtime3 / working_hr,
                'number_of_hours': val_overtime3,
                'contract_id': self.contract_id.id,
            }

            overtime4 = {
                'name': 'ค่าจ้างทำงานวันหยุด (รายเดือน)',
                'sequence': 14,
                'code': 'Overtime4',
                'number_of_days': val_overtime4 / working_hr,
                'number_of_hours': val_overtime4,
                'contract_id': self.contract_id.id,
            }
        elif self.employee_id.contract_id.overtime_structure_id.overtime_method == 'ov_attendance':
            # for day in range(0, self.get_number_of_day_of_month(self.date_from, self.date_to)):
            start_dt = strToDate(self.date_from)

            str_time_from = str(self.contract_id.resource_calendar_id.attendance_ids[0].hour_from)
            str_time_to = str(self.contract_id.resource_calendar_id.attendance_ids[0].hour_to)
            str_hour_form = str_time_from.split('.')[0]
            str_hour_form = int(str_hour_form)
            str_hour_to = str_time_to.split('.')[0]
            str_hour_to = int(str_hour_to)

            hour_to_s = str(str_time_to).split(".")
            h = hour_to_s[0]
            m = hour_to_s[1]
            if len(str(h)) < 2:
                h = '0' + str(h)
            if len(str(m)) < 2:
                m = str(m) + '0'
            start_time = datetime.strptime(str(h) + ':' + str(m) + ':' + '00', '%H:%M:%S')
            start_time = start_time.time()
            start_time_of_date = datetime.combine(start_dt, start_time)

            start_time1 = datetime.strptime('23:59:59', '%H:%M:%S')
            start_time1 = start_time1.time()
            finish_time_of_the_day = datetime.combine(start_dt, start_time1)

            # attendance_ids = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id),
            #                                                    ('check_out', '>', str(start_time_of_date))])
            attendance_ids = self.get_search_attendance(self, self.date_from, self.date_to)

            val_overtime2_hours = 0
            ot_time = days = ot_time_total = 0

            if attendance_ids:

                for att in attendance_ids:
                    # print('attendance : '+str(att))

                    # hour working from attendance check_out - check_in -----------------------------------
                    str_hour_actual = self.get_hour_actual(self)
                    actual_hr = self.get_actual_hr(att.check_out, att.check_in)

                    # if att.check_out <= att.check_in:
                    #     continue

                    try:
                        float_actual_hr = self.get_float_from_time(str(actual_hr))

                    except ValueError as e:
                        raise UserError(_("Please check attendance record %s") % pytz.utc.localize(datetime.strptime(att.check_in, DATETIME_FORMAT)).astimezone(tz))


                    # compare hour working from attendance with hour working working schedule--------------
                    if int(float_actual_hr) > str_hour_actual:
                        ot_time = int(float_actual_hr) - str_hour_actual
                        ot_time_total += ot_time
                        days += 1
                    elif int(float_actual_hr) == str_hour_actual:
                        days += 1

                val_overtime2 = days
                val_overtime2_hours = ot_time_total

                # print("val_overtime2 : " + str(val_overtime2))
                # print("val_overtime2_hours : " + str(ot_time_total))

                # don't use ------------------------------------------------------------------------------
                # start_time_of_date = datetime.combine(start_dt, start_time)
                # start_time_of_date = self.env['hr.attendance'].convert_TZ_UTC(str(start_time_of_date))
                # finish_time_of_date = datetime.combine(start_dt, finish_time)
                # finish_time_of_date = self.env['hr.attendance'].convert_TZ_UTC(str(finish_time_of_date))
                #
                # attendance_ids = self.env['hr.attendance'].search([('employee_id','=',self.employee_id.id),('check_in','>=',str(start_time_of_date)),('check_out','<=',str(finish_time_of_date))])
                # if attendance_ids:
                #     for attendance in attendance_ids:
                #         # print "ATT--:"
                #         # print attendance.check_in
                #         # print attendance.check_out
                #         working_hours_on_day = self.is_in_working_schedule(start_dt, self.contract_id.resource_calendar_id)
                #         ########### Actual working day as per working schedule
                #         working_actual_hours_on_day = self.contract_id.resource_calendar_id.working_hours_on_day(start_day_from)
                #
                #         ########### Actual by attendance
                #         # print start_day_from
                #         # print start_day_from + timedelta(days=1)
                #
                #         no_hr = self.get_working_hr(self.contract_id.employee_id.id, start_day_from,start_day_from + timedelta(days=1))
                #         # print "NO-HR"
                #         # print no_hr
                #         if no_hr:
                #             no_hr = self.get_float_from_time(str(no_hr))
                #
                #         ########## if attendnance less then working hour schedule then use attendance
                #         if no_hr and no_hr < working_actual_hours_on_day:
                #             working_actual_hours_on_day = no_hr
                #
                #         # if they have break time then actual hour deduct by break time but if actual hour <= 4 mean only monring time or afternoon time then no need to deduct break time
                #         if self.contract_id.resource_calendar_id.break_time and working_actual_hours_on_day and working_actual_hours_on_day > 4:
                #             working_actual_hours_on_day = working_actual_hours_on_day - self.contract_id.resource_calendar_id.break_time
                #
                #
                #         ##################### this is for team lead who don't have break time and will get extra OT on morning time and break time
                #         no_hr_extra = 0
                #         if self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids and not self.contract_id.resource_calendar_id.break_time and working_actual_hours_on_day > 4:
                #
                #             ######### - 1 to remove break time, they don't have break time but break time get another rate
                #
                #             # print "CHECK OT STRCTURE"
                #             # print attendance.check_in
                #             date_time_check_in = datetime.strptime(attendance.check_in,DATETIME_FORMAT)
                #             date_time_check_out = datetime.strptime(attendance.check_out, DATETIME_FORMAT)
                #             # start_extra_time = self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[0].start_time
                #             # start_extra_time = self.get_time_from_float(start_extra_time)
                #             start_time = datetime.strptime('01:00:00', '%H:%M:%S')
                #             end_time_normal = datetime.strptime('10:00:00', '%H:%M:%S')
                #             end_time_1 = datetime.strptime('11:30:00', '%H:%M:%S')
                #             end_time_2 = datetime.strptime('13:00:00', '%H:%M:%S')
                #             start_time = start_time.time()
                #             end_time_normal = end_time_normal.time()
                #             end_time_1 = end_time_1.time()
                #             end_time_2 = end_time_2.time()
                #
                #             start_time_of_date = datetime.combine(start_dt, start_time)
                #             end_time_of_date_normal = datetime.combine(start_dt, end_time_normal)
                #             end_time_of_date_1 = datetime.combine(start_dt, end_time_1)
                #             end_time_of_date_2 = datetime.combine(start_dt, end_time_2)
                #             # print start_time_of_date
                #
                #             ######### only if check in less than start time of the day, and define rule start_time not be zero mean will have extra for morning time
                #             if date_time_check_in < start_time_of_date and self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[0].start_time:
                #
                #                 ############ deduct to add hr_extra next line
                #                 working_actual_hours_on_day = working_actual_hours_on_day - 1
                #                 no_hr_extra = (start_time_of_date - date_time_check_in) + timedelta(hours=1)
                #                 # print no_hr_extra
                #                 no_hr_extra = (self.get_float_from_time(str(no_hr_extra)) * self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[0].rate) / working_hr
                #                 # print no_hr_extra
                #                 # print "END CHECK OT STRUCTURE--MORNING"
                #
                #             ######### only if check out not end ot time, and define rule end_time not be zero mean will have extra for evening time
                #             if date_time_check_out != end_time_of_date_1 and date_time_check_out != end_time_of_date_2 and \
                #                     self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[
                #                         0].end_time:
                #
                #
                #                 ############# extra from 17:00 to check out
                #                 no_hr_extra = (date_time_check_out - end_time_of_date_normal)
                #                 # print no_hr_extra
                #                 no_hr_extra = (self.get_float_from_time(str(no_hr_extra)) *
                #                                self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[
                #                                    0].rate) / working_hr
                #                 # print no_hr_extra
                #                 # print "END CHECK OT STRUCTURE--EVENING"
                #
                #         ################ This is for anyone who don't have break time in working schedule but would like to manage break time by each attendance day
                #         if not self.contract_id.resource_calendar_id.break_time and attendance.is_break_time:
                #             working_actual_hours_on_day = working_actual_hours_on_day - 1
                #
                #         ############### This is normal working day 17:00 and before 18:30 and has some extra
                #         if attendance.check_out < str(finish_time_1_25_3_date) or no_hr_extra:
                #
                #             if working_hours_on_day:
                #                 # print working_actual_hours_on_day
                #                 # print
                #
                #                 if self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids and self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[0].start_time and not self.contract_id.resource_calendar_id.break_time and no_hr_extra:
                #                     ############### this is for team leader has extra rate for noon and morning
                #                     # print "UPDATE-1"
                #                     val_overtime1 += (no_hr_extra + 1)
                #                     val_overtime1_hr += working_actual_hours_on_day
                #
                #                 elif self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids and self.contract_id.overtime_structure_id.hr_ov_structure_rule_attendance_ids[0].end_time and not self.contract_id.resource_calendar_id.break_time and no_hr_extra:
                #                     ############### this is for team leader has extra rate for evening only, not for noon
                #                     # print "UPDATE-2"
                #                     val_overtime1 += (no_hr_extra + 1.125)
                #                     val_overtime1_hr += working_actual_hours_on_day
                #                 else:
                #                     # print "UPDATE-3"
                #                     ############### This is team member of no break time, normal has break time then working_actual_hours_on_day will be difference
                #                     val_overtime1 += working_actual_hours_on_day / working_hr
                #                     val_overtime1_hr += working_actual_hours_on_day
                #             else:
                #                 ######this is weekend (sunday)
                #                 val_overtime4 += 1
                #
                #         ############# This is ot from 18:30 before 20:00, no extra
                #         elif attendance.check_out < str(finish_time_1_5_date):
                #
                #             if working_hours_on_day:
                #                 val_overtime2 += 1
                #
                #             else:
                #                 ######this is weekend (sunday)
                #                 val_overtime4 += 1
                #
                #
                #         ################ this is from 20:00 onward and no extra
                #         else:
                #             if working_hours_on_day:
                #                 val_overtime3 += 1
                #             else:
                #                 ######this is weekend (sunday)
                #                 val_overtime4 += 1
                #
                #
                #
                # else:
                #     # print "NOT-FOUND"
                #     continue

            # print "Total OT"
            # print val_overtime1
            # print val_overtime2
            # print val_overtime3
            # print val_overtime4
            # ทำงาน 8.00-17.00น.  เอาค่าแรงรายวันคูณ 1

            # print "----------Start CHECK Working Hour"
            # print working_actual_hours_on_day
            # print working_hr
            # print "----------END CHECK Working Hour"

            overtime1 = {
                'name': 'วันธรรมดา-1',
                'sequence': 11,
                'code': 'Overtime1',
                'number_of_days': val_overtime1,
                'number_of_hours': val_overtime1_hr,
                'contract_id': self.contract_id.id,
            }

            # ทำงาน 8.00-18.30น.  เอาค่าแรงรายวันคูณ 1.25
            overtime2 = {
                'name': 'OT-วันธรรมดา-1.5',
                'sequence': 12,
                'code': 'Overtime2',
                'number_of_days': val_overtime2,
                'number_of_hours': val_overtime2_hours,
                'contract_id': self.contract_id.id,
            }

            # ทำงาน 8.00-20.00น. เอาค่าแรงรายวันคูณ 1.50
            overtime3 = {
                'name': 'OT-วันหยุด-2',
                'sequence': 13,
                'code': 'Overtime3',
                'number_of_days': val_overtime3,
                'number_of_hours': val_overtime3 * 8,
                'contract_id': self.contract_id.id,
            }

            # ทำงานวันหยุด 8.00-18.30 เอาค่าแรงรายวันคูณ 3
            overtime4 = {
                'name': 'OT-วันหยุด-3',
                'sequence': 14,
                'code': 'Overtime4',
                'number_of_days': val_overtime4,
                'number_of_hours': val_overtime4 * 8,
                'contract_id': self.contract_id.id,
            }

        return overtime1, overtime2, overtime3, overtime4

    # refund ##################
    @api.multi
    def refund_sheet(self):
        print('def refund_sheet')
        total_revenue_summary_net = 0.0
        total_revenue_summary_net1 = 0.0
        total_revenue_summary_for_tax = 0.0
        sum_total_tax = 0.0
        total_tax_paid = 0.0
        total_tax_paid1 = 0.0
        revenue_summary_for_tax = 0.0
        revenue_summary_for_tax1 = 0.0
        total_sso_paid = 0.0
        total_sso_paid1 = 0.0
        # sum_data = 0.0
        total_tax_one_paid = 0.0

        for payslip in self:
            payslip.refund = True
            payslip.credit_note = True

            if payslip.contract_id:
                total_revenue_summary_net = payslip.contract_id.total_revenue_summary_net
                total_revenue_summary_for_tax = payslip.contract_id.total_revenue_summary_for_tax
                total_tax_paid = payslip.contract_id.total_tax_paid
                total_sso_paid = payslip.contract_id.total_sso_paid
                total_tax_one_paid = payslip.contract_id.total_tax_one_paid
                total_revenue_summary_for_tax_one = payslip.total_revenue_summary_for_tax_one

            sum_total_tax = payslip.sum_total_tax
            sum_total_tax_one = payslip.get_summary_for_tax_onetime()

            for line in payslip.line_ids:
                if line.code == 'NET':
                    if payslip.credit_note:
                        total_revenue_summary_net1 += (line['amount'])

                if line.code == 'sso':
                    if payslip.credit_note:
                        total_sso_paid1 -= (line['amount'])

                if line.code == 'tax':
                    if payslip.credit_note:
                        total_tax_paid1 -= (line['amount'])

                # if line.code == 'deduct06':
                #     if payslip.credit_note:
                #         sum_data -= (line['amount'])

            total_revenue_summary_net = total_revenue_summary_net - total_revenue_summary_net1
            total_revenue_summary_for_tax = total_revenue_summary_for_tax - ( sum_total_tax + sum_total_tax_one)
            total_sso_paid = total_sso_paid - total_sso_paid1
            total_tax_paid = total_tax_paid - total_tax_paid1
            total_tax_one_paid = total_tax_one_paid - payslip.tax_one_paid
            total_revenue_summary_for_tax_one = total_revenue_summary_for_tax_one - payslip.summary_for_tax_one

            # print('total_revenue_summary_net : ',total_revenue_summary_net)
            # print('total_revenue_summary_for_tax : ',total_revenue_summary_for_tax)
            # print('total_sso_paid : ',total_sso_paid)
            # print('total_tax_paid : ',total_tax_paid)
            # print('total_tax_one_paid : ',total_tax_one_paid)
            # print('total_revenue_summary_for_tax_one : ',total_revenue_summary_for_tax_one)

        self.write({'total_revenue_summary_net': total_revenue_summary_net,
                    'revenue_summary_for_tax': revenue_summary_for_tax,
                    'total_revenue_summary_for_tax': total_revenue_summary_for_tax,
                    'total_tax_paid': total_tax_paid,
                    'total_sso_paid': total_sso_paid,
                    'state': 'draft',
                    'credit_note': False,
                    'total_tax_one_paid': total_tax_one_paid,
                    'total_revenue_summary_for_tax_one': total_revenue_summary_for_tax_one,
                    })

        self.contract_id.write({'total_revenue_summary_net': total_revenue_summary_net,
                                'total_revenue_summary_for_tax': total_revenue_summary_for_tax,
                                'total_tax_paid': total_tax_paid,
                                'total_sso_paid': total_sso_paid,
                                'revenue_summary_for_tax': revenue_summary_for_tax,
                                'total_tax_one_paid': total_tax_one_paid,
                                'total_revenue_summary_for_tax_one': total_revenue_summary_for_tax_one,
                                })