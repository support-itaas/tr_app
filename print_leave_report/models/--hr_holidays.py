# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from dateutil.relativedelta import relativedelta
import time
from io import BytesIO
from datetime import datetime, date, timedelta
import base64

from addons.calendar.models import calendar
from odoo.exceptions import UserError
from odoo.tools import misc
import xlwt
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, '%Y-%m-%d %H:%M:%S')

class HolidaysSummaryDeptInherit(models.TransientModel):

    _inherit = 'hr.holidays.summary.dept'
    _description = 'HR Leaves Summary Report By Department'

    date_to = fields.Date(string='To', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    # add field to report history report
    employee_id = fields.Many2one('hr.employee', 'Employees Name')
    operating_unit_id = fields.Many2one('operating.unit','Operating Unit')

    # @api.multi
    # @api.onchange('date_to','date_from')
    # def _get_default_date_from_to(self):
    #     print(time.strftime('%Y-%m-01'))
    #     # date_from = time.strftime('%Y-%m-01')
    #     date_from = self.date_from
    #     date_from = datetime.strptime(str(date_from), '%Y-%m-%d')
    #     date_to = date_from + relativedelta(months=+1)
    #     date_to = date_to - relativedelta(days=1)
    #     print(date_to)
    #     self.date_to = date_to.strftime('%Y-%m-%d')
        # date_from = fields.Date.from_string(date_from)
        # date_to = date_from + relativedelta(days=1)
        # previous_date = datetime.datetime.now() - datetime.timedelta(days=30)

    # @api.multi
    # def print_report(self):
    #     self.ensure_one()
    #     [data] = self.read()
    #     if not data.get('depts'):
    #         raise UserError(_('You have to select at least one Department. And try again.'))
    #     departments = self.env['hr.department'].browse(data['depts'])
    #     datas = {
    #         'ids': [],
    #         'model': 'hr.department',
    #         'form': data
    #     }
    #     return self.env.ref('hr_holidays.action_report_holidayssummary').with_context(
    #         from_transient_model=True).report_action(departments, data=datas)

    def _get_header_info_itaas(self, start_date,end_date ,holiday_type):
        st_date = fields.Date.from_string(start_date)
        en_date = fields.Date.from_string(end_date)

        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(en_date),#fields.Date.to_string(st_date + relativedelta(days=59)),
            'holiday_type': 'Confirmed and Approved' if holiday_type == 'both' else holiday_type
        }

    def _date_is_day_off(self, date):
        # print(date)
        # print(date.weekday())
        # print(calendar)
        # = calendar.SATURDAY = 5 , calendar.SUNDAY =6
        # return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)#
        return date.weekday() in (5, 6,)

    def _get_day_itaas(self, start_date,end_date):
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        # print(end_date - start_date)
        daysDiff = str((end_date - start_date).days)
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
        # start_date_s = datetime.strptime(str(start_date), '%Y-%m-%d')
        # end_date_s = datetime.strptime(str(end_date), '%Y-%m-%d')
        start_date = fields.Date.from_string(start_date)
        # print(end_date)
        end_date = fields.Date.from_string(end_date)#start_date + relativedelta(days=59)
        #datetime.strptime(str(date_from), '%Y-%m-%d')
        daysDiff = str((end_date - start_date).days)
        # print('daysDiff '+str(daysDiff))
        for index in range(0, int(daysDiff)+1):
            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': ''})
            if self._date_is_day_off(current) :
                res[index]['color'] = '#ababab'
        # count and get leave summary details.
        holiday_type = ['confirm','validate'] if holiday_type == 'both' else ['confirm'] if holiday_type == 'Confirmed' else ['validate']
        holidays = self.env['hr.holidays'].search([
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
        # print('res1: '+str(res))
        # print(empid)
        add_res_absence,count = self._get_absence_itaas(start_date,end_date,empid,res)
        # print('absence:'+str(add_res_absence))
        # print(count)
        # self.sum_absence = count
        # return res
        return add_res_absence,count
    #
    def _get_data_from_report_leave_itaas(self, data):
        res = []
        Employee = self.env['hr.employee']
        print('date:'+str(data))
        print('depts:' + str(data['depts']))
        if 'depts' in data:
            print('1')
            domain =[]
            employee_id = False
            operating_unit_id = False
            if data['employee_id']:
                employee_id = data['employee_id'][0]
                # domain.append(str('employee_id','=',employee_id))
            if data['operating_unit_id']:
                operating_unit_id = data['operating_unit_id'][0]
                # domain.append(str('operating_unit_id', '=', operating_unit_id))
            for department in self.env['hr.department'].browse(data['depts']):
                print('2'+str(department))
                res.append({'dept' : department.name, 'data': [], 'color': self._get_day_itaas(data['date_from'],data['date_to'])})
                # domain.pop()
                # domain.append(str('department_id', '=', department.id))
                # print('domain: '+str(domain))
                if employee_id and operating_unit_id:
                    if 'department_id' in domain:
                        domain.pop()
                    domain.append(('id', '=', employee_id))
                    domain.append(('operating_unit_id','=',operating_unit_id))
                    domain.append(('department_id', '=', department.id))
                elif employee_id and not operating_unit_id:
                    val = (('department_id', '=', department.id), ('id', '=', employee_id)
                           )
                    domain = val
                elif not employee_id and operating_unit_id:
                    val = (('department_id', '=', department.id),
                           ('operating_unit_id', '=', operating_unit_id))
                    domain = val
                else:
                    val = (('department_id', '=', department.id))
                    domain = val

                print(domain)
                domain.pop()
                print(domain)
                # print(Employee.search([domain]))
                # for emp in Employee.search([('department_id', '=', department.id)]):# 18-09-2019
                for emp in Employee.search(domain):
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
            print('employee_id')
            res.append({'data':[]})
            for emp in Employee.browse(data['emp'].id):
                get_leaves_data,count = self._get_leaves_summary_itaas(data['date_from'], data['date_to'], emp.id, data['holiday_type'])
                res[0]['data'].append({
                    'emp': emp.name,
                    'display': get_leaves_data,#self._get_leaves_summary_itaas(data['date_from'], data['date_to'],emp.id, data['holiday_type']),
                    'sum': self.sum,
                    'sum_absence': count,
                })

        print('return data form'+str(res))
        return res

    def _get_absence_itaas(self,start_date,end_date,empid,res):
        print('_get_absence_itaas')
        # print(res)
        # print(start_date)
        # print(end_date)
        start_date_s = datetime.strptime(str(start_date), '%Y-%m-%d')
        end_date_s = datetime.strptime(str(end_date), '%Y-%m-%d')
        # print(start_date_s)
        # print(end_date_s)
        daysDiff = str((end_date_s - start_date_s).days)
        # print(daysDiff)
        # print(empid)
        # res = []
        count = 0
        # start_date_s = fields.Date.from_string(start_date)
        # end_date_s = fields.Date.from_string(end_date)  # start_date + relativedelta(days=59)
        # daysDiff = str((end_date_s - start_date_s).days)
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
                current = start_date + timedelta(index)
                # res.append({'day': current.day, 'color': ''})
                # print(index)
                sing_date = start_date + relativedelta(days=+index)
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
        print(res)
        print(count)
        print('end _get_absence_itaas')
        return res,count

    def _get_holidays_status_itaas(self):
        res = []
        #hr.holidays.status
        # for holiday in self.env['hr.leave.type'].search([]):
        #     res.append({'color': holiday.color_name, 'name': holiday.name})
        for holiday in self.env['hr.holidays.status'].search([]):
            res.append({'color': holiday.color_name, 'name': holiday.name})
        # print(res)
        return res

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     # res =super(HrHolidaySummaryReportInherit, self)._get_report_values(docids, data=None)
    #     print('data: '+str(data))
    #     if not data.get('form'):
    #         raise UserError(_("Form content is missing, this report cannot be printed."))
    #
    #     holidays_report = self.env['ir.actions.report']._get_report_from_name('hr_holidays.report_holidayssummary')
    #     print(self.ids)
    #     holidays = self.env['hr.holidays'].browse(self.ids)
    #     print(holidays)
    #     print(holidays_report.model)
    #     return {
    #         'doc_ids': self.ids,
    #         'doc_model': holidays_report.model,
    #         'docs': holidays,
    #         'get_header_info': self._get_header_info_itaas(data['form']['date_from'], data['form']['date_to'],
    #                                                        data['form']['holiday_type']),
    #         'get_day': self._get_day_itaas(data['form']['date_from'], data['form']['date_to']),
    #         'get_months': self._get_months_itaas(data['form']['date_from'], data['form']['date_to']),
    #         'get_data_from_report': self._get_data_from_report_leave_itaas(data['form']),
    #         'get_holidays_status': self._get_holidays_status_itaas(),
    #         # 'get_absence':self._get_absence_itaas(data['form']['date_from'],data['form']['date_to']),
    #     }

    @api.multi
    def print_report_excel(self, docids, data=None):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'employee_id', 'holiday_type', 'operating_unit_id', 'depts'])[
            0]
        print(data)
        get_data = self._get_report_values(docids, data)
        print('[')
        print(get_data)
        print(get_data['get_data_from_report'])
        print(']')


        # fl = StringIO()
        fl = BytesIO()
        company_id = self.env.user.company_id
        # ir_values = self.env['ir.values']
        IrDefault = self.env['ir.default']
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Sheet 1')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right.num_format_str = '#,###.00'
        for_right_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_right_bold.num_format_str = '#,###.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left_bold_no_border = xlwt.easyxf(
            "font: bold 1, name  Times New Roman, color black, height 180;  align: horiz left,vertical center;")

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

        worksheet.row(0).height = 200
        worksheet.col(0).width = 2000
        worksheet.col(1).width = 4000
        worksheet.col(2).width = 3500
        worksheet.col(3).width = 6000
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 3000
        worksheet.col(6).width = 2000
        worksheet.col(7).width = 3000
        worksheet.col(8).width = 3000

        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders

        inv_row = 10

        worksheet.write_merge(0, 1, 0, 3, 'self.env.user.company_id', for_left)
        worksheet.write_merge(0, 1, 9, 12, "รายงานประวัติการลางาน/ขาดงาน", GREEN_TABLE_HEADER)
        worksheet.write_merge(2, 3, 0, 2, "[ข้อสรุป]", for_left)
        worksheet.write_merge(2, 3, 9, 12, "ตั้งแต่วันที่", for_center_bold)
        worksheet.write_merge(2, 3, 13, 14, "ตั้งแต่วันที่", for_center_bold)
        #
        type_leave = self.env['hr.holidays.status'].search([])
        # worksheet.write(4, 0, 'รหัส', for_center_bold)
        worksheet.write_merge(4, 5, 0, 1, "รหัส", for_center_bold)
        worksheet.write_merge(4, 5, 2, 3, "ชื่อ-นามสกุล", for_center_bold)
        worksheet.write_merge(4, 5, 4, 5, "", for_center_bold)
        col = 6
        col_nex = 7
        for line in type_leave:
            worksheet.write_merge(4, 5, col, col_nex, line.name, for_center_bold)
            # worksheet.write(4, col, line.name, for_center_bold)
            # worksheet.write(4, 4, 'ลาป่วย ชม./นาที', for_center_bold)
            # worksheet.write(4, 5, 'ลาคลอด ชม./นาที', for_center_bold)
            # worksheet.write(4, 6, 'ลาบวช ชม./นาที', for_center_bold)
            # worksheet.write(4, 7, 'รหัส', for_center_bold)
            # worksheet.write(4, 8, 'รหัส', for_center_bold)
            # worksheet.write(4, 9, 'รหัส', for_center_bold)
            # worksheet.write(4, 10, 'รหัส', for_center_bold)
            # worksheet.write(4, 12, 'รหัส', for_center_bold)
            # worksheet.write(4, 13, 'รหัส', for_center_bold)
            col += 2
            col_nex += 2
        #
        # else:
        #     raise UserError(_('There is invoices between this date range.'))

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE tax_excel_export CASCADE")
        wizard_id = self.env['hr.history.leaves.dept.excel'].create(
            vals={'name': 'History Leaves Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.history.leaves.dept.excel',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

# class HistoryHistoryleavesDeptInherit(models.TransientModel):
#
#     _name = 'hr.history.leaves.dept'
#     _description = 'HR Leaves and absence Summary Report '
#
#     date_from = fields.Date(string='From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
#     date_to = fields.Date(string='From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
#     employee_id = fields.Many2one('hr.employee','Employees Name')
#     operating_unit_id = fields.Many2one('operating.unit','Operating Unit')
#     depts = fields.Many2many('hr.department', 'summary_dept_rel', string='Department(s)')
#     holiday_type = fields.Selection([
#         ('Approved', 'Approved'),
#         ('Confirmed', 'Confirmed'),
#         ('both', 'Both Approved and Confirmed')
#     ], string='Leave Type', required=True, default='Approved')
#
#     def _get_header_info_itaas(self, start_date,end_date ,holiday_type):
#         st_date = fields.Date.from_string(start_date)
#         en_date = fields.Date.from_string(end_date)
#
#         return {
#             'start_date': fields.Date.to_string(st_date),
#             'end_date': fields.Date.to_string(en_date),#fields.Date.to_string(st_date + relativedelta(days=59)),
#             'holiday_type': 'Confirmed and Approved' if holiday_type == 'both' else holiday_type
#         }
#
#     def _date_is_day_off(self, date):
#         # print(date)
#         # print(date.weekday())
#         # print(calendar)
#         # = calendar.SATURDAY = 5 , calendar.SUNDAY =6
#         # return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)#
#         return date.weekday() in (5, 6,)
#
#     def _get_day_itaas(self, start_date,end_date):
#         res = []
#         start_date = fields.Date.from_string(start_date)
#         end_date = fields.Date.from_string(end_date)
#         # print(end_date - start_date)
#         daysDiff = str((end_date - start_date).days)
#         for x in range(0, int(daysDiff)+1):
#             color = '#ababab' if self._date_is_day_off(start_date) else ''
#             res.append({'day_str': start_date.strftime('%a'), 'day': start_date.day , 'color': color})
#             start_date = start_date + relativedelta(days=1)
#         return res
#
#     def _get_months_itaas(self, start_date,end_date):
#         # it works for geting month name between two dates.
#         res = []
#         start_date = fields.Date.from_string(start_date)
#         end_date = fields.Date.from_string(end_date)#start_date + relativedelta(days=59)
#         while start_date <= end_date:
#             last_date = start_date + relativedelta(day=1, months=+1, days=-1)
#             if last_date > end_date:
#                 last_date = end_date
#             month_days = (last_date - start_date).days + 1
#             res.append({'month_name': start_date.strftime('%B'), 'days': month_days})
#             start_date += relativedelta(day=1, months=+1)
#         return res
#
#     def _get_leaves_summary_itaas(self, start_date,end_date ,empid, holiday_type):
#         res = []
#         count = 0
#         start_date_s = fields.Date.from_string(start_date)
#         end_date_s = end_date = fields.Date.from_string(end_date)
#         start_date = fields.Date.from_string(start_date)
#         end_date = end_date = fields.Date.from_string(end_date)#start_date + relativedelta(days=59)
#         daysDiff = str((end_date - start_date).days)
#         for index in range(0, int(daysDiff)+1):
#             current = start_date + timedelta(index)
#             res.append({'day': current.day, 'color': ''})
#             if self._date_is_day_off(current) :
#                 res[index]['color'] = '#ababab'
#         # count and get leave summary details.
#         holiday_type = ['confirm','validate'] if holiday_type == 'both' else ['confirm'] if holiday_type == 'Confirmed' else ['validate']
#         holidays = self.env['hr.leave'].search([
#             ('employee_id', '=', empid), ('state', 'in', holiday_type),
#             ('date_from', '<=', str(end_date)),
#             ('date_to', '>=', str(start_date))
#         ])
#         for holiday in holidays:
#             # Convert date to user timezone, otherwise the report will not be consistent with the
#             # value displayed in the interface.
#             date_from = fields.Datetime.from_string(holiday.date_from)
#             date_from = fields.Datetime.context_timestamp(holiday, date_from).date()
#             date_to = fields.Datetime.from_string(holiday.date_to)
#             date_to = fields.Datetime.context_timestamp(holiday, date_to).date()
#
#             for index in range(0, ((date_to - date_from).days + 1)):
#                 if date_from >= start_date and date_from <= end_date:
#                     res[(date_from-start_date).days]['color'] = holiday.holiday_status_id.color_name
#                 date_from += timedelta(1)
#             count += holiday.number_of_days
#
#         self.sum = count
#         print('res1: '+str(res))
#         print(empid)
#         add_res_absence,count = self._get_absence_itaas(start_date_s,end_date_s ,empid,res)
#         print('absence:'+str(add_res_absence))
#         print(count)
#         # self.sum_absence = count
#         # return res
#         return add_res_absence,count
#     #
#     def _get_data_from_report_itaas(self, data):
#         res = []
#         Employee = self.env['hr.employee']
#         print('date:'+str(data))
#         print('depts:' + str(data['depts']))
#         if 'depts' in data:
#             print('1')
#             for department in self.env['hr.department'].browse(data['depts']):
#                 print('2'+str(department))
#                 res.append({'dept' : department.name, 'data': [], 'color': self._get_day(data['date_from'])})
#                 for emp in Employee.search([('department_id', '=', department.id)]):
#                     print('3'+str(emp))
#                     print(data['holiday_type'])
#                     get_leaves_data,count = self._get_leaves_summary_itaas(data['date_from'], data['date_to'], emp.id, data['holiday_type'])
#                     res[len(res)-1]['data'].append({
#                         'emp': emp.name,
#                         'display':get_leaves_data, #self._get_leaves_summary_itaas(data['date_from'],data['date_to'], emp.id, data['holiday_type']),
#                         'sum': self.sum,
#                         'sum_absence':count,
#                     })
#         elif 'emp' in data:
#             res.append({'data':[]})
#             for emp in Employee.browse(data['emp']):
#                 get_leaves_data,count = self._get_leaves_summary_itaas(data['date_from'], data['date_to'], emp.id, data['holiday_type'])
#                 res[0]['data'].append({
#                     'emp': emp.name,
#                     'display': get_leaves_data,#self._get_leaves_summary_itaas(data['date_from'], data['date_to'],emp.id, data['holiday_type']),
#                     'sum': self.sum,
#                     'sum_absence': count,
#                 })
#
#         print('return data form'+str(res))
#         return res
#
#     def _get_absence_itaas(self,start_date,end_date,empid,res):
#         print('_get_absence_itaas')
#         # print(res)
#         # print(start_date)
#         # print(end_date)
#         # print(empid)
#         # res = []
#         count = 0
#         start_date_s = fields.Date.from_string(start_date)
#         end_date_s = end_date = fields.Date.from_string(end_date)  # start_date + relativedelta(days=59)
#         daysDiff = str((end_date_s - start_date_s).days)
#         if empid:
#             # print(empid)
#             em_attendance = self.env['hr.attendance']#.search([('employee_id', '=', int(empid)),
#             working_day = []                                                  # ])
#             em_att = self.env['hr.attendance'].search([('employee_id', '=', empid)],limit=1)
#             # print(em_att)
#             # print(em_att.employee_id.resource_calendar_id)
#             # print(em_att.employee_id.resource_calendar_id.attendance_ids)
#             if em_att.employee_id.resource_calendar_id.attendance_ids:
#                 for day in em_att.employee_id.resource_calendar_id.attendance_ids:
#                     if day.dayofweek not in working_day:
#                         working_day.append(day.dayofweek)
#             # print(working_day)
#             # print(em_attendance)
#             # em_attendance.browse(data['emp'])
#             # domain = [
#             #     ('employee_id', '=', empid),
#             #     ('check_in', '>=', '2019-07-01 00:00:00'),
#             #     ('check_out', '<=', '2019-07-01 23:59:59')
#             # ]
#             # print(domain)
#             # print(em_attendance.search(domain))
#             for index in range(0, int(daysDiff)+1):
#                 current = start_date_s + timedelta(index)
#                 # res.append({'day': current.day, 'color': ''})
#                 # print(index)
#                 sing_date = start_date_s + relativedelta(days=+index)
#                 # print(sing_date)
#                 attendance = em_attendance.search([('employee_id', '=',int(empid)),
#                                       ('check_in', '>=', str(sing_date)+' 00:00:00'),
#                                       ('check_in', '<=', str(sing_date)+' 23:59:59'),
#                                       ])
#                 if not attendance :#and sing_date.weekday() in working_day
#                     # print('[')
#                     # print(working_day)
#                     # print(sing_date.weekday()) # 5 == sat // 6 == sun
#                     # print(sing_date)
#                     # print(attendance)
#                     if str(sing_date.weekday()) in working_day:
#                         print('abb')
#                         print(index)
#                         print(count)
#                         # print(res[index-1])
#                         if not res[index]['color']:
#                             res[index]['color'] = '#ff9933'
#                             count = count +1
#                             print(count)
#                             print('......')
#                     # print(']')
#
#             # if self._date_is_day_off(current):
#             #     res[index]['color'] = '#ff9933'
#
#         # end _get_absence_itaas
#         print(res)
#         print(count)
#         print('end _get_absence_itaas')
#         return res,count
#
#     def _get_holidays_status_itaas(self):
#         res = []
#         #hr.holidays.status
#         # for holiday in self.env['hr.leave.type'].search([]):
#         #     res.append({'color': holiday.color_name, 'name': holiday.name})
#         for holiday in self.env['hr.holidays.status'].search([]):
#             res.append({'color': holiday.color_name, 'name': holiday.name})
#         # print(res)
#         return res
#
#     @api.model
#     def _get_report_values(self, docids, data=None):
#         # res =super(HrHolidaySummaryReportInherit, self)._get_report_values(docids, data=None)
#         print('data: '+str(data))
#         if not data.get('form'):
#             raise UserError(_("Form content is missing, this report cannot be printed."))
#
#         holidays_report = self.env['ir.actions.report']._get_report_from_name('hr_holidays.report_holidayssummary')
#         print(self.ids)
#         holidays = self.env['hr.holidays'].browse(self.ids)
#         print(holidays)
#         print(holidays_report.model)
#         return {
#             'doc_ids': self.ids,
#             'doc_model': holidays_report.model,
#             'docs': holidays,
#             'get_header_info': self._get_header_info_itaas(data['form']['date_from'], data['form']['date_to'],
#                                                            data['form']['holiday_type']),
#             'get_day': self._get_day_itaas(data['form']['date_from'], data['form']['date_to']),
#             'get_months': self._get_months_itaas(data['form']['date_from'], data['form']['date_to']),
#             'get_data_from_report': self._get_data_from_report_itaas(data['form']),
#             'get_holidays_status': self._get_holidays_status_itaas(),
#             # 'get_absence':self._get_absence_itaas(data['form']['date_from'],data['form']['date_to']),
#         }



class HistoryHistoryleavesDeptExcel(models.TransientModel):

    _name = 'hr.history.leaves.dept.excel'

    report_file = fields.Binary('File')
    name = fields.Char(string='File Name', size=32)
