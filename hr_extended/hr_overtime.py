#-*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-2015 Asmaa Aly.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import itertools
from lxml import etree
import time
import pytz
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import UserError, ValidationError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # print strdate
    return datetime.strptime(strdate, DATETIME_FORMAT)

class hr_overtime(models.Model):
    _name = "hr.overtime"
    _description = "HR Overtime"
    _inherit = "mail.thread"

    def _employee_get(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    def _employee_get_original(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.one
    @api.depends('from_date','to_date')
    def _compute_total(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        diff_day = 0.0
        diff_day_minutes = 0.0
        if self.from_date and self.to_date:
            from_date = datetime.strptime(self.from_date, DATETIME_FORMAT)
            to_date = datetime.strptime(self.to_date, DATETIME_FORMAT)
            timedelta = to_date - from_date
            diff_day = (float(timedelta.seconds) / 86400) * 24
            diff_day_minutes = (float(timedelta.seconds) / 60)
        self.total_time = diff_day
        self.total_time_minutes = diff_day_minutes


    name = fields.Char(string="Name", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,default=_employee_get_original)
    department = fields.Char(related='employee_id.department_id.name',store=True)
    reason = fields.Text(string="Overtime/Reject Reason")
    from_date = fields.Datetime(srting="From Date", required=True)
    to_date = fields.Datetime(srting="To Date", required=True)
    approve_ot_time = fields.Float(string="Approve OT Time (Rate Applied)", digits=(16, 2),readonly=True)
    total_time = fields.Float(string="Total Time", compute='_compute_total',digits=(16, 2),store=True)
    total_time_minutes = fields.Float(string="Total Time Minutes", digits=(16, 2),compute='_compute_total', store=True)
    # user_id = fields.Many2one('hr.employee',string="Requester Name",required=True,default=_employee_get)
    request_user = fields.Many2one('hr.employee', string="Requester Name", default=_employee_get)
    request_date = fields.Date(string="Request date",required=True,default=datetime.today())
    type = fields.Selection([
        ('working_day', 'โอทีวันทำงานปกติ'),
        ('weekend', 'โอทีวันหยุด'),
        ('day_off_charge_daily',' ค่าจ้างทำงานวันหยุด (รายวัน)'),
        ('day_off_charge_monthly', 'ค่าจ้างทำงานวันหยุด (รายเดือน)'),
        ('compensate_holiday', 'สลับวันหยุดประพณี'),
        ('compensate_weekly_shift', 'สลับวันหยุดประจำสัปดาห์'),
        ('compensate_day', 'สลับวันหยุด'),
        ('accomulate_holiday', 'ทำงานสะสมวันหยุด'),
    ], string="Overtime Type",default="working_day")

    state = fields.Selection([('draft','Draft'),
                              ('submit','Submitted'),
                              ('approve','Approved'),
                              ('reject', 'Rejected'),
                              ], string="Status", default= "draft", track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id
    )
    leave_type = fields.Many2one('hr.holidays.status', string="Leave type")

    @api.multi
    def create_holiday(self):
        # print "create holiday"
        holiday_obj = self.env['hr.holidays']
        # print self.leave_type.id
        holiday_ids = self.env['hr.holidays'].search(
            [('holiday_type', '=', 'category'),('state', '=', 'validate'),('holiday_status_id', '=', self.leave_type.id),('company_id', '=', self.env.user.company_id.id)])
        if holiday_ids:
            # print "found holiday approve by tag"
            for holiday in holiday_ids:
                # find_holiday = self.env['hr.holidays'].search([('holiday_status_id', '=', self.leave_type.id), ('holiday_type', '=', 'employee'),('employee_id', '=', self.employee_id.id), ('company_id', '=', self.env.user.company_id.id)])
                # if not find_holiday:
                vals = {
                    'name': holiday.name,
                    'type': holiday.type,
                    'holiday_type': 'employee',
                    'holiday_status_id': self.leave_type.id,
                    'date_from': False,
                    'date_to': False,
                    'notes': False,
                    'number_of_days_temp': self.approve_ot_time/8,
                    'parent_id': holiday.id,
                    'employee_id': self.employee_id.id,
                    'state': 'validate'
                }
                # print holiday.holiday_status_id.id
                # print "create holiday for employee"
                holiday_id = holiday_obj.create(vals)
                holiday_id.state = 'validate'

    def cal_ot(self,re_call):
        # print "calculate actual ot time"
        actual_ot_time = 0.0
        hour_to = 0.0
        hour_from = 0.0
        user_pool = self.env['res.users']
        contract_obj = self.env['hr.contract']
        attendance_obj = self.env['hr.attendance']
        working_hours_obj = self.env['resource.calendar']
        tz = pytz.timezone('Asia/Bangkok')
        tz_base = pytz.timezone(self._context.get('tz') or 'UTC')
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        TIME_FORMAT = "%H:%M:%S"
        start_time = datetime.strptime('00:00:00', '%H:%M:%S')
        finish_time = datetime.strptime('23:59:59', '%H:%M:%S')
        start_time = start_time.time()
        finish_time = finish_time.time()
        overtime_from_date_time = datetime.strptime(self.from_date, '%Y-%m-%d %H:%M:%S')
        overtime_to_date_time = datetime.strptime(self.to_date, '%Y-%m-%d %H:%M:%S')
        overtime_from_date = overtime_from_date_time.date()
        overtime_to_date = overtime_to_date_time.date()

        def is_in_working_schedule(date_in, working_hours_id):
            found = False
            # print "date_in"
            # print type(date_in)
            if type(date_in) is datetime:
                # print "if date time"
                working_hours = working_hours_obj.browse(working_hours_id)
                for line in working_hours.attendance_ids:
                    if int(line.dayofweek) == date_in.weekday():
                        found = True
                        break
            return found

        def get_end_hour_of_the_day(date_in, working_hours_id):
            hour = 0.0

            if type(date_in) is datetime:

                working_hours = working_hours_obj.browse(working_hours_id)
                for line in working_hours.attendance_ids:
                    # First assign to hour

                    if int(line.dayofweek) == date_in.weekday() and hour == 0.0:
                        hour = line.hour_to

                    elif int(line.dayofweek) == date_in.weekday() and hour != 0.0 and line.hour_from > hour:
                        hour = line.hour_to

            return hour

        def get_start_hour_of_the_day(date_in, working_hours_id):
            hour = 0.0
            if type(date_in) is datetime:

                working_hours = working_hours_obj.browse(working_hours_id)
                for line in working_hours.attendance_ids:

                    # First assign to hour
                    if int(line.dayofweek) == date_in.weekday() and hour == 0.0:
                        hour = line.hour_from

                    # Other assignments to hour
                    # No need for this part but it's a fail safe condition
                    elif int(line.dayofweek) == date_in.weekday() and hour != 0.0 and line.hour_to < hour:
                        hour = line.hour_from

            return hour

        def get_time_from_float(float_time):
            str_time = str(float_time)
            str_hour = str_time.split('.')[0]
            str_minute = ("%2d" % int(str(float("0." + str_time.split('.')[1]) * 60).split('.')[0])).replace(' ', '0')
            str_ret_time = str_hour + ":" + str_minute + ":00"
            str_ret_time = datetime.strptime(str_ret_time, TIME_FORMAT).time()
            return str_ret_time

        def get_float_from_time(time_type):
            # print "original time"
            # print time_type

            signOnP = [int(n) for n in time_type.split(":")]

            # if signOnP < 30 then it will 00, if more then 30 then it will 30
            if signOnP[1] < 30:
                signOnP[1] = 0
            else:
                signOnP[1] = 30

            signOnH = signOnP[0] + signOnP[1] / 60.0
            return signOnH

        # find working hour_from and hour_to
        if is_in_working_schedule(strToDatetime(self.from_date), self.employee_id.contract_id.resource_calendar_id.id):
            hour_to = get_end_hour_of_the_day(
                pytz.utc.localize(datetime.strptime(self.from_date, DATETIME_FORMAT)).astimezone(tz),
                self.employee_id.contract_id.resource_calendar_id.id)
            hour_from = get_start_hour_of_the_day(
                pytz.utc.localize(datetime.strptime(self.from_date, DATETIME_FORMAT)).astimezone(tz),
                self.employee_id.contract_id.resource_calendar_id.id)
            hour_to_time = get_time_from_float(hour_to)
            hour_from_time = get_time_from_float(hour_from)
            # print hour_to
            # print hour_from
            # print hour_to_time
            # print hour_from_time
            # print "working schedule"

        else:

            hour_to = get_end_hour_of_the_day(
                pytz.utc.localize(datetime.strptime(self.from_date, DATETIME_FORMAT)).astimezone(tz) + timedelta(
                    days=2), self.employee_id.contract_id.resource_calendar_id.id)
            hour_from = get_start_hour_of_the_day(
                pytz.utc.localize(datetime.strptime(self.from_date, DATETIME_FORMAT)).astimezone(tz) + timedelta(
                    days=2), self.employee_id.contract_id.resource_calendar_id.id)
            hour_to_time = get_time_from_float(hour_to)
            hour_from_time = get_time_from_float(hour_from)
            # print "none working schedule"
        # start of the day
        start_time_of_the_day = tz.localize(datetime.combine(overtime_from_date, start_time))
        finish_time_of_the_day = tz.localize(datetime.combine(overtime_from_date, finish_time))
        # print "start - finish"
        # print start_time_of_the_day
        # print finish_time_of_the_day
        # start_time_std = tz.localize(datetime.combine(overtime_from_date, hour_from_time)).astimezone(tz_base)
        # finish_time_std = tz.localize(datetime.combine(overtime_from_date, hour_to_time)).astimezone(tz_base)

        for rule in self.employee_id.contract_id.overtime_structure_id.hr_ov_structure_rule_ids:
            # print "Rule"
            # print rule.type
            # print self.type
            if rule.type == self.type:

                search_domain = [
                    ('check_in', '<=', str(finish_time_of_the_day)),
                    ('check_out', '>=', str(start_time_of_the_day)),
                    ('employee_id', '=', self.employee_id.id),
                ]

                attendance_ids = attendance_obj.search(search_domain)
                if attendance_ids:
                    # print "Found Some ATTENDANT"
                    if rule.leave_type:
                        self.leave_type = rule.leave_type.id
                    for attendance in attendance_ids:


                        attendance_datetime = pytz.utc.localize(
                            datetime.strptime(attendance.check_in, DATETIME_FORMAT)).astimezone(tz)
                        # print "Attendant"
                        # print attendance_datetime_in

                        # attendance_datetime_out = pytz.utc.localize(
                        #     datetime.strptime(attendance.check_out, DATETIME_FORMAT)).astimezone(tz)
                        # print "Attendant-out"
                        # print attendance_datetime_out

                        ######### OT from TO
                        # print "OT TO"


                        overtime_to = pytz.utc.localize(datetime.strptime(self.to_date, DATETIME_FORMAT)).astimezone(tz)
                        # print overtime_to
                        overtime_from = pytz.utc.localize(
                            datetime.strptime(self.from_date, DATETIME_FORMAT)).astimezone(tz)

                        # print "OT Fromm"
                        # print overtime_from
                        ######### OT from TO

                        # print attendance.check_in
                        check_in = strToDatetime(attendance.check_in) + relativedelta(hours=7)
                        check_out = strToDatetime(attendance.check_out) + relativedelta(hours=7)
                        ot_start = strToDatetime(self.from_date) + relativedelta(hours=7)
                        ot_end = strToDatetime(self.to_date) + relativedelta(hours=7)
                        # print check_in
                        # print check_out
                        # print ot_start
                        # print ot_end
                        # print attendance.check_out
                        # print self.from_date
                        # print self.to_date
                        # start_overtime = hour_from - rule.begin_before
                        # print start_overtime

                        if check_in < ot_start and check_out > ot_end:
                            # print "BEFORE"

                            diff_time = self.total_time
                            # print self.total_time
                            diff_time = diff_time * rule.rate
                            # print diff_time
                            # print rule.rate
                            actual_ot_time += diff_time
                        elif check_in < ot_start and check_out <= ot_end:
                            # print "11111111"
                            diff_time = check_out - ot_start
                            # print diff_time
                            diff_time = get_float_from_time(str(diff_time)) * rule.rate
                            actual_ot_time += diff_time

                        elif check_in >= ot_start and check_out > ot_end:
                            # print "1"
                            diff_time = ot_end - check_in
                            # print diff_time
                            diff_time = get_float_from_time(str(diff_time)) * rule.rate
                            actual_ot_time += diff_time

                        elif check_in >= ot_start and check_out <= ot_end:
                            # print "1"
                            diff_time = check_out - check_in
                            # print diff_time
                            diff_time = get_float_from_time(str(diff_time)) * rule.rate
                            actual_ot_time += diff_time

                        # elif check_in >= ot_start and check_out <= ot_end:
                        #     diff_time = check_out - check_in
                        #     print diff_time
                        #     diff_time = get_float_from_time(str(diff_time)) * rule.rate
                        #     actual_ot_time += diff_time
                        #
                        # elif check_in >= ot_start and check_out <= ot_end:
                        #     diff_time = check_out - check_in
                        #     print diff_time
                        #     diff_time = get_float_from_time(str(diff_time)) * rule.rate
                        #     actual_ot_time += diff_time


                else:
                    if re_call:
                        raise ValidationError(
                            "วันที่กำลังคำนวนโอทีใหม่ ยังไม่ได้บันทึกเวลา ให้พนักงานตรวจสอบการบันทึกเวลาให้เรียบร้อย")
            # print "update actual ot time"
        # self.actual_ot_time = actual_ot_time
        # print actual_ot_time
        msg_body = "Approve and Calculate OT"
        # self.message_post(body=msg_body, message_type="notification", subtype="mt_comment")
        self.approve_ot_time = actual_ot_time
        # print actual_ot_time
        return actual_ot_time

    @api.multi
    def action_re_cal_after_approve(self):
        re_call = True
        self.cal_ot(re_call)

    @api.multi
    def calculate_approve_ot_time(self):
        re_call = False
        self.cal_ot(re_call)


    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.ov.req') or ' '
        user_ids = []
        if 'employee_id' in values:
            employee_id = self.env['hr.employee'].browse(values.get('employee_id'))

            manager_id = employee_id.parent_id.user_id.id
            # print('manager_id* : ',employee_id.parent_id.user_id.name)
            if manager_id:
                user_ids.append(manager_id)
            manager_department_id = employee_id.department_id.manager_id.user_id.id
            # print('manager_department_id* : ', employee_id.department_id.manager_id.user_id.name)
            if manager_department_id and manager_department_id not in user_ids:
                user_ids.append(manager_department_id)
        res = super(hr_overtime, self).create(values)
        # print('user_ids :', user_ids)

        if user_ids:
            res.message_subscribe_users(user_ids=user_ids)

        return res

    @api.multi
    def action_sumbit(self):
        return self.write({'state': 'submit'})

    @api.multi
    def action_reject(self):
        self.total_time = 0.0
        self.approve_ot_time = 0.0
        return self.write({'state': 'reject'})

    @api.multi
    def action_approve(self):
        # print self.type
        self.calculate_approve_ot_time()
        if self.type == 'accomulate_holiday':
            # print "let cal ot time"
            self.create_holiday()
        return self.write({'state': 'approve'})
    @api.multi
    def action_set_to_draft(self):
        return self.write({'state': 'draft'})

    @api.onchange('user_id')
    def onchange_user_id(self):
        result = {}
        if self.user_id:
            if self.env.user.has_group('hr_extended.group_hr_leave'):
                domain = [('department_id','=',self.user_id.department_id.id)]

            else:
                domain = [('user_id','=',self.env.uid)]

            employee_ids = self.env['hr.employee'].search(domain)
            if employee_ids:
                emps = []
                for emp in employee_ids:
                    emps.append(emp.id)
                result['domain'] = {'employee_id': [('id', 'in', emps)]}

        return result

    @api.one
    @api.constrains('type')
    def _ot_condition(self):
        day_list = []
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        if self.from_date:
            # print self.from_date
            contract_id = self.env['hr.employee'].browse(self.employee_id.id).contract_id.id
            for con in self.env['hr.contract'].browse(contract_id):
                for con_day in con.resource_calendar_id.attendance_ids:
                    day_list.append(con_day.dayofweek)
            request_date = datetime.strptime(self.from_date, DATETIME_FORMAT).date()
            request_day = request_date.weekday()
            # print request_day
            if str(request_day) in day_list:
                # print request_day
                if self.type == 'weekend':
                    raise ValidationError("กรุณาตรวจสอบวันขอโอทีว่าเป็นวันหยุดหรือวันทำงานปรกติ")


    @api.onchange('from_date','employee_id')
    def onchange_from_date(self):
        day_list =[]
        type = ''
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        if self.from_date:
            contract_id = self.env['hr.employee'].browse(self.employee_id.id).contract_id.id
            for con in self.env['hr.contract'].browse(contract_id):
                for con_day in con.resource_calendar_id.attendance_ids:
                    day_list.append(con_day.dayofweek)
            request_date = datetime.strptime(self.from_date, DATETIME_FORMAT).date()
            request_day = request_date.weekday()
            if str(request_day) in day_list:
                type = 'working_day'
            else:
                type = 'weekend'


            self.type = type


class hr_overtime_structure(models.Model):
    _name= "hr.overtime.structure"
    _description = "Overtime Structure"

    name= fields.Char(string="Structure Name")
    code = fields.Char(string="Code", required=True)
    department_ids = fields.Many2many('hr.department', string="Department (s)")
    overtime_method = fields.Selection([
        ('ov_request','According to Request'),
        ('ov_attendance','According to Attendance'),
    ], string="Overtime Method", required=True)
    hr_ov_structure_rule_ids = fields.One2many('hr.ov.structure.rule','hr_overtime_structure_id', string="Overtime Structure Line")
    hr_ov_structure_rule_attendance_ids = fields.One2many('hr.ov.structure.attendance.rule','hr_overtime_structure_id', string="Overtime Structure by Attendance")
    state = fields.Selection([
        ('draft','Draft'),
        ('apply','Applied')
    ], string="Status", default="draft")
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id
    )
    is_check_manager = fields.Boolean(string='Manager')
    ot_hour = fields.Integer(string='OT')


    @api.model
    def create(self, values):
        values['name'] = values['name'] + "( " + values['code'] + " )"
        res = super(hr_overtime_structure, self).create(values)
        return res

    @api.one
    def apply_ov_structure(self):
        dep_list =[]
        emp_list =[]
        for dep in self.department_ids:
            dep_list.append(dep.id)
        employee_ids = self.env['hr.employee'].search([('department_id','in',dep_list)])
        for emp in employee_ids:
            emp_list.append(emp.id)
        contract_ids = self.env['hr.contract'].search([('employee_id','in',emp_list)])
        for contract in contract_ids:
            contract.write({'overtime_structure_id': self.id})
        self.write({'state':'apply'})


class hr_late_structure(models.Model):
    _name = "hr.late.structure"
    _description = "Late Structure"

    name = fields.Char(string="Structure Name")
    code = fields.Char(string="Code", required=True)
    department_ids = fields.Many2many('hr.department', string="Department (s)")
    hr_late_structure_rule_ids = fields.One2many('hr.late.structure.rule', 'hr_late_structure_id',
                                                 string="Late Structure Line")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('apply', 'Applied')
    ], string="Status", default="draft")
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id
    )

    @api.model
    def create(self, values):
        values['name'] = values['name'] + "( " + values['code'] + " )"
        res = super(hr_late_structure, self).create(values)
        return res

    @api.one
    def apply_late_structure(self):
        dep_list = []
        emp_list = []
        for dep in self.department_ids:
            dep_list.append(dep.id)
        employee_ids = self.env['hr.employee'].search([('department_id', 'in', dep_list)])
        for emp in employee_ids:
            emp_list.append(emp.id)
        contract_ids = self.env['hr.contract'].search([('employee_id', 'in', emp_list)])
        for contract in contract_ids:
            contract.write({'late_structure_id': self.id})
        self.write({'state': 'apply'})

