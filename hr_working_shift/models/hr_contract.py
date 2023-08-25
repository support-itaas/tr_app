#-*-coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
import calendar
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
from math import ceil


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class resource_calendar(models.Model):
    _inherit = "resource.calendar"

    shift = fields.Many2one('employee.shift',string='Shift')


# class resource_shift(models.Model):
#     _name = 'resource.shift'
#
#     name = fields.Char(string='Shift')

class shift_saturday_type(models.Model):
    _name = 'shift.saturday.type'

    name = fields.Char(string='Type')
    is_week_1 = fields.Boolean(string='Week1')
    is_week_2 = fields.Boolean(string='Week2')
    is_week_3 = fields.Boolean(string='Week3')
    is_week_4 = fields.Boolean(string='Week4')
    is_week_5 = fields.Boolean(string='Week5')
    # is_saturday_holiday = fields.Boolean(string='Is saturday On Holidays')
    is_saturday_one = fields.Boolean(string='Is saturday one')
    is_saturday_last = fields.Boolean(string='Is saturday last')

    is_monday = fields.Boolean(string='Monday')
    is_tuesday = fields.Boolean(string='Tuesday')
    is_wednesday = fields.Boolean(string='Wednesday')
    is_thursday = fields.Boolean(string='Thursday')
    is_friday = fields.Boolean(string='Friday')
    is_saturday = fields.Boolean(string='Saturday')
    is_sunday = fields.Boolean(string='Sunday')




