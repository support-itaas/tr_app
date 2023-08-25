#-*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

import base64
from io import StringIO
from datetime import datetime, date
import locale
import xlwt

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
    department_id = fields.Many2one('hr.department')
    employee_id = fields.Many2one('hr.employee')
    company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env.user.company_id)

    @api.model
    def default_get(self, fields):
        res = super(attendance_report,self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year,curr_date.month,1).date() or False
        to_date = datetime(curr_date.year,curr_date.month,curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
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
        signOnH = signOnP[0] + signOnP[1]/60.0
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
            # working_hours = self.env['resource.calendar'].browse(working_hours_id.id)
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

        print (signOnH)
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
        overtime = False
        overtime_ids = self.env['hr.overtime'].search([('employee_id', '=', employee_id.id),
                                                       ('state', '=', 'approve'),
                                                       ('from_date', '>=', day),
                                                       ('to_date', '<=', day)])
        if overtime_ids:
            overtime = overtime_ids[0]

        return overtime



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
                        print (start_time_of_date)
                        print (finish_time_of_date)
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
                            print (hour_from)
                            print (hour_to)
                        else:
                            continue

                        search_domain = [
                            ('name', '<=', str(finish_time_of_date)),
                            ('name', '>=', str(start_time_of_date)),
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
                                if attendance.action == 'sign_in':
                                    if not first_sign_in_of_day:
                                        first_sign_in_of_day = attendance.name
                                    else:
                                        if attendance.name < first_sign_in_of_day:
                                            first_sign_in_of_day = attendance.name
                                else:
                                    if not last_sign_out_of_day:
                                        last_sign_out_of_day = attendance.name
                                    else:
                                        if attendance.name > last_sign_out_of_day:
                                            last_sign_out_of_day = attendance.name
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

                            print (attendance_datetime_sign_in)
                            print (start_late_date_time)
                            print ('sign_in')
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
                                print (late_time)
                                print ('late_time')
                            print (attendance_datetime_sign_out)
                            print (end_late_date_time)
                            print ('sign_out')
                            end_late_date_time = end_late_date_time - timedelta(minutes = 3)
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
    #
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


        fl = StringIO()
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

        domain_employee = [('is_temp_dept', '=', False),('company_id', '=', self.company_id.id)]

        if self.employee_id:
            domain_employee.append(('id', '=', self.employee_id.id))
        if self.department_id:
            # domain_employee.append(('|'))
            domain_employee.append(('department_id', '=', self.department_id.id))
            # if self.department_id.parent_id:
            # domain_employee.append(('department_id', '=', self.department_id.parent_id.id))
            # domain_employee.append(('employee_id', '=', self.employee_id.id))
            # domain_employee.append(('employee_id', '=', self.employee_id.id))


        # if self.report_type == 'cho-leam':
        #     domain.append(('is_leam', '=', True))
        # if self.agent_id:
        #     domain.append(('agent_id', '=', self.agent_id.id))
        # if self.date_from:
        #     domain.append(('date_time', '>=', self.date_from))
        # if self.date_to:
        #     domain.append(('date_time', '<=', self.date_to))

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
            j = 0
            tomorrow_sign_in_of_day = {}
            sign_in = False

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
                sheet.write(inv_row, 0, i, for_right)
                sheet.write(inv_row, 1, employee_id.employee_code, for_right)
                sheet.write(inv_row, 2, employee_id.name, for_right)
                sheet.write(inv_row, 3, employee_id.job_id.name, for_right)
                sheet.write(inv_row, 4, employee_id.department_id.name, for_right)
                sheet.write(inv_row, 5, '', for_right)
                sheet.write(inv_row, 6, date.strftime("%d/%m/%Y"), for_right)
                sheet.write(inv_row, 7, self._get_day(date), for_right)

                search_domain = [
                    ('name', '<=', str(finish_time_of_date)),
                    ('name', '>=', str(start_time_of_date)),
                    ('employee_id', '=', employee_id.id),
                ]
                attendance_ids = hr_attendance_obj.search(search_domain)
                absent = True
                public_holiday = self.was_on_holiday(date)
                leave_id = self.was_on_leave(employee_id,date)
                ot_id = self.was_on_overtime(employee_id,date)

                if attendance_ids:

                    print (j)
                    tomorrow_sign_in_of_day[j] = False
                    print (date.strftime("%d/%m/%Y"))
                    sign_in = False
                    first_sign_in_of_day = False
                    last_sign_out_of_day = False
                    attendance_datetime_sign_in = False
                    attendance_datetime_sign_out = False
                    for attendance in attendance_ids:
                        time = attendance.name.split(" ")
                        if attendance.action == 'sign_in':
                            if not first_sign_in_of_day:
                                if time[1] < '17:00:00':
                                    first_sign_in_of_day = attendance.name
                                else:
                                    print ('jj')
                                    print (j)
                                    sign_in = True
                                    tomorrow_sign_in_of_day[j] = attendance.name
                            else:
                                if attendance.name < first_sign_in_of_day:
                                    first_sign_in_of_day = attendance.name
                        else:
                            if not last_sign_out_of_day:
                                last_sign_out_of_day = attendance.name
                            else:
                                if attendance.name > last_sign_out_of_day:
                                    last_sign_out_of_day = attendance.name


                    # if j == 1:
                    # print tomorrow_sign_in_of_day[1]
                    if j > 0:
                        if not first_sign_in_of_day and tomorrow_sign_in_of_day and tomorrow_sign_in_of_day[j-1]:
                            print ('99999')
                            first_sign_in_of_day = tomorrow_sign_in_of_day[j-1]
                            # if employee_id.contract_id.late_structure_id:
                            #     if employee_id.contract_id.late_structure_id.hr_late_structure_rule_ids:
                            #         late_time = '00:' +str(int(employee_id.contract_id.late_structure_id.hr_late_structure_rule_ids[0].begin_after)).zfill(2)+':'+'00'
                            #         print late_time
                            #         sign_in_time_split = str(datetime.strptime((pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%H:%M:%S")),'%H:%M:%S')).split(':')
                            #         sign_in_rate_time_split = str(datetime.strptime('07:00:00', '%H:%M:%S')).split(':')
                            #         late_time_split = late_time.split(':')
                            #         sign_in_rate_time_split[1] = str(int(sign_in_rate_time_split[1]) + int(late_time_split[1])).zfill(2)
                            #         sign_in_rate_time = str(sign_in_rate_time_split[0]) + ':' + str(sign_in_rate_time_split[1]) + ':' + str(sign_in_rate_time_split[2])
                            #         print sign_in_rate_time
                                    # tdelta = datetime.strptime((pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%H:%M:%S")),'%H:%M:%S') - datetime.strptime('07:00:00', '%H:%M:%S')
                                    # print tdelta
                                    # if (pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%H:%M:%S") - '07:00:00') > late_time:
                                    #     print (pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%H:%M:%S") - '07:00:00')

                    j = j + 1
                    print ('2')






                    # if first_sign_in_of_day:
                    #     attendance_datetime_sign_in = pytz.utc.localize(
                    #         datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz)
                    #     start_late_time = hour_from + rule.begin_after
                    #     start_late_time = get_time_from_float(start_late_time)
                    #     start_late_date_time = tz.localize(
                    #         datetime.combine(attendance_datetime_sign_in.date(), start_late_time))
                    #
                    # if last_sign_out_of_day:
                    #     attendance_datetime_sign_out = pytz.utc.localize(
                    #         datetime.strptime(last_sign_out_of_day, DATETIME_FORMAT)).astimezone(tz)
                    #     end_late_time = hour_to
                    #     end_late_time = get_time_from_float(end_late_time)
                    #     end_late_date_time = tz.localize(
                    #         datetime.combine(attendance_datetime_sign_out.date(), end_late_time))


                    if first_sign_in_of_day:
                        sheet.write(inv_row, 8, pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                        # print pytz.utc.localize(datetime.strptime(first_sign_in_of_day, DATETIME_FORMAT)).astimezone(tz).time()

                    if last_sign_out_of_day:
                        sheet.write(inv_row, 9, pytz.utc.localize(datetime.strptime(last_sign_out_of_day, DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                        # print pytz.utc.localize(datetime.strptime(last_sign_out_of_day, DATETIME_FORMAT)).astimezone(tz).time()

                    if first_sign_in_of_day and last_sign_out_of_day and  last_sign_out_of_day > first_sign_in_of_day:
                        absent = False

                print ('finish2')

                sheet.write(inv_row, 10, self.get_late(employee_id.contract_id, date), for_right)
                sum_late += self.get_late(employee_id.contract_id, date)
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

                if ot_id:
                    if ot_id.type == 'working_day':
                        sheet.write(inv_row, 15, 'โอทีวันทำงานปกติ', for_right)
                    if ot_id.type == 'weekend':
                        sheet.write(inv_row, 15, 'โอทีวันหยุด', for_right)
                    if ot_id.type == 'day_off_charge_daily':
                        sheet.write(inv_row, 15, 'ค่าจ้างทำงานวันหยุด (รายวัน)', for_right)
                    if ot_id.type == 'day_off_charge_monthly':
                        sheet.write(inv_row, 15, 'ค่าจ้างทำงานวันหยุด (รายเดือน)', for_right)
                    if ot_id.type == 'compensate_holiday':
                        sheet.write(inv_row, 15, 'สลับวันหยุดประพณี', for_right)
                    if ot_id.type == 'compensate_weekly_shift':
                        sheet.write(inv_row, 15, 'สลับวันหยุดประจำสัปดาห์', for_right)
                    if ot_id.type == 'compensate_day':
                        sheet.write(inv_row, 15, 'สลับวันหยุด', for_right)
                    if ot_id.type == 'accomulate_holiday':
                        sheet.write(inv_row, 15, 'ทำงานสะสมวันหยุด', for_right)

                    sheet.write(inv_row, 16, pytz.utc.localize(datetime.strptime(ot_id.from_date,DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                    sheet.write(inv_row, 17, pytz.utc.localize(datetime.strptime(ot_id.to_date,DATETIME_FORMAT)).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S"), for_right)
                    sheet.write(inv_row, 18, '', for_right)
                else:
                    sheet.write(inv_row, 15, '', for_right)
                    sheet.write(inv_row, 16, '', for_right)
                    sheet.write(inv_row, 17, '', for_right)
                    sheet.write(inv_row, 18, '', for_right)


                if self.is_in_working_schedule(start_time_of_date,employee_id.contract_id.resource_calendar_id) and absent and not public_holiday and not leave_id  and int(employee_id.job_category) < 5:
                    sheet.write(inv_row, 19, 'ขาดงาน', for_right)

                if public_holiday:
                    sheet.write(inv_row, 19, public_holiday, for_right)


        workbook.save(fl)
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE attendance_excel_export CASCADE")
        wizard_id = self.pool.get('attendance.excel.export').create(cr, uid, vals={'name': 'attendance Report.xls',
                                                                                   'report_file': ctx[
                                                                                       'report_file']},
                                                                    context=context)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id,
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

