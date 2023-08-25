#-*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

import base64
from datetime import datetime, date

import xlwt
import locale

from io import BytesIO
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import misc
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import pytz


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)



#this is for tax report section
class attendance_report(models.TransientModel):
    _name = 'attendance.report'

    date_from = fields.Date(string='Date From',required=True)
    date_to = fields.Date(string='Date To',required=True)
    # department_id = fields.Many2one('hr.department')
    employee_id = fields.Many2one('hr.employee')
    company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env.user.company_id)
    department_ids = fields.Many2many('hr.department')

    @api.model
    def default_get(self, fields):
        res = super(attendance_report,self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year,curr_date.month,1).date() or False
        to_date = datetime(curr_date.year,curr_date.month,curr_date.day).date() or False
        employee_id = False
        department_id = False
        if not self.env.user.has_group('base.group_hr_user') or not self.env.user.has_group('base.group_hr_manager'):
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id

        res.update({'date_from': str(from_date), 'date_to': str(to_date), 'employee_id': employee_id})
        return res

    def _get_day(self, date):
        day_name = str(datetime.strptime(str(date),"%Y-%m-%d").weekday())
        if day_name == "0":
            day_name = "Monday"
        if day_name == "1":
            day_name = "Tuesday"
        if day_name == "2":
            day_name ="Wednesday"
        if day_name == "3":
            day_name = "Thursday"
        if day_name == "4":
            day_name = "Friday"
        if day_name == "5":
            day_name = "Saturday"
        if day_name == "6":
            day_name = "Sunday"
        return day_name

    def _get_index_day(self, date):
        day_name = str(datetime.strptime(str(date),"%Y-%m-%d").weekday())
        return day_name

    def _get_month(self, date):
        if date:
            return datetime.strptime(date,"%Y-%m-%d").month
        return 0

    def _get_year(self, date):
        if date:
            return datetime.strptime(date,"%Y-%m-%d").year
        return 0


    def get_time_from_float(self, float_type):
        str_off_time = str(float_type)
        official_hour = str_off_time.split('.')[0]
        official_minute = ("%2d" % int(str(float("0." + str_off_time.split('.')[1]) * 60).split('.')[0])).replace(' ','0')
        str_off_time = official_hour + ":" + official_minute
        str_off_time = datetime.strptime(str_off_time,"%H:%M").time()
        return str_off_time

    def get_float_from_time(self,time_type):

        signOnP = [int(n) for n in time_type.split(":")]

        # if signOnP < 30 then it will 00, if more then 30 then it will 30
        if signOnP[1] < 30:
            signOnP[1] = 0
        else:
            signOnP[1] = 30

        signOnH = signOnP[0] + signOnP[1] / 60.0
        return signOnH

    def get_number_of_day_of_month(self, date_from,date_to):
        day_from = datetime.strptime(date_from, "%Y-%m-%d")
        day_to = datetime.strptime(date_to, "%Y-%m-%d")
        nb_of_days = (day_to - day_from).days + 1
        return nb_of_days


    def get_working_hr_of_the_day(self,employee_id):
        working_hr = 0
        i = 0
        working_hr_id = employee_id.contract_id.resource_calendar_id.attendance_ids
        for line in working_hr_id:
            i += 1
            working_hr += line.hour_to - line.hour_from

        if i != 0:
            working_hr = working_hr * 2 / i

        return working_hr

    def is_in_working_schedule(self,date_in,working_hours_id):
        found = False
        if type(date_in) is datetime:
            # print working_hours_id
            working_hours = self.env['resource.calendar'].browse(working_hours_id.id)
            # print working_hours
            # print working_hours.name
            for line in working_hours_id.attendance_ids:
                if int(line.dayofweek) == date_in.weekday():
                    found = True
                    break
        return found

    def get_float_from_time_late(self,time_type):

        signOnP = [int(n) for n in time_type.split(":")]
        signOnH = signOnP[0] + signOnP[1] / 60.0

        # print signOnH
        return signOnH

    def was_on_leave(self, employee_id, datetime_day):
        res = False
        day = datetime_day.strftime("%Y-%m-%d")
        holiday_ids = self.env['hr.holidays'].search([('state', '=', 'validate'),('employee_id', '=', employee_id.id),('type', '=', 'remove'),('date_from', '<=', day),
('date_to', '>=', day)])
        if holiday_ids:
            res = holiday_ids[0]
        return res

    #
    # def was_on_absent(employee_id, datetime_day, context=None):
    #     res = False
    #     sign_in = False
    #     sign_out = False
    #     day = datetime_day.strftime("%Y-%m-%d")
    #     absent_ids = self.pool.get('hr.attendance').search(cr, uid, [('employee_id', '=', employee_id),
    #                                                                  ('name', '<=', day),
    #                                                                  ('name', '>=', day)])
    #
    #     for attendance in absent_ids:
    #         if self.pool.get('hr.attendance').browse(cr, uid, attendance, context=context).action == 'sign_in':
    #             sign_in = True
    #         if self.pool.get('hr.attendance').browse(cr, uid, attendance, context=context).action == 'sign_out':
    #             sign_out = True
    #     job_category = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context).job_category
    #     if int(job_category) < 5:
    #         if not sign_in or not sign_out:
    #             res = "absent"
    #     return res
    #

    def was_on_holiday(self,datetime_day):
        res = False
        day = datetime_day.strftime("%Y-%m-%d")
        # holiday_ids = self.env['hr.holidays.public'].get_holidays_lines(day, day, employee_id.address_id.id)

        holiday_ids = self.env['hr.holidays.public.line'].search([('date', '>=', day), ('date', '<=', day)])

        if holiday_ids:
            # print "วันหยุด"
            # print datetime_day
            res = holiday_ids[0].name
        return res

    def was_on_overtime(self,employee_id,datetime_day):
        day = datetime_day.strftime("%Y-%m-%d")
        # overtime = False
        overtime_ids = self.env['hr.overtime'].search([('employee_id', '=', employee_id.id),
                                                                 ('state', '=', 'approve'),
                                                                 ('from_date', '>=', day),
                                                                 ('to_date', '<=', day)])
        # if overtime_ids:
        #     overtime = overtime_ids[0]

        return overtime_ids

    def get_start_hour_of_the_day(self,date_in, working_hours_id):
        hour = 0.0
        if type(date_in) is datetime:
            for line in working_hours_id.attendance_ids:

                # First assign to hour
                if int(line.dayofweek) == date_in.weekday() and hour == 0.0:
                    hour = line.hour_from

                # Other assignments to hour
                # No need for this part but it's a fail safe condition
                elif int(line.dayofweek) == date_in.weekday() and hour != 0.0 and line.hour_to < hour:
                    hour = line.hour_from

        return hour

    def get_end_hour_of_the_day(self,date_in, working_hours_id):
        hour = 0.0

        if type(date_in) is datetime:
            for line in working_hours_id.attendance_ids:
                # First assign to hour
                if int(line.dayofweek) == date_in.weekday() and hour == 0.0:
                    hour = line.hour_to
                # Other assignments to hour
                # No need for this part but it's a fail safe condition
                elif int(line.dayofweek) == date_in.weekday() and hour != 0.0 and line.hour_from > hour:
                    hour = line.hour_to

        return hour

    # late calculation
    def get_late(self,contract,date):
        late_time = 0.0
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        tz = pytz.timezone('Asia/Bangkok')
        if contract.late_structure_id and int(contract.employee_id.job_category) < 5:
            if contract.late_structure_id.hr_late_structure_rule_ids:
                start_time = datetime.strptime('00:00:00', '%H:%M:%S')
                finish_time = datetime.strptime('23:59:59', '%H:%M:%S')
                start_time = start_time.time()
                finish_time = finish_time.time()

                for rule in contract.late_structure_id.hr_late_structure_rule_ids:
                    # future support multiple late type
                    if rule.type == 'all_day':

                        start_time_of_date = tz.localize(datetime.combine(date, start_time))
                        finish_time_of_date = tz.localize(datetime.combine(date, finish_time))
                        if self.is_in_working_schedule(start_time_of_date, contract.resource_calendar_id):

                            if self.was_on_holiday(date):
                                # print "continue public holiday"
                                continue
                            leave_type = self.was_on_leave(contract.employee_id, date)
                            if leave_type and not leave_type.holiday_status_id.attendance_record:
                                # print "continue leave"
                                continue

                            hour_from = self.get_start_hour_of_the_day(start_time_of_date,
                                                                  contract.resource_calendar_id)
                            hour_to = self.get_end_hour_of_the_day(start_time_of_date, contract.resource_calendar_id)
                        else:
                            continue

                        # search_domain = [
                        #     ('name', '<=', str(finish_time_of_date)),
                        #     ('name', '>=', str(start_time_of_date)),
                        #     ('employee_id', '=', contract.employee_id.id),
                        # ]
                        # Edit By Book 18/12/2019 ಠ_ಠ
                        search_domain = [
                            ('check_in', '<=', str(finish_time_of_date)),
                            ('check_out', '>=', str(start_time_of_date)),
                            ('employee_id', '=', contract.employee_id.id),
                        ]

                        attendance_all = self.env['hr.attendance'].search(search_domain)
                        if attendance_all:
                            first_sign_in_of_day = False
                            last_sign_out_of_day = False
                            attendance_datetime_sign_in = False
                            attendance_datetime_sign_out = False
                            start_late_date_time = False
                            end_late_date_time = False

                            for attendance in attendance_all:
                                # attendance = self.pool.get('hr.attendance').browse(cr, uid, attendance,
                                #                                                    context=context)
                                # Edit By Book 18/12/2019 ಠ_ಠ
                                first_sign_in_of_day = attendance.check_in
                                last_sign_out_of_day = attendance.check_out
                                # if attendance.action == 'sign_in':
                                #     if not first_sign_in_of_day:
                                #         first_sign_in_of_day = attendance.name
                                #     else:
                                #         if attendance.name < first_sign_in_of_day:
                                #             first_sign_in_of_day = attendance.name
                                # else:
                                #     if not last_sign_out_of_day:
                                #         last_sign_out_of_day = attendance.name
                                #     else:
                                #         if attendance.name > last_sign_out_of_day:
                                #             last_sign_out_of_day = attendance.name
                            if first_sign_in_of_day:
                                attendance_datetime_sign_in = pytz.utc.localize(
                                    datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz)
                                start_late_time = hour_from + rule.begin_after
                                start_late_time = self.get_time_from_float(start_late_time)
                                start_late_date_time = tz.localize(
                                    datetime.combine(attendance_datetime_sign_in.date(), start_late_time))

                            if last_sign_out_of_day:
                                attendance_datetime_sign_out = pytz.utc.localize(
                                    datetime.strptime(last_sign_out_of_day, DATETIME_FORMAT)).astimezone(tz)
                                end_late_time = hour_to
                                end_late_time = self.get_time_from_float(end_late_time)
                                end_late_date_time = tz.localize(
                                    datetime.combine(attendance_datetime_sign_out.date(), end_late_time))

                            if attendance_datetime_sign_in and (
                                        attendance_datetime_sign_in > start_late_date_time):
                                # print "after att - late start"
                                # print attendance_datetime_sign_in
                                # print start_late_date_time
                                diff_time = attendance_datetime_sign_in - start_late_date_time
                                # print diff_time
                                diff_time = self.get_float_from_time_late(str(diff_time))
                                # print diff_time
                                late_time += diff_time
                            if attendance_datetime_sign_out and (
                                        attendance_datetime_sign_out < end_late_date_time):
                                # print "after att - late start"
                                # print attendance_datetime_sign_out
                                # print start_late_date_time
                                diff_time = end_late_date_time - attendance_datetime_sign_out
                                # print diff_time
                                diff_time = self.get_float_from_time_late(str(diff_time))
                                # print diff_time
                                late_time += diff_time

        return late_time * 60

    def get_ot(self,employee_id,contract,date):
        # OT calculation
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        tz = pytz.timezone('Asia/Bangkok')
        tz_base = pytz.timezone('UTC')
        val_overtime = 0.0
        if contract.overtime_structure_id.overtime_method == 'ov_attendance' and int(
                contract.employee_id.job_category) < 5:
            # Search and Loop attendance records

            search_domain = [
                ('name', '>=', date),
                ('name', '<=', date),
                ('employee_id', '=', contract.employee_id.id),
            ]
            # attendance_ids = self.pool.get('hr.attendance').search(cr, uid, search_domain)
            # for attendance in attendance_ids:
            #     attendance = self.pool.get('hr.attendance').browse(cr, uid, attendance,
            #                                                        context=context)
            #     attendance_datetime = pytz.utc.localize(
            #         datetime.strptime(attendance.name, DATETIME_FORMAT)).astimezone(tz)
            #
            #     # Get end of day from Working Hours
            #     hour_to = get_end_hour_of_the_day(attendance_datetime, contract.working_hours.id)
            #     hour_to_time = get_time_from_float(hour_to)
            #
            #     holiday_status_id = self.pool.get('hr.holidays.status').search(cr, uid,
            #                                                                    [('name', '=', 'Official Leave')]).id
            #
            #     domain = [
            #         ('employee_id', '=', attendance.employee_id.id),
            #         ('holiday_status_id', '=', holiday_status_id)
            #     ]
            #     leave_ids = self.pool.get('hr.holidays').search(cr, uid, domain)
            #     Flage = False
            #     for leave in leave_ids:
            #         leave = self.pool.get('hr.holidays').browse(cr, uid, leave,
            #                                                     context=context)
            #         leave_datetime = datetime.strptime(leave.date_from, DATETIME_FORMAT)
            #         leave_date = leave_datetime.date()
            #         if attendance_datetime.date() == leave_datetime.date():
            #             Flage = True
            #
            #     for rule in contract.overtime_structure_id.hr_ov_structure_rule_ids:
            #         # First condition overtime in Working Day
            #         if is_in_working_schedule(attendance_datetime, contract.working_hours.id):
            #             if Flage == False:
            #                 if rule.type == 'working_day':
            #                     if attendance.action == 'sign_out':
            #                         start_overtime = hour_to + rule.begin_after
            #                         start_overtime_time = get_time_from_float(start_overtime)
            #                         start_overtime = tz.localize(
            #                             datetime.combine(attendance_datetime.date(), start_overtime_time))
            #                         if start_overtime > attendance_datetime:
            #                             continue
            #                         diff_time = attendance_datetime - start_overtime
            #                         diff_time = get_float_from_time(str(diff_time)) * rule.rate
            #                         val_overtime += diff_time
            #             else:
            #                 if rule.type == 'official_leave':
            #                     if attendance.action == 'sign_in':
            #                         sign_in_date = attendance_datetime.date()
            #                         sign_in_attendance_time = attendance_datetime
            #
            #                     elif attendance.action == 'sign_out':
            #                         sign_out_date = attendance_datetime.date()
            #                         sign_out_attendance_time = attendance_datetime
            #
            #                     if sign_in_date == sign_out_date:
            #                         diff_time = sign_out_attendance_time - sign_in_attendance_time
            #                         diff_time = get_float_from_time(str(diff_time)) * rule.rate
            #                         val_overtime += diff_time
            #         else:
            #             if rule.type == 'weekend':
            #                 if attendance.action == 'sign_in':
            #                     sign_in_date = attendance_datetime.date()
            #                     sign_in_attendance_time = attendance_datetime
            #
            #                 elif attendance.action == 'sign_out':
            #                     sign_out_date = attendance_datetime.date()
            #                     sign_out_attendance_time = attendance_datetime
            #
            #                 if sign_in_date == sign_out_date:
            #                     diff_time = sign_out_attendance_time - sign_in_attendance_time
            #                     diff_time = get_float_from_time(str(diff_time)) * rule.rate
            #                     val_overtime += diff_time

        else:
            for rule in contract.overtime_structure_id.hr_ov_structure_rule_ids:
                # print rule.type
                overtime_ids = self.env['hr.overtime'].search([('employee_id', '=', contract.employee_id.id),('state', '=', 'approve'),('from_date', '>=', str(date)),('to_date', '<=', str(date))])
                # print overtime_ids
                if overtime_ids:
                    for overtime in overtime_ids:
                        # print overtime.name
                        if rule.type == overtime.type:
                            if overtime.state == 'approve':
                                # print "match and approve"
                                # print overtime.name
                                # print overtime.from_date
                                # print overtime.to_date
                                # print overtime.total_time

                                start_time = datetime.strptime('00:00:00', '%H:%M:%S')
                                finish_time = datetime.strptime('23:59:59', '%H:%M:%S')
                                start_time = start_time.time()
                                finish_time = finish_time.time()
                                start_time_std = datetime.strptime('08:00:00', '%H:%M:%S')
                                start_time_std = start_time_std.time()
                                std_tz = datetime.strptime('07:00:00', '%H:%M:%S')
                                std_tz = std_tz.time()
                                overtime_from_date_time = datetime.strptime(overtime.from_date, '%Y-%m-%d %H:%M:%S')
                                overtime_to_date_time = datetime.strptime(overtime.to_date, '%Y-%m-%d %H:%M:%S')
                                overtime_from_date = overtime_from_date_time.date()
                                overtime_to_date = overtime_to_date_time.date()

                                # to define overtime date, it is working day or none working day
                                overtime_date = tz.localize(datetime.combine(overtime_from_date, start_time))

                                # find working hour_from and hour_to
                                if self.is_in_working_schedule(overtime_date, contract.resource_calendar_id):
                                    hour_to = self.get_end_hour_of_the_day(overtime_date, contract.resource_calendar_id)
                                    working_hr = self.get_working_hr_of_the_day(employee_id)
                                    hour_from = self.get_start_hour_of_the_day(overtime_date,
                                                                          contract.resource_calendar_id)
                                    hour_to_time = self.get_time_from_float(hour_to)
                                    hour_from_time = self.get_time_from_float(hour_from)

                                else:

                                    hour_to = self.get_end_hour_of_the_day(overtime_date + timedelta(days=2),
                                                                      contract.resource_calendar_id)
                                    working_hr = self.get_working_hr_of_the_day(employee_id)
                                    hour_from = self.get_start_hour_of_the_day(
                                        (overtime_date + timedelta(days=2)), contract.resource_calendar_id)
                                    hour_to_time = self.get_time_from_float(hour_to)
                                    hour_from_time = self.get_time_from_float(hour_from)

                                    # start of the day
                                start_time_of_the_day = tz.localize(
                                    datetime.combine(overtime_from_date, start_time))

                                finish_time_of_the_day = tz.localize(
                                    datetime.combine(overtime_from_date, finish_time))

                                start_time_std = tz.localize(
                                    datetime.combine(overtime_from_date, hour_from_time)).astimezone(tz_base)

                                finish_time_std = tz.localize(
                                    datetime.combine(overtime_from_date, hour_to_time)).astimezone(tz_base)

                                search_domain = [
                                    ('check_in', '<=', str(finish_time_of_the_day)),
                                    ('check_out', '>=', str(start_time_of_the_day)),
                                    ('employee_id', '=', contract.employee_id.id),
                                ]

                                attendance_ids = self.env['hr.attendance'].search(search_domain)
                                # attendance_all = attendance_obj.search([])
                                # print "attendance for ot"
                                # print attendance_ids
                                for attendance in attendance_ids:
                                    if not rule.is_day_time:
                                        # attendance = self.pool.get('hr.attendance').browse(cr, uid, attendance,
                                        #                                                    context=context)
                                        attendance_datetime = pytz.utc.localize(
                                            datetime.strptime(attendance.name, DATETIME_FORMAT)).astimezone(tz)
                                        overtime_to = pytz.utc.localize(
                                            datetime.strptime(overtime.to_date, DATETIME_FORMAT)).astimezone(tz)
                                        overtime_from = pytz.utc.localize(
                                            datetime.strptime(overtime.from_date, DATETIME_FORMAT)).astimezone(tz)

                                        # if attendance.action == 'sign_out':
                                        #     # in case example request from 7:10 - 7:55 and 17:00 - 17:55
                                        #     # in case attendnace is 7:00 , signin 18:00 signout
                                        #     start_overtime = hour_to + rule.begin_after
                                        #     start_overtime_time = self.get_time_from_float(start_overtime)
                                        #     start_overtime = tz.localize(
                                        #         datetime.combine(attendance_datetime.date(), start_overtime_time))
                                        #     # print start_overtime
                                        #     if attendance_datetime > overtime_to:
                                        #         attendance_datetime = overtime_to
                                        #     if start_overtime < overtime_from:
                                        #         start_overtime = overtime_from
                                        #     if attendance_datetime < start_overtime:
                                        #         continue
                                        #
                                        #     diff_time = attendance_datetime - start_overtime
                                        #     diff_time = self.get_float_from_time(str(diff_time)) * rule.rate
                                        #     val_overtime += diff_time
                                        #
                                        #
                                        # else:
                                        #     # in case example request from 7:10 - 7:55 and 17:00 - 17:55
                                        #     # in case attendnace is 7:00 , signin 18:00 signout
                                        #     start_overtime = hour_from - rule.begin_before
                                        #     start_overtime_time = self.get_time_from_float(start_overtime)
                                        #     start_overtime = tz.localize(
                                        #         datetime.combine(attendance_datetime.date(), start_overtime_time))
                                        #     # if attendance date less than overtime request then use overtime request from
                                        #     if attendance_datetime < overtime_from:
                                        #         attendance_datetime = overtime_from
                                        #     # if start oveertime
                                        #     if start_overtime > overtime_to:
                                        #         start_overtime = overtime_to
                                        #     if attendance_datetime > start_overtime:
                                        #         continue
                                        #
                                        #     diff_time = start_overtime - attendance_datetime
                                        #     diff_time = self.get_float_from_time(str(diff_time)) * rule.rate
                                        #     val_overtime += diff_time
                                    else:
                                        # if overtime for weekend, then use total time and deduct noon time if over 4 hr
                                        # print "weekend ot"
                                        diff_time_request = overtime.total_time
                                        if diff_time_request > 4:
                                            diff_time_request -= 1
                                        # print diff_time_request
                                        diff_time = self.get_time_from_float(diff_time_request)
                                        # print "after get time from float"
                                        # print diff_time
                                        diff_time = self.get_float_from_time(str(diff_time)) * rule.rate
                                        # print "after rate apply"
                                        # print diff_time
                                        val_overtime += diff_time
                                        # print "val_overtime"
                                        # print val_overtime
                                        # daily ot type need only one attendance, exit attendnace loop to next overtime
                                        continue
                            # print "val_overtime"
                            # print val_overtime
        # print "the end"
        # print val_overtime
        return val_overtime


    @api.multi
    def print_report(self):
        hr_employee_obj = self.env['hr.employee']
        hr_attendance_obj = self.env['hr.attendance']
        hr_holidays_obj = self.env['hr.holidays']
        hr_overtime_obj = self.env['hr.overtime']
        start_time = datetime.strptime('00:00:00', '%H:%M:%S')
        finish_time = datetime.strptime('23:59:59', '%H:%M:%S')
        start_time = start_time.time()
        finish_time = finish_time.time()
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        tz = pytz.timezone('Asia/Bangkok')


        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        # worksheet = workbook.add_sheet('Sheet 1')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        # bold = workbook.add_format({'bold': True})
        # for_center_bold = workbook.add_format({'bold': True})
        for_right = xlwt.easyxf("font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,###.00'
        for_right_bold = xlwt.easyxf("font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right_bold.num_format_str = '#,###.00'
        for_center = xlwt.easyxf("font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf("font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center_bold = xlwt.easyxf("font: bold 1, name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left_bold_no_border = xlwt.easyxf("font: bold 1, name  Times New Roman, color black, height 180;  align: horiz left,vertical center;")

        GREEN_TABLE_HEADER = xlwt.easyxf(
                 'font: bold 1, name  Times New Roman, height 300,color black;'
                 'align: vertical center, horizontal center, wrap on;'
                    'borders: top thin, bottom thin, left thin, right thin;'
                 'pattern:  pattern_fore_colour white, pattern_back_colour white'
                 )

        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '#,###.00'
        cr, uid, context = self.env.args
        sheet = workbook.add_sheet('Attendance Report')

        domain_employee = [('company_id', '=', self.company_id.id)]

        if self.employee_id:
            domain_employee.append(('id', '=', self.employee_id.id))
        if self.department_ids:
            domain_employee.append(('department_id.id', 'in', self.department_ids.ids))

        employee_ids = hr_employee_obj.search(domain_employee)
        inv_row = 0
        i = 0

        sheet.write(inv_row, 0, 'No', for_center_bold)
        sheet.write(inv_row, 1, 'Emp Code', for_center_bold)
        sheet.write(inv_row, 2, 'Emp Name', for_center_bold)
        sheet.write(inv_row, 3, 'Job Title', for_center_bold)
        sheet.write(inv_row, 4, 'Department', for_center_bold)
        sheet.write(inv_row, 5, 'Section', for_center_bold)
        sheet.write(inv_row, 6, 'Date', for_center_bold)
        sheet.write(inv_row, 7, 'Day', for_center_bold)
        sheet.write(inv_row, 8, 'Sign-in', for_center_bold)
        sheet.write(inv_row, 9, 'Sign-out', for_center_bold)
        sheet.write(inv_row, 10, 'Late', for_center_bold)
        sheet.write(inv_row, 11, 'Leave Type', for_center_bold)
        sheet.write(inv_row, 12, 'Leave Description', for_center_bold)
        sheet.write(inv_row, 13, 'Leave From Time', for_center_bold)
        sheet.write(inv_row, 14, 'Leave To Time', for_center_bold)
        sheet.write(inv_row, 15, 'Overtime Type', for_center_bold)
        sheet.write(inv_row, 16, 'Overtime From Time', for_center_bold)
        sheet.write(inv_row, 17, 'Overtime To Time', for_center_bold)
        sheet.write(inv_row, 18, 'Overtime Approved Time', for_center_bold)
        sheet.write(inv_row, 19, 'Remark', for_center_bold)

        for employee_id in employee_ids:
            sum_late = 0.0
            sum_ot = 0.0
            sum_ot_time = 0.0
            day_from = datetime.strptime(self.date_from, "%Y-%m-%d")
            day_to = datetime.strptime(self.date_to, "%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            for day in range(0, nb_of_days):
                inv_row += 1
                i += 1
                date = (day_from + timedelta(days=day)).date()
                start_time_of_date = datetime.combine(day_from + timedelta(days=day), start_time)
                finish_time_of_date = datetime.combine(day_from + timedelta(days=day), finish_time)

                #start write to excel
                sheet.write(inv_row, 0, locale.format("%.0f", int(i)), for_right)
                sheet.write(inv_row, 1, employee_id.employee_code, for_right)
                sheet.write(inv_row, 2, employee_id.name, for_right)
                sheet.write(inv_row, 3, employee_id.job_id.name, for_right)
                sheet.write(inv_row, 4, employee_id.department_id.name, for_right)
                sheet.write(inv_row, 5, '', for_right)
                sheet.write(inv_row, 6, date.strftime("%d/%m/%Y"), for_right)
                sheet.write(inv_row, 7, self._get_day(date), for_right)

                search_domain = [
                    ('check_in', '<=', str(finish_time_of_date)),
                    ('check_out', '>=', str(start_time_of_date)),
                    ('employee_id', '=', employee_id.id),
                ]
                attendance_ids = hr_attendance_obj.search(search_domain)
                absent = True
                public_holiday = self.was_on_holiday(date)
                leave_id = self.was_on_leave(employee_id,date)
                ot_ids = self.was_on_overtime(employee_id,date)

                if attendance_ids:
                    first_sign_in_of_day = False
                    last_sign_out_of_day = False
                    attendance_datetime_sign_in = False
                    attendance_datetime_sign_out = False
                    for attendance in attendance_ids:
                        first_sign_in_of_day = attendance.check_in
                        last_sign_out_of_day = attendance.check_out
                        # if attendance.action == 'sign_in':
                        #     if not first_sign_in_of_day:
                        #         first_sign_in_of_day = attendance.name
                        #     else:
                        #         if attendance.name < first_sign_in_of_day:
                        #             first_sign_in_of_day = attendance.name
                        # else:
                        #     if not last_sign_out_of_day:
                        #         last_sign_out_of_day = attendance.name
                        #     else:
                        #         if attendance.name > last_sign_out_of_day:
                        #             last_sign_out_of_day = attendance.name

                    if first_sign_in_of_day:
                        sheet.write(inv_row, 8, pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                        # print pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).time()

                    if last_sign_out_of_day:
                        sheet.write(inv_row, 9, pytz.utc.localize(datetime.strptime(last_sign_out_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                        # print pytz.utc.localize(datetime.strptime(last_sign_out_of_day, DATETIME_FORMAT)).astimezone(tz).time()

                    if first_sign_in_of_day and last_sign_out_of_day and  last_sign_out_of_day > first_sign_in_of_day:
                        absent = False



                sheet.write(inv_row, 10, self.get_late(employee_id.contract_id,date), for_right)
                sum_late += self.get_late(employee_id.contract_id,date)
                if leave_id:
                    sheet.write(inv_row, 11, leave_id.holiday_status_id.name, for_right)
                    sheet.write(inv_row, 12, leave_id.name, for_right)
                    sheet.write(inv_row, 13, pytz.utc.localize(datetime.strptime(leave_id.date_from,DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                    sheet.write(inv_row, 14, pytz.utc.localize(datetime.strptime(leave_id.date_to,DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                else:
                    sheet.write(inv_row, 11, '', for_right)
                    sheet.write(inv_row, 12, '', for_right)
                    sheet.write(inv_row, 13, '', for_right)
                    sheet.write(inv_row, 14, '', for_right)

                if ot_ids:
                    ot_type = ""
                    ot_from = ""
                    ot_to = ""
                    ot_time = 0.0
                    for ot_id in ot_ids:
                        if ot_id.type == 'working_day':
                            ot_type += 'โอทีวันทำงานปกติ'
                            ot_type += ','
                            # sheet.write(inv_row, 15, 'โอทีวันทำงานปกติ', for_right)
                        if ot_id.type == 'weekend':
                            ot_type += 'โอทีวันหยุด'
                            ot_type += ','
                            # sheet.write(inv_row, 15, 'โอทีวันหยุด', for_right)

                        if ot_id.type == 'day_off_charge_daily':
                            ot_type += 'ค่าจ้างทำงานวันหยุด (รายวัน)'
                            ot_type += ','
                            # sheet.write(inv_row, 15, 'ค่าจ้างทำงานวันหยุด (รายวัน)', for_right)
                        if ot_id.type == 'day_off_charge_monthly':
                            ot_type += 'ค่าจ้างทำงานวันหยุด (รายเดือน)'
                            ot_type += ','
                            # sheet.write(inv_row, 15, 'ค่าจ้างทำงานวันหยุด (รายเดือน)', for_right)
                        if ot_id.type == 'compensate_holiday':
                            ot_type += 'สลับวันหยุดประพณี'
                            ot_type += ','
                            # sheet.write(inv_row, 15, 'สลับวันหยุดประพณี', for_right)
                        if ot_id.type == 'compensate_weekly_shift':
                            ot_type += 'สลับวันหยุดประจำสัปดาห์'
                            ot_type += ','
                            # sheet.write(inv_row, 15, 'สลับวันหยุดประจำสัปดาห์', for_right)
                        if ot_id.type == 'compensate_day':
                            ot_type += 'สลับวันหยุด'
                            ot_type += ','
                            # sheet.write(inv_row, 15, 'สลับวันหยุด', for_right)
                        if ot_id.type == 'accomulate_holiday':
                            ot_type += 'ทำงานสะสมวันหยุด'
                            ot_type += ','
                            ot_time += ot_id.approve_ot_time
                            # sheet.write(inv_row, 15, 'ทำงานสะสมวันหยุด', for_right)
                        ot_from += str(pytz.utc.localize(datetime.strptime(ot_id.from_date,DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"))
                        ot_from += ','
                        ot_to += str(pytz.utc.localize(datetime.strptime(ot_id.to_date,DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"))
                        ot_to += ','
                    sheet.write(inv_row, 15, ot_type, for_right)
                    sheet.write(inv_row, 16, ot_from, for_right)
                    sheet.write(inv_row, 17, ot_to, for_right)
                    # sheet.write(inv_row, 18, self.get_ot(employee_id, employee_id.contract_id, date), for_right)
                    # if ot from สะสมวันหยุด then use ot approve time, no need to calculate again
                    if not ot_time:
                        sheet.write(inv_row, 18, self.get_ot(employee_id,employee_id.contract_id,date), for_right)
                        sum_ot += self.get_ot(employee_id, employee_id.contract_id, date)
                    else:
                        sheet.write(inv_row, 18, ot_time, for_right)
                        sum_ot_time += ot_time

                else:
                    sheet.write(inv_row, 15, '', for_right)
                    sheet.write(inv_row, 16, '', for_right)
                    sheet.write(inv_row, 17, '', for_right)
                    sheet.write(inv_row, 18, '', for_right)


                if self.is_in_working_schedule(start_time_of_date,employee_id.contract_id.resource_calendar_id) and absent and not public_holiday and not leave_id  and int(employee_id.job_category) < 5:
                    sheet.write(inv_row, 19, 'ขาดงาน', for_right)

                if public_holiday:
                    sheet.write(inv_row, 19, public_holiday, for_right)
            inv_row +=1
            sheet.write(inv_row, 10, sum_late, for_right)
            if sum_ot:
                sheet.write(inv_row, 18, sum_ot, for_right)
            else:
                sheet.write(inv_row, 18, sum_ot_time, for_right)

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE attendance_excel_export CASCADE")
        wizard_id = self.env['attendance.excel.export'].create(
            vals={'name': 'Attendance Report.xls', 'report_file': ctx['report_file']})
        print ('wizard_id')
        print (wizard_id)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class attendance_excel_export(models.TransientModel):
    _name = 'attendance.excel.export'

    report_file = fields.Binary('File')
    name = fields.Char(string='File Name', size=32)

    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.report',
            'target': 'new',
        }