class employee_shift(models.Model):
    _name = 'employee.shift'

    name = fields.Char(string='Description')
    # shift_id = fields.Many2one('resource.shift', string='Shift')
    public_holidays_type = fields.Many2one('hr.holidays.public', string='Holiday Type')
    saturday_type = fields.Many2one('shift.saturday.type',string='Saturday Type')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    employee_working_schedule_ids = fields.One2many('employee.working.schedule','employee_shift_id')



    def week_of_month(self,dt):
        """ Returns the week of the month for the specified date.
        """
        first_day = dt.replace(day=1)

        dom = dt.day
        adjusted_dom = dom + first_day.weekday()

        return int(ceil(adjusted_dom / 7.0))

    @api.multi
    @api.onchange('is_saturday_one','is_saturday_last')
    def is_saturday_one_two(self):
        if not self:
            return
        if self.is_saturday_one:
            self.is_saturday_last = False
        if self.is_saturday_last:
            self.is_saturday_last = False

    @api.multi
    def _get_day(self, date):
        # 2018-03-31 07:57:00+07:00
        if date:
            txt = str(date)
            txt_date = txt.split(' ')
            date = txt_date[0]
        # print date
        day_name = str(datetime.strptime(str(date), "%Y-%m-%d").weekday())
        day_value = 0
        if day_name == "0":
            day_name = "Monday"
            day_value = 0
        if day_name == "1":
            day_name = "Tuesday"
            day_value = 1
        if day_name == "2":
            day_name = "Wednesday"
            day_value = 2
        if day_name == "3":
            day_name = "Thursday"
            day_value = 3
        if day_name == "4":
            day_name = "Friday"
            day_value = 4
        if day_name == "5":
            day_name = "Saturday"
            day_value = 5
        if day_name == "6":
            day_name = "Sunday"
            day_value = 6
        return day_name, day_value

    @api.multi
    def generate_schedule(self):
        for schedule in self.employee_working_schedule_ids:
            schedule.unlink()
        start_date = strToDate(self.start_date)
        end_date = strToDate(self.end_date)
        number_of_day = end_date - start_date

        holiday_s = []
        for holiday in self.public_holidays_type.line_ids:
            holiday_s.append(holiday.date)

        saturday_work_week = []

        if self.saturday_type.is_week_1:
            saturday_work_week.append(1)
        if self.saturday_type.is_week_2:
            saturday_work_week.append(2)
        if self.saturday_type.is_week_3:
            saturday_work_week.append(3)
        if self.saturday_type.is_week_4:
            saturday_work_week.append(4)
        if self.saturday_type.is_week_5:
            saturday_work_week.append(5)

        is_1_first = 0
        is_2_first = 0
        is_3_first = 0
        is_4_first = 0
        is_5_first = 0
        is_6_first = 0
        is_7_first = 0
        is_8_first = 0
        is_9_first = 0
        is_10_first = 0
        is_11_first = 0
        is_12_first = 0
        holiday_s1 = []
        for x in range(0, number_of_day.days + 1, 1):
            schedule_date = start_date + relativedelta(days=x)
            date_saturday = self._get_day(str(schedule_date))
            print('=========1')
            print(date_saturday)

            if schedule_date.isoweekday() == 7:
                continue
            if schedule_date.isoweekday() == 6:

                if self.week_of_month(schedule_date) not in saturday_work_week:
                    continue

            if self.saturday_type.is_saturday_one and self.saturday_type.is_saturday_last:
                if date_saturday[1] == 5:
                    holiday_s.append(str(schedule_date))
                if schedule_date.month == 1:
                    if date_saturday[1] == 5:
                        if not is_1_first:
                            holiday_s1.append(str(schedule_date))
                            is_1_first += 1
                elif schedule_date.month == 2:
                    if date_saturday[1] == 5:
                        if not is_2_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_2_first += 1
                elif schedule_date.month == 3:
                    if date_saturday[1] == 5:
                        if not is_3_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_3_first += 1
                elif schedule_date.month == 4:
                    if date_saturday[1] == 5:
                        if not is_4_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_4_first += 1
                elif schedule_date.month == 5:
                    if date_saturday[1] == 5:
                        if not is_5_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_5_first += 1
                elif schedule_date.month == 6:
                    if date_saturday[1] == 5:
                        if not is_6_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_6_first += 1
                elif schedule_date.month == 7:
                    if date_saturday[1] == 5:
                        if not is_7_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_7_first += 1
                elif schedule_date.month == 8:
                    if date_saturday[1] == 5:
                        if not is_8_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_8_first += 1
                elif schedule_date.month == 9:
                    if date_saturday[1] == 5:
                        if not is_9_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_9_first += 1
                elif schedule_date.month == 10:
                    if date_saturday[1] == 5:
                        if not is_10_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_10_first += 1
                elif schedule_date.month == 11:
                    if date_saturday[1] == 5:
                        if not is_11_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_11_first += 1
                elif schedule_date.month == 12:
                    if date_saturday[1] == 5:
                        if not is_12_first:
                            date_1 = schedule_date - relativedelta(days=7)
                            holiday_s1.append(str(date_1))
                            holiday_s1.append(str(schedule_date))
                            is_12_first += 1
                        else:
                            print ('==============1')
                            if str(schedule_date) == '2019-12-31':
                                holiday_s1.append(str(schedule_date))
                            elif str(schedule_date) == '2019-12-30':
                                holiday_s1.append(str(schedule_date))
                            elif str(schedule_date) == '2019-12-29':
                                holiday_s1.append(str(schedule_date))
                            elif str(schedule_date) == '2019-12-28':
                                holiday_s1.append(str(schedule_date))
                            elif str(schedule_date) == '2019-12-27':
                                holiday_s1.append(str(schedule_date))
                            elif str(schedule_date) == '2019-12-26':
                                holiday_s1.append(str(schedule_date))
                            elif str(schedule_date) == '2019-12-25':
                                holiday_s1.append(str(schedule_date))

            if self.saturday_type.is_monday:
                if date_saturday[1] == 0:
                    holiday_s.append(str(schedule_date))
            elif self.saturday_type.is_tuesday:
                if date_saturday[1] == 1:
                    holiday_s.append(str(schedule_date))
            elif self.saturday_type.is_wednesday:
                if date_saturday[1] == 2:
                    holiday_s.append(str(schedule_date))
            elif self.saturday_type.is_thursday:
                if date_saturday[1] == 3:
                    holiday_s.append(str(schedule_date))
            elif self.saturday_type.is_friday:
                if date_saturday[1] == 4:
                    holiday_s.append(str(schedule_date))
            elif self.saturday_type.is_saturday:
                if date_saturday[1] == 5:
                    holiday_s.append(str(schedule_date))
            else:
                if date_saturday[1] == 6:
                    holiday_s.append(str(schedule_date))


        print ('holiday_s============1')
        print (holiday_s1)

        for i in range(0, number_of_day.days+1, 1):
            schedule_date = start_date + relativedelta(days=i)
            date_saturday = self._get_day(str(schedule_date))

            if schedule_date.isoweekday() == 7:
                continue
            if schedule_date.isoweekday() == 6:

                if self.week_of_month(schedule_date) not in saturday_work_week:
                    continue

            if str(schedule_date) in holiday_s1:
                data = {
                    'date': schedule_date,
                    'employee_shift_id': self.id,
                }
                self.env['employee.working.schedule'].create(data)

            if str(schedule_date) not in holiday_s:
                data = {
                    'date': schedule_date,
                    'employee_shift_id': self.id,
                }
                self.env['employee.working.schedule'].create(data)

class employee_working_schedule(models.Model):
    _name = 'employee.working.schedule'

    date = fields.Date(string='Date')
    day = fields.Char(string='Day',compute='get_day',store=True)
    employee_shift_id = fields.Many2one('employee.shift', string='Employee Shift')


    @api.multi
    @api.depends('date')
    def get_day(self):
        self.day = calendar.day_name[date.weekday(strToDate(self.date))]


# class hr_employee(models.Model):
#     _inherit = 'hr.employee'
#
#     #############employee define single or multiple shift, if single select shift then finish, if multiple need to select shift per date range
#     shift_type = fields.Selection([('single','Single'),('multiple','multiple')],default='single',string='Shift Type')
#     shift_id = fields.Many2one('employee.shift',string='Employee Shift')
#     employee_multiple_working_schedule_ids = fields.One2many('employee.multiple.working.schedule', 'employee_id',
#                                                              string='Multiple Employee Schedule')

class employee_multiple_working_schedule(models.Model):
    _name = 'employee.multiple.working.schedule'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    employee_shift_id = fields.Many2one('employee.shift', string='Employee Shift')
    employee_id = fields.Many2one('hr.employee',string='Employee')



