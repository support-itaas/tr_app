#-*-coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from odoo import api, tools
from odoo.osv import  osv
from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class resource_calendar(models.Model):
    _inherit = "resource.calendar"

    @api.multi
    def working_hours_on_day(self, day):
        # print("def working_hours_on_day")
        """ Used in hr_payroll/hr_payroll.py

        :deprecated: Odoo saas-3. Use get_working_hours_of_date instead. Note:
        since saas-3, take hour/minutes into account, not just the whole day."""
        # print "GOTO WHOD"

        # print
        # "working_hours_on_day"
        # print
        # day
        # print
        # isinstance(day, datetime.datetime)

        # if isinstance(day, datetime.datetime):
            # print "GO-1"
            # day = day.replace(hour=0, minute=0)
        # return self.get_working_hours_of_date(start_dt=day)

        return 8

class hr_contract(models.Model):
    _inherit = "hr.contract"

    work_age = fields.Integer(string="Age")
    work_age_full = fields.Char(string="Age Year-Month-Day")
    wage_type = fields.Selection([('daily', 'รายวัน'), ('monthly', 'รายเดือน'), ('hour', 'รายชั่วโมง')],
                                 string="ประเภทเงินเดือน", default='daily')
    leave_tag = fields.Selection([('office', 'สำนักงาน'), ('onsite', 'หน้างาน'), ('mix', 'ผสม')], string="สิทธิการลา",
                                 default='onsite')
    total_revenue_summary_net = fields.Float(string='รายได้สุทธิสะสม')
    total_revenue_summary_for_tax = fields.Float(string='รายได้สำหรับคิดภาษีบุคคลธรรมดาสะสม')
    total_tax_paid = fields.Float(string='ภาษีบุคคลธรรมดา หัก ณ ที่จ่ายสะสม')
    total_sso_paid = fields.Float(string='ประกันสังคมจ่ายสะสม')
    exclude_sso = fields.Boolean(string="Exclude SSO")
    payroll_year_record_ids = fields.One2many('hr.payroll.yearly.record','contract_id',string='Payroll Yearly Record')

    pvd_rate = fields.Float(string='PVD Rate')
    summary_pvd = fields.Float(string='Summary PVD')
    pvd_start_date = fields.Date(string='PVD Start')
    pvd_end_date = fields.Date(string='PVD End')

    submit_sso = fields.Boolean(string='เคยยื่นผู้ประกันตนแล้ว')
    end_sso = fields.Selection([('type1', '1.ลาออก/ละทิ้งหน้าที่โดยมีการติดต่อนายจ้างภายใน 6 วันทำงานติดต่อกัน')
                                   ,('type2', '2.สิ้นสุดระยะเวลาการจ้าง')
                                   ,('type3', '3.เลิกจ้าง/โครงการเกษียณก่อนกำหนด')
                                   ,('type4', '4.เกษียณอายุ')
                                   ,('type5', '5.ไล่ออก/ปลดออก/ให้ออกเนื่องจากการกระะทำความผิด/ละทิ้งหน้าโดยไม่มีการติดต่อนายจ้างภายใน 7 วันทำงานติดต่อกัน')
                                   ,('type6', '6.ตาย')
                                   ,('type7', '7.โอนย้ายสาขา')]
                               , string='สิ้นสุดผู้ประกันตน',)
    con_branch_id = fields.Many2one('contract.branch', string='Contract Branch')
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")

    @api.model
    def create(self, vals):
        if vals['employee_id']:
            employee_id = self.env['hr.employee'].browse(vals['employee_id'])

            if not vals['operating_unit_id']:
                vals['operating_unit_id'] = employee_id.operating_unit_id.id
            else:
                operating_unit_id = self.env['operating.unit'].browse(vals['operating_unit_id'])
                employee_id.update({
                    'operating_unit_id': operating_unit_id.id
                })

        return super(hr_contract, self).create(vals)


    def write(self, vals):
        if 'operating_unit_id' in vals:
            if vals['operating_unit_id']:
                operating_unit_id = self.env['operating.unit'].browse(vals['operating_unit_id'])
                self.employee_id.update({
                    'operating_unit_id': operating_unit_id.id
                })
        return super(hr_contract, self).write(vals)

    # @api.onchange('operating_unit_id')
    # def _onchange_operating_unit_id(self):
    #     print('_onchange_operating_unit_id')
    #     if self.employee_id:
    #         self.employee_id.write({
    #             'operating_unit_id': self.operating_unit_id.id,
    #         })

    @api.multi
    def reset_salary_stat_all(self):
        for rec in self.env['hr.contract'].search([]):
            lastyear = datetime.today() - relativedelta(years=1)
            yearly_val = {
                'year': lastyear.year,
                'total_revenue_summary_net': rec.total_revenue_summary_net,
                'total_revenue_summary_for_tax': rec.total_revenue_summary_for_tax,
                'total_tax_paid': rec.total_tax_paid,
                'total_sso_paid': rec.total_sso_paid,
                'contract_id': rec.id,
                'total_tax_one_paid': rec.total_tax_one_paid,
            }
            if self.env['hr.payroll.yearly.record'].search(
                    [('year', '=', lastyear.year), ('contract_id', '=', rec.id)]):
                raise UserError(_("รายการได้บันทึกไปแล้ว หากต้องการแก้ไขให้ลบรายการก่อนหรือปรับปรุงรายการโดยตรง"))

            else:
                record_id = self.env['hr.payroll.yearly.record'].create(yearly_val)
                if record_id:
                    rec.total_revenue_summary_net = 0.0
                    rec.total_revenue_summary_for_tax = 0.0
                    rec.total_tax_paid = 0.0
                    rec.total_sso_paid = 0.0
                    rec.total_tax_one_paid = 0.0
                else:
                    raise UserError(_("ไม่สามารถบันทึกได้"))

    @api.multi
    def reset_salary_stat(self):

        lastyear = datetime.today() - relativedelta(years=1)

        yearly_val = {
            'year': lastyear.year,
            'total_revenue_summary_net': self.total_revenue_summary_net,
            'total_revenue_summary_for_tax': self.total_revenue_summary_for_tax,
            'total_tax_paid': self.total_tax_paid,
            'total_sso_paid': self.total_sso_paid,
            'total_tax_one_paid': self.total_tax_one_paid,
            'contract_id': self.id,
        }
        if self.env['hr.payroll.yearly.record'].search([('year','=',lastyear.year),('contract_id','=',self.id)]):
            raise UserError(_("รายการได้บันทึกไปแล้ว หากต้องการแก้ไขให้ลบรายการก่อนหรือปรับปรุงรายการโดยตรง"))

        else:
            record_id = self.env['hr.payroll.yearly.record'].create(yearly_val)
            if record_id:
                self.total_revenue_summary_net = 0.0
                self.total_revenue_summary_for_tax = 0.0
                self.total_tax_paid = 0.0
                self.total_sso_paid = 0.0
                self.total_tax_one_paid = 0.0
            else:
                raise UserError(_("ไม่สามารถบันทึกได้"))

    @api.model
    def update_work_ages(self):
        """Updates age field for all partners once a day"""
        for rec in self.env['hr.contract'].search([]):
            if rec.date_start:
                d1 = datetime.strptime(rec.date_start, "%Y-%m-%d").date()
                d2 = date.today()
                current_year = rec.work_age
                rec.work_age = relativedelta(d2, d1).years

                age_year = str(rec.work_age)
                age_month = str(relativedelta(d2, d1).months)
                age_day = str(relativedelta(d2, d1).days)
                rec.work_age_full = (age_year or '') + ' ปี ' + (age_month or '') + ' เดือน ' + (age_day or '') + ' วัน'

    @api.model
    def update_holiday(self):

        employee_tags = self.env['hr.employee.category'].search([])
        emp_ids = False
        holiday_ids = False

        holiday_obj = self.env['hr.holidays']

        if self.employee_id:
            for tag in self.employee_id.category_ids:
                # print tag.name
                holiday_ids = self.env['hr.holidays'].search(
                    [('category_id', '=', tag.id), ('holiday_type', '=', 'category'), ('state', '=', 'validate')])

                if holiday_ids:
                    for holiday in holiday_ids:
                        # print "has employee"
                        emp_id = self.employee_id
                        find_holiday = self.env['hr.holidays'].search(
                            [('holiday_status_id', '=', holiday.holiday_status_id.id),
                             ('holiday_type', '=', 'employee'), ('employee_id', '=', emp_id.id)])

                        if not find_holiday:

                            # if holiday.holiday_status_id.first_year_holiday_flag and (emp_id.contract_id.work_age == 1):
                            #     d1 = datetime.strptime(emp_id.contract_id.date_start, "%Y-%m-%d").date()
                            #     start_m = int(d1.strftime('%m'))
                            #     if start_m == 1 or start_m == 2:
                            #         number_of_day = number_of_day
                            #     elif start_m == 3 or start_m == 4:
                            #         number_of_day = number_of_day - 1
                            #     elif start_m == 5 or start_m == 6:
                            #         number_of_day = number_of_day - 2
                            #     elif start_m == 7 or start_m == 8:
                            #         number_of_day = number_of_day - 3
                            #     elif start_m == 9 or start_m == 10:
                            #         number_of_day = number_of_day - 4
                            #     elif start_m == 11 or start_m == 12:
                            #         number_of_day = number_of_day - 5
                            #
                            # if holiday.holiday_status_id.five_year_holiday_flag and (emp_id.contract_id.work_age == 5):
                            #     d1 = datetime.today().date()
                            #     start_m = int(d1.strftime('%m'))
                            #     if start_m == 1:
                            #         number_of_day = number_of_day
                            #     else:
                            #         number_of_day = 0

                            vals = {
                                'name': holiday.name,
                                'type': holiday.type,
                                'holiday_type': 'employee',
                                'holiday_status_id': holiday.holiday_status_id.id,
                                'date_from': False,
                                'date_to': False,
                                'notes': False,
                                'number_of_days_temp': holiday.number_of_days_temp,
                                'parent_id': holiday.id,
                                'employee_id': emp_id.id,
                                'state': 'validate'
                            }

                            # print "create holiday for employee"
                            holiday_id = holiday_obj.create(vals)
                            holiday_id.state = 'validate'



        else:
            if employee_tags:
                for tag in employee_tags:
                    # print tag.name
                    holiday_ids = self.env['hr.holidays'].search(
                        [('category_id', '=', tag.id), ('holiday_type', '=', 'category'), ('state', '=', 'validate')])

                    if holiday_ids:
                        for holiday in holiday_ids:
                            emp_ids = tag.employee_ids.ids
                            if emp_ids:
                                for emp in emp_ids:
                                    emp_id = self.env['hr.employee'].browse(emp)
                                    # print emp_id.name
                                    find_holiday = self.env['hr.holidays'].search(
                                        [('holiday_status_id', '=', holiday.holiday_status_id.id),
                                         ('holiday_type', '=', 'employee'),
                                         ('employee_id', '=', emp_id.id)])

                                    if not find_holiday:

                                        # if holiday.holiday_status_id.first_year_holiday_flag and (
                                        #     emp_id.contract_id.work_age == 1):
                                        #
                                        #     d1 = datetime.strptime(emp_id.contract_id.date_start, "%Y-%m-%d").date()
                                        #     start_m = int(d1.strftime('%m'))
                                        #     if start_m == 1 or start_m == 2:
                                        #         number_of_day = number_of_day
                                        #     elif start_m == 3 or start_m == 4:
                                        #         number_of_day = number_of_day - 1
                                        #     elif start_m == 5 or start_m == 6:
                                        #         number_of_day = number_of_day - 2
                                        #     elif start_m == 7 or start_m == 8:
                                        #         number_of_day = number_of_day - 3
                                        #     elif start_m == 9 or start_m == 10:
                                        #         number_of_day = number_of_day - 4
                                        #     elif start_m == 11 or start_m == 12:
                                        #         number_of_day = number_of_day - 5
                                        #
                                        # if holiday.holiday_status_id.five_year_holiday_flag and (
                                        #     emp_id.contract_id.work_age == 5):
                                        #     d1 = datetime.today().date()
                                        #     start_m = int(d1.strftime('%m'))
                                        #     if start_m == 1:
                                        #         number_of_day = number_of_day
                                        #     else:
                                        #         number_of_day = 0

                                        vals = {
                                            'name': holiday.name,
                                            'type': holiday.type,
                                            'holiday_type': 'employee',
                                            'holiday_status_id': holiday.holiday_status_id.id,
                                            'date_from': False,
                                            'date_to': False,
                                            'notes': False,
                                            'number_of_days_temp': holiday.number_of_days_temp,
                                            'parent_id': holiday.id,
                                            'employee_id': emp_id.id,
                                            'state': 'validate'
                                        }

                                        holiday_id = holiday_obj.create(vals)
                                        holiday_id.state = 'validate'

    @api.multi
    def apply_holiday(self):

        employee_tags = self.env['hr.employee.category'].search([])
        emp_ids = False
        holiday_ids = False

        holiday_obj = self.env['hr.holidays']

        if self.employee_id:
            for tag in self.employee_id.category_ids:
                # print tag.name
                # print self.env.user.company_id.name
                holiday_ids = self.env['hr.holidays'].search(
                    [('category_id', '=', tag.id), ('holiday_type', '=', 'category'), ('state', '=', 'validate')])
                if holiday_ids:
                    for holiday in holiday_ids:
                        # print holiday.name
                        # print holiday.company_id.name

                        emp_id = self.employee_id
                        find_holiday = self.env['hr.holidays'].search(
                            [('holiday_status_id', '=', holiday.holiday_status_id.id),
                             ('holiday_type', '=', 'employee'), ('employee_id', '=', emp_id.id)])

                        if not find_holiday:
                            # if holiday.holiday_status_id.first_year_holiday_flag and (emp_id.contract_id.work_age == 1):
                            #     d1 = datetime.strptime(emp_id.contract_id.date_start, "%Y-%m-%d").date()
                            #     start_m = int(d1.strftime('%m'))
                            #     if start_m == 1 or start_m == 2:
                            #         number_of_day = number_of_day
                            #     elif start_m == 3 or start_m == 4:
                            #         number_of_day = number_of_day - 1
                            #     elif start_m == 5 or start_m == 6:
                            #         number_of_day = number_of_day - 2
                            #     elif start_m == 7 or start_m == 8:
                            #         number_of_day = number_of_day - 3
                            #     elif start_m == 9 or start_m == 10:
                            #         number_of_day = number_of_day - 4
                            #     elif start_m == 11 or start_m == 12:
                            #         number_of_day = number_of_day - 5
                            #
                            # if holiday.holiday_status_id.five_year_holiday_flag and (emp_id.contract_id.work_age == 5):
                            #     d1 = datetime.today().date()
                            #     start_m = int(d1.strftime('%m'))
                            #     if start_m == 1:
                            #         number_of_day = number_of_day
                            #     else:
                            #         number_of_day = 0

                            vals = {
                                'name': holiday.name,
                                'type': holiday.type,
                                'holiday_type': 'employee',
                                'holiday_status_id': holiday.holiday_status_id.id,
                                'date_from': False,
                                'date_to': False,
                                'notes': False,
                                'number_of_days_temp': holiday.number_of_days_temp,
                                'parent_id': holiday.id,
                                'employee_id': emp_id.id,
                                'state': 'validate'
                            }

                            # print "create holiday for employee"
                            holiday_id = holiday_obj.create(vals)
                            holiday_id.state = 'validate'



        else:
            if employee_tags:
                for tag in employee_tags:
                    # print tag.name
                    holiday_ids = self.env['hr.holidays'].search(
                        [('category_id', '=', tag.id), ('holiday_type', '=', 'category'), ('state', '=', 'validate')])

                    if holiday_ids:
                        for holiday in holiday_ids:
                            emp_ids = tag.employee_ids.ids
                            if emp_ids:
                                for emp in emp_ids:
                                    emp_id = self.env['hr.employee'].browse(emp)
                                    # print emp_id.name
                                    find_holiday = self.env['hr.holidays'].search(
                                        [('holiday_status_id', '=', holiday.holiday_status_id.id),
                                         ('holiday_type', '=', 'employee'),
                                         ('employee_id', '=', emp_id.id)])

                                    if not find_holiday:

                                        # if holiday.holiday_status_id.first_year_holiday_flag and (
                                        #             emp_id.contract_id.work_age == 1):
                                        #
                                        #     d1 = datetime.strptime(emp_id.contract_id.date_start, "%Y-%m-%d").date()
                                        #     start_m = int(d1.strftime('%m'))
                                        #     if start_m == 1 or start_m == 2:
                                        #         number_of_day = number_of_day
                                        #     elif start_m == 3 or start_m == 4:
                                        #         number_of_day = number_of_day - 1
                                        #     elif start_m == 5 or start_m == 6:
                                        #         number_of_day = number_of_day - 2
                                        #     elif start_m == 7 or start_m == 8:
                                        #         number_of_day = number_of_day - 3
                                        #     elif start_m == 9 or start_m == 10:
                                        #         number_of_day = number_of_day - 4
                                        #     elif start_m == 11 or start_m == 12:
                                        #         number_of_day = number_of_day - 5
                                        #
                                        # if holiday.holiday_status_id.five_year_holiday_flag and (
                                        #     emp_id.contract_id.work_age == 5):
                                        #     d1 = datetime.today().date()
                                        #     start_m = int(d1.strftime('%m'))
                                        #     if start_m == 1:
                                        #         number_of_day = number_of_day
                                        #     else:
                                        #         number_of_day = 0

                                        vals = {
                                            'name': holiday.name,
                                            'type': holiday.type,
                                            'holiday_type': 'employee',
                                            'holiday_status_id': holiday.holiday_status_id.id,
                                            'date_from': False,
                                            'date_to': False,
                                            'notes': False,
                                            'number_of_days_temp': holiday.number_of_days_temp,
                                            'parent_id': holiday.id,
                                            'employee_id': emp_id.id,
                                            'state': 'validate'
                                        }

                                        holiday_id = holiday_obj.create(vals)
                                        holiday_id.state = 'validate'

    def working_hours_on_day(self, date):
        calendar_id = self.resource_calendar_id
        working_hours_on_day = 0.0
        day_of_week = int(date.strftime('%w')) - 1
        # print('day_of_week : ', day_of_week)
        if day_of_week == -1:
            day_of_week = 6
        domain_calendar = [('calendar_id','=', calendar_id.id),
                           ('dayofweek', '=', day_of_week)
                           ]
        # print('domain_calendar : ',domain_calendar)
        calendar = self.env['resource.calendar.attendance'].sudo().search(domain_calendar, limit=1)
        # print('calendar : ',calendar)
        if not calendar:
            working_hours_on_day = 0.0
            # working_hours_on_day = self.employee_id.get_day_work_hours_count(date, calendar=calendar)
            # print('working_hours_on_day: ',working_hours_on_day)
        else:
            hour_from = calendar.hour_from
            hour_to = calendar.hour_to
            break_time = calendar_id.break_time
            # print('hour_from : ',hour_from)
            # print('hour_to : ',hour_to)
            # print('break_time : ',break_time)
            if hour_from <= hour_to:
                working_hours_on_day = hour_to - hour_from - break_time
            else:
                hour_from = 24 - hour_from
                working_hours_on_day = (hour_to + hour_from) - break_time

        return working_hours_on_day


class hr_payroll_yearly_record(models.Model):
    _name = "hr.payroll.yearly.record"

    name = fields.Many2one('hr.employee', related='contract_id.employee_id',string='Employee')
    contract_id = fields.Many2one('hr.contract',string='Contract')
    year = fields.Integer(string='Year')
    total_revenue_summary_net = fields.Float(string='รายได้สุทธิสะสม')
    total_revenue_summary_for_tax = fields.Float(string='รายได้สำหรับคิดภาษีบุคคลธรรมดาสะสม')
    total_tax_paid = fields.Float(string='ภาษีบุคคลธรรมดา หัก ณ ที่จ่ายสะสม')
    total_sso_paid = fields.Float(string='ประกันสังคมจ่ายสะสม')

class resource_calendar(models.Model):
    _inherit = 'resource.calendar'

    break_time = fields.Float(string='Break Time (Hr)')