class hr_ov_structure_attendance_rule(models.Model):
    _name = 'hr.ov.structure.attendance.rule'
    _order = 'sequence'

    day_of_week = fields.Selection([('0','Monday'),('1','Tuesday'),('2','Wednesday'),('3','Thursday'),('4','Friday'),('5','Saturday'),('6','Sunday')],string='Day of Week')
    sequence = fields.Integer(string='Sequence', default=10)
    rate = fields.Float(string="Rate", widget="float_time", required=True, default=1)
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    hr_overtime_structure_id = fields.Many2one('hr.overtime.structure', string="Overtime Structure Ref.",
                                               ondelete='cascade')
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id
    )


class hr_ov_structure_rule(models.Model):
    _name = "hr.ov.structure.rule"
    _description = "Overtime Structure Rule"

    sequence = fields.Integer(string='Sequence', default=10)
    type = fields.Selection([
        ('working_day', 'โอทีวันทำงานปกติ'),
        ('weekend', 'โอทีวันหยุด'),
        ('day_off_charge_daily', ' ค่าจ้างทำงานวันหยุด (รายวัน)'),
        ('day_off_charge_monthly', 'ค่าจ้างทำงานวันหยุด (รายเดือน)'),
        ('compensate_holiday','สลับวันหยุดประพณี'),
        ('compensate_weekly_shift', 'สลับวันหยุดประจำสัปดาห์'),
        ('compensate_day', 'สลับวันหยุด'),
        ('accomulate_holiday', 'ทำงานสะสมวันหยุด'),
    ], string="Overtime Type", default="working_day")

    rate = fields.Float(string="Rate", widget="float_time", required=True, default=1)
    begin_after = fields.Float(string="Begin After")
    begin_before = fields.Float(string="Begin Before")
    is_day_time = fields.Boolean(string="Working Time",default=False)
    leave_type = fields.Many2one('hr.holidays.status',string="Leave type")
    hr_overtime_structure_id = fields.Many2one('hr.overtime.structure', string="Overtime Structure Ref.", ondelete='cascade')
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id
    )



class hr_late_structure_rule(models.Model):
    _name = "hr.late.structure.rule"
    _description = "Late Structure Rule"

    type = fields.Selection([
        ('all_day', 'ทุกวัน'),
    ], string="Late Type", default="all_day")

    rate = fields.Float(string="Rate", widget="float_time", required=True, default=1)
    begin_after = fields.Float(string="Begin After")

    hr_late_structure_id = fields.Many2one('hr.late.structure', string="Late Structure Ref.",
                                           ondelete='cascade')
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id
    )

class hr_contract(models.Model):
    _inherit = "hr.contract"

    overtime_structure_id = fields.Many2one('hr.overtime.structure', string="Overtime Structure")
    late_structure_id = fields.Many2one('hr.late.structure', string="Late Structure")
