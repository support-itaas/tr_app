# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrHolidaySummaryReportInherit(models.AbstractModel):
    _inherit = 'report.hr_holidays.report_holidayssummary'
    _description = 'Holidays Summary Report'

    # sum_absence = fields.Integer('Sum Absence')

    def _get_header_info_itaas(self, start_date,end_date ,holiday_type):
        st_date = fields.Date.from_string(start_date)
        en_date = fields.Date.from_string(end_date)

        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(en_date),#fields.Date.to_string(st_date + relativedelta(days=59)),
            'holiday_type': 'Confirmed and Approved' if holiday_type == 'both' else holiday_type
        }

    # def _date_is_day_off(self, date):
    #     return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)
    # 
    def _get_day_itaas(self, start_date,end_date):
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        # print(end_date - start_date)
        daysDiff = str((end_date - start_date).days)
        # print('day off '+str(self._date_is_day_off(start_date)))
        for x in range(0, int(daysDiff)+1):
            color = '#ababab' if self._date_is_day_off(start_date) else ''
            res.append({'day_str': start_date.strftime('%a'), 'day': start_date.day , 'color': color})
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_months_itaas(self, start_date,end_date):
        # it works for geting month name between two dates.
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)#start_date + relativedelta(days=59)
        while start_date <= end_date:
            last_date = start_date + relativedelta(day=1, months=+1, days=-1)
            if last_date > end_date:
                last_date = end_date
            month_days = (last_date - start_date).days + 1
            res.append({'month_name': start_date.strftime('%B'), 'days': month_days})
            start_date += relativedelta(day=1, months=+1)
        return res

    def _get_leaves_summary_itaas(self, start_date,end_date ,empid, holiday_type):
        res = []
        count = 0
        start_date_s = fields.Date.from_string(start_date)
        end_date_s = end_date = fields.Date.from_string(end_date)
        start_date = fields.Date.from_string(start_date)
        end_date = end_date = fields.Date.from_string(end_date)#start_date + relativedelta(days=59)
        daysDiff = str((end_date - start_date).days)
        for index in range(0, int(daysDiff)+1):
            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': ''})
            if self._date_is_day_off(current) :
                res[index]['color'] = '#ababab'
        # count and get leave summary details.
        holiday_type = ['confirm','validate'] if holiday_type == 'both' else ['confirm'] if holiday_type == 'Confirmed' else ['validate']
        holidays = self.env['hr.leave'].search([
            ('employee_id', '=', empid), ('state', 'in', holiday_type),
            ('date_from', '<=', str(end_date)),
            ('date_to', '>=', str(start_date))
        ])
        for holiday in holidays:
            # Convert date to user timezone, otherwise the report will not be consistent with the
            # value displayed in the interface.
            date_from = fields.Datetime.from_string(holiday.date_from)
            date_from = fields.Datetime.context_timestamp(holiday, date_from).date()
            date_to = fields.Datetime.from_string(holiday.date_to)
            date_to = fields.Datetime.context_timestamp(holiday, date_to).date()

            for index in range(0, ((date_to - date_from).days + 1)):
                if date_from >= start_date and date_from <= end_date:
                    res[(date_from-start_date).days]['color'] = holiday.holiday_status_id.color_name
                date_from += timedelta(1)
            count += holiday.number_of_days

        self.sum = count
        print('res1: '+str(res))
        print(empid)
        add_res_absence,count = self._get_absence_itaas(start_date_s,end_date_s ,empid,res)
        print('absence:'+str(add_res_absence))
        print(count)
        # self.sum_absence = count
        # return res
        return add_res_absence,count
    # 
    def _get_data_from_report_itaas(self, data):
        res = []
        Employee = self.env['hr.employee']
        print('_get_data_from_report_itaas')
        # print('date:'+str(data))
        # print('depts:' + str(data['depts']))
        if 'depts' in data:
            print('1')
            for department in self.env['hr.department'].browse(data['depts']):
                print('2'+str(department))
                res.append({'dept' : department.name, 'data': [], 'color': self._get_day(data['date_from'])})
                for emp in Employee.search([('department_id', '=', department.id)]):
                    print('3'+str(emp))
                    print(data['holiday_type'])
                    get_leaves_data,count = self._get_leaves_summary_itaas(data['date_from'], data['date_to'], emp.id, data['holiday_type'])
                    res[len(res)-1]['data'].append({
                        'emp': emp.name,
                        'display':get_leaves_data, #self._get_leaves_summary_itaas(data['date_from'],data['date_to'], emp.id, data['holiday_type']),
                        'sum': self.sum,
                        'sum_absence':count,
                    })
        elif 'emp' in data:
            res.append({'data':[]})
            for emp in Employee.browse(data['emp']):
                get_leaves_data,count = self._get_leaves_summary_itaas(data['date_from'], data['date_to'], emp.id, data['holiday_type'])
                res[0]['data'].append({
                    'emp': emp.name,
                    'display': get_leaves_data,#self._get_leaves_summary_itaas(data['date_from'], data['date_to'],emp.id, data['holiday_type']),
                    'sum': self.sum,
                    'sum_absence': count,
                })

        return res

    def _get_absence_itaas(self,start_date,end_date,empid,res):
        print('_get_absence_itaas')
        # print(res)
        # print(start_date)
        # print(end_date)
        # print(empid)
        # res = []
        count = 0
        start_date_s = fields.Date.from_string(start_date)
        end_date_s = end_date = fields.Date.from_string(end_date)  # start_date + relativedelta(days=59)
        daysDiff = str((end_date_s - start_date_s).days)
        if empid:
            # print(empid)
            em_attendance = self.env['hr.attendance']#.search([('employee_id', '=', int(empid)),
            working_day = []                                                  # ])
            em_att = self.env['hr.attendance'].search([('employee_id', '=', empid)],limit=1)
            # print(em_att)
            # print(em_att.employee_id.resource_calendar_id)
            # print(em_att.employee_id.resource_calendar_id.attendance_ids)
            if em_att.employee_id.resource_calendar_id.attendance_ids:
                for day in em_att.employee_id.resource_calendar_id.attendance_ids:
                    if day.dayofweek not in working_day:
                        working_day.append(day.dayofweek)
            # print(working_day)
            # print(em_attendance)
            # em_attendance.browse(data['emp'])
            # domain = [
            #     ('employee_id', '=', empid),
            #     ('check_in', '>=', '2019-07-01 00:00:00'),
            #     ('check_out', '<=', '2019-07-01 23:59:59')
            # ]
            # print(domain)
            # print(em_attendance.search(domain))
            for index in range(0, int(daysDiff)+1):
                current = start_date_s + timedelta(index)
                # res.append({'day': current.day, 'color': ''})
                # print(index)
                sing_date = start_date_s + relativedelta(days=+index)
                # print(sing_date)
                attendance = em_attendance.search([('employee_id', '=',int(empid)),
                                      ('check_in', '>=', str(sing_date)+' 00:00:00'),
                                      ('check_in', '<=', str(sing_date)+' 23:59:59'),
                                      ])
                if not attendance :#and sing_date.weekday() in working_day
                    # print('[')
                    # print(working_day)
                    # print(sing_date.weekday()) # 5 == sat // 6 == sun
                    # print(sing_date)
                    # print(attendance)
                    if str(sing_date.weekday()) in working_day:
                        print('abb')
                        print(index)
                        print(count)
                        # print(res[index-1])
                        if not res[index]['color']:
                            res[index]['color'] = '#ff9933'
                            count = count +1
                            print(count)
                            print('......')
                    # print(']')

            # if self._date_is_day_off(current):
            #     res[index]['color'] = '#ff9933'

        # end _get_absence_itaas
        # print(res)
        # print(count)
        print('end _get_absence_itaas')
        return res,count

    # def _get_holidays_status(self):
    #     res = []
    #     for holiday in self.env['hr.leave.type'].search([]):
    #         res.append({'color': holiday.color_name, 'name': holiday.name})
    #     return res

    @api.model
    def _get_report_values(self, docids, data=None):
        # res =super(HrHolidaySummaryReportInherit, self)._get_report_values(docids, data=None)

        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        holidays_report = self.env['ir.actions.report']._get_report_from_name('hr_holidays.report_holidayssummary')
        holidays = self.env['hr.holidays'].browse(self.ids)
        # print('')
        return {
            'doc_ids': self.ids,
            'doc_model': holidays_report.model,
            'docs': holidays,
            'get_header_info': self._get_header_info_itaas(data['form']['date_from'],data['form']['date_to'], data['form']['holiday_type']),
            'get_day': self._get_day_itaas(data['form']['date_from'],data['form']['date_to']),
            'get_months': self._get_months_itaas(data['form']['date_from'],data['form']['date_to']),
            'get_data_from_report': self._get_data_from_report_itaas(data['form']),
            'get_holidays_status': self._get_holidays_status(),
            # 'get_absence':self._get_absence_itaas(data['form']['date_from'],data['form']['date_to']),
        }
