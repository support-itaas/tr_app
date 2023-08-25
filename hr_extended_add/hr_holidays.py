#-*-coding: utf-8 -*-
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from odoo import api, tools
from odoo.osv import osv
from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
import pytz
from datetime import datetime,timedelta,date
from odoo import SUPERUSER_ID
from odoo.tools import float_compare, float_is_zero
from decimal import *
import math

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class Hr_Holidays(models.Model):
    _inherit = "hr.holidays"

    @api.onchange('holiday_status_id')
    def onchange_holiday_status_id(self):
        print ('onchange_holiday_status_id')
        working_hours_obj = self.env['resource.calendar']
        # Common Variable
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        TIME_FORMAT = "%H:%M:%S"
        start_time = datetime.strptime('01:00:00', '%H:%M:%S').time()
        finish_time = datetime.strptime('10:00:00', '%H:%M:%S').time()
        tz = pytz.timezone(self._context.get('tz') or 'UTC')

        def get_end_hour_of_the_day(date_in, working_hours_id):
            hour = 0.0
            if type(date_in) is datetime:
                working_hours = working_hours_obj.browse(working_hours_id)
                for line in working_hours.attendance_ids:
                    # First assign to hour
                    if int(line.dayofweek) == date_in.weekday() and hour == 0.0:
                        hour = line.hour_to
                    # Other assignments to hour
                    # No need for this part but it's a fail safe condition
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
            signOnP = [int(n) for n in time_type.split(":")]
            signOnH = signOnP[0] + signOnP[1] / 60.0
            return signOnH

        today = datetime.now().date()
        today_y = int(today.strftime('%Y'))
        today_m = int(today.strftime('%m'))
        today_d = int(today.strftime('%d'))

        if self.date_from:

            leave_date_from = strToDate(self.date_from)
            leave_date_y = int(leave_date_from.strftime('%Y'))
            leave_date_m = int(leave_date_from.strftime('%m'))
            leave_date_d = int(leave_date_from.strftime('%d'))

            if self.employee_id.contract_id.resource_calendar_id:
                hour_to = get_end_hour_of_the_day(datetime.combine(leave_date_from, start_time),
                                                  self.employee_id.contract_id.resource_calendar_id.id)
                hour_from = get_start_hour_of_the_day(datetime.combine(leave_date_from, start_time),
                                                      self.employee_id.contract_id.resource_calendar_id.id)
                if hour_to == 0.0 and hour_from == 0.0:
                    hour_to_time = get_time_from_float(11.0)
                    hour_from_time = get_time_from_float(1.0)
                else:
                    hour_to_time = get_time_from_float(hour_to - 7)
                    hour_from_time = get_time_from_float(hour_from - 7)

                self.date_from = datetime.combine(leave_date_from, hour_from_time)
                self.date_to = datetime.combine(leave_date_from, hour_to_time)


        else:
            # !!!!!ต้องทำ start time และ finish time ให้ตรงกับเวลาทำงานของแต่ละคน
            if self.type == 'remove' and self.employee_id.contract_id.resource_calendar_id:
                # self.date_from = today
                # self.date_to = today
                date_from = datetime.combine(today, start_time)
                hour_to = get_end_hour_of_the_day(date_from, self.employee_id.contract_id.resource_calendar_id.id)
                hour_from = get_start_hour_of_the_day(date_from, self.employee_id.contract_id.resource_calendar_id.id)
                hour_to_time = get_time_from_float(hour_to - 7)
                hour_from_time = get_time_from_float(hour_from - 7)

                self.date_from = datetime.combine(today, hour_from_time)
                self.date_to = datetime.combine(today, hour_to_time)




