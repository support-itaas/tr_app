# -*- coding: utf-8 -*-

# for more product stock calculation and report

from bahttext import bahttext
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
import locale
import time
from pytz import timezone, utc
from odoo import api,fields, models
from odoo.osv import osv
# from odoo.report import report_sxw
from odoo.tools import float_compare, float_is_zero

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class hr_attendance(models.Model):
    _inherit = 'hr.attendance'

    # sign_in_local = fields.Datetime(string='Sign-In Local',compute='get_local_timezone',store=True)
    # sign_out_local = fields.Datetime(string='Sign-Out Local',compute='get_local_timezone',store=True)

    sign_in_local = fields.Datetime(string='Sign-In Local')
    sign_out_local = fields.Datetime(string='Sign-Out Local')

    is_break_time = fields.Boolean(string='Break Time')

    # @api.depends('check_in','check_out')
    # def get_local_timezone(self):
    #     if self.check_in:
    #         self.sign_in_local = self.convert_TZ_UTC(self.check_in)
    #
    #     if self.check_out:
    #         self.sign_out_local = self.convert_TZ_UTC(self.check_out)
    #
    #     # print "IN---"
    #     # print self.sign_in_local
    #     # print self.sign_out_local
    #     # print "Out---"
    #
    def convert_TZ_UTC(self, TZ_datetime):
        fmt = "%Y-%m-%d %H:%M:%S"
        # Current time in UTC
        now_utc = datetime.now(timezone('UTC'))
        # Convert to current user time zone
        now_timezone = now_utc.astimezone(timezone(self.env.user.tz))
        # print (now_timezone)
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_utc.strftime(fmt), fmt) - datetime.strptime(
            now_timezone.strftime(fmt), fmt)
        local_datetime = datetime.strptime(TZ_datetime, fmt)
        result_utc_datetime = local_datetime + UTC_OFFSET_TIMEDELTA
        return result_utc_datetime.strftime(fmt)

class hr_attendance_record(models.Model):
    _name = 'hr.attendance.record'
    _rec_name = 'code'

    date_time = fields.Datetime(string='Date-Time')
    date = fields.Date(string='Date',compute='_get_employee_id',store=True)
    code = fields.Char(string='Code')
    employee_id = fields.Many2one('hr.employee',string='Employee_id',compute='_get_employee_id',store=True)
    # machine_number = fields.Char(string='Machine Number')
    # type = fields.Selection([('C/In','C/In'),('C/Out','C/Out')],string='Type')
    type = fields.Char(string='Type')
    active = fields.Boolean(string='Active',default=True)

    @api.multi
    @api.depends('code')
    def _get_employee_id(self):
        for att in self:
            employee_id = self.env['hr.employee'].search([('employee_code','=',att.code)],limit=1)
            if employee_id and att.date_time:
                att.employee_id = employee_id.id
                date_time_plus = fields.Datetime.from_string(att.date_time) + timedelta(hours=7)
                date_time_plus = date_time_plus.strftime('%Y-%m-%d')
                att.date = date_time_plus

    @api.multi
    def generate_attendance(self):
        print("def generate_attendance")
        attendance_ids = self.env['hr.attendance.record'].search([('active','=',True),
                                                                  ('employee_id','!=',False)],
                                                                 order='date_time asc')
        employee_ids = []
        date_ids = []
        att_ids = []
        for attendance in attendance_ids:
            date = attendance.date

            if date not in date_ids:
                date_ids.append(date)
            if attendance.employee_id and attendance.employee_id.id not in employee_ids:
                employee_ids.append(attendance.employee_id.id)
        print('date_ids : ',date_ids)

        for date in date_ids:
            for emp in employee_ids:
                attendance_record_ids = self.env['hr.attendance.record'].search([('active', '=', True),
                                                                                 ('employee_id', '=', emp),
                                                                                 ('date', '=', date)], order='date_time ASC')

                if attendance_record_ids:
                    check_in = attendance_record_ids[0].date_time
                    check_out = attendance_record_ids[len(attendance_record_ids) - 1].date_time
                    vals = {
                        'employee_id': emp,
                        'check_in': check_in,
                        'check_out': check_out,
                    }
                    # print('vals : ',vals)
                    check_attendance = True
                    # we take the latest attendance before our check_in time and check it doesn't overlap with ours
                    last_attendance_before_check_in = self.env['hr.attendance'].search([
                        ('employee_id', '=', emp),
                        ('check_in', '<=', check_in),
                    ], order='check_in desc', limit=1)
                    if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > check_in:
                        print('last_attendance_before_check_in : ',last_attendance_before_check_in)
                        check_attendance = False

                    if not check_out:
                        print('not check_out')
                        # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                        no_check_out_attendances = self.env['hr.attendance'].search([
                            ('employee_id', '=', emp),
                            ('check_out', '=', False),
                        ], order='check_in desc', limit=1)
                        if no_check_out_attendances:
                            check_attendance = False
                    else:
                        print('check_out : ',check_out)
                        # we verify that the latest attendance with check_in time before our check_out time
                        # is the same as the one before our check_in time computed before, otherwise it overlaps
                        last_attendance_before_check_out = self.env['hr.attendance'].search([
                            ('employee_id', '=', emp),
                            ('check_in', '<', check_out),
                        ], order='check_in desc', limit=1)
                        if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                            print('last_attendance_before_check_out : ', last_attendance_before_check_out)
                            check_attendance = False

                    print('check_attendance : ', check_attendance)
                    if check_attendance:
                        self.env['hr.attendance'].create(vals)

                    attendance_record_ids.update({
                        'active': False,
                    })