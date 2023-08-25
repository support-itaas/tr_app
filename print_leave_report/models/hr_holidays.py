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
from odoo.tools import misc, math, pytz
import xlwt
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, '%Y-%m-%d %H:%M:%S')

class HistoryHistoryleavesDept(models.TransientModel):
    _name = 'hr.history.leaves.dept'

    date_from = fields.Date(string='From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    depts = fields.Many2many('hr.department', string='Department(s)')
    emp = fields.Many2many('hr.employee',  string='Employee(s)')
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")
    holiday_type = fields.Selection([
        ('Approved', 'Approved'),
        ('Confirmed', 'Confirmed'),
        ('both', 'Both Approved and Confirmed')
    ], string='Leave Type', required=True, default='Approved')

    @api.multi
    def _get_weekday(self, date):
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

    def get_time_from_float(self,float_time):
        # print "time_from_float=========="
        str_time = str(float_time)
        try:
            str_time.index(".")
            str_hour = str_time.split('.')[0]
            str_minute = int(round((float('0.'+str_time.split('.')[1]) * 60), 0))
            if (str_minute < 10):
                str_minute = "0" + str(str_minute)
            else:
                str_minute = str(str_minute)
        except ValueError:
            str_hour = "0"
            str_minute = "00"

        # print str_hour+":"+str_minute
        # print "=========================="
        if len(str(str_hour))<2:
            str_hour = "0"+str(str_hour)
        return str_hour+":"+str_minute

    def _get_header_info(self, start_date, holiday_type):
        st_date = fields.Date.from_string(start_date)
        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(st_date + relativedelta(days=59)),
            'holiday_type': 'Confirmed and Approved' if holiday_type == 'both' else holiday_type
        }

    def _date_is_day_off(self, date):

        # = calendar.SATURDAY = 5 , calendar.SUNDAY =6
        # return date.weekday() in (calendar.SATURDAY, calendar.SUNDAY,)#
        return date.weekday() in (5, 6,)

    def _get_day_work(self,emp):
        sum_work_day = 0
        # if emp.resource_calendar_id.shift.start_date and emp.resource_calendar_id.shift.end_date:
        #     start_date = emp.resource_calendar_id.shift.start_date
        #     end_date = emp.resource_calendar_id.shift.end_date
        #     start_date = fields.Date.from_string(start_date)
        #     end_date = fields.Date.from_string(end_date)
        #     daysDiff = str((end_date - start_date).days)
        #     for x in range(0, int(daysDiff) + 1):
        #         if not self._date_is_day_off(start_date):
        #             sum_work_day +=1
        #         start_date = start_date + relativedelta(days=1)
        if emp.resource_calendar_id.shift.employee_working_schedule_ids:
            sum_work_day = len(emp.resource_calendar_id.shift.employee_working_schedule_ids)
        return sum_work_day

    def _get_day(self, start_date,end_date):
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        daysDiff = str((end_date - start_date).days)
        # for x in range(0, 60):
        for x in range(0, int(daysDiff) + 1):
            color = '#ababab' if self._date_is_day_off(start_date) else ''
            res.append({'day_str': start_date.strftime('%a'), 'day': start_date.day, 'color': color})
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_months(self, start_date):
        # it works for geting month name between two dates.
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = start_date + relativedelta(days=59)
        while start_date <= end_date:
            last_date = start_date + relativedelta(day=1, months=+1, days=-1)
            if last_date > end_date:
                last_date = end_date
            month_days = (last_date - start_date).days + 1
            res.append({'month_name': start_date.strftime('%B'), 'days': month_days})
            start_date += relativedelta(day=1, months=+1)
        return res

    def _get_leaves_summary(self, start_date, end_date, empid, holiday_type):
        res = []
        count = 0
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        # end_date = start_date + relativedelta(days=59)
        daysDiff = str((end_date - start_date).days)
        # for index in range(0, 60):
        for index in range(0, int(daysDiff) + 1):
            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': '','number_of_days_temp':0.0,})
            if self._date_is_day_off(current):
                res[index]['color'] = '#ababab'
        # count and get leave summary details.
        holiday_type = ['confirm', 'validate'] if holiday_type == 'both' else [
            'confirm'] if holiday_type == 'Confirmed' else ['validate']
        holidays = self.env['hr.holidays'].search([
            ('employee_id', '=', empid), ('state', 'in', holiday_type),
            ('type', '=', 'remove'), ('date_from', '<=', str(end_date)),
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
                    res[(date_from - start_date).days]['color'] = holiday.holiday_status_id.color_name
                    res[(date_from - start_date).days]['number_of_days_temp'] = holiday.number_of_days_temp
                date_from += timedelta(1)
            count += abs(holiday.number_of_days)
        self.sum = count
        return res

    def _get_data_from_report(self, data):
        res = []
        Employee = self.env['hr.employee']
        if 'depts' in data:
            for department in self.env['hr.department'].browse(data['depts']):
                res.append({'dept': department.name, 'data': [], 'color': self._get_day(data['date_from'],data['date_to'])})
                # print(Employee.search([('department_id', '=', department.id)]))
                for emp in Employee.search([('department_id', '=', department.id)]):
                    res[len(res) - 1]['data'].append({
                        'emp': emp.name,
                        'display': self._get_leaves_summary(data['date_from'], data['date_to'], emp.id, data['holiday_type']),
                        'sum': self.sum,
                        'sum_work':self._get_day_work(emp),
                        'sum_absence': self.get_count_absence_em(emp, data['date_from'], data['date_to']),
                        'sum_late': self.get_count_late_em(emp, data['date_from'], data['date_to'])
                    })
        elif 'emp' in data:
            res.append({'data': []})
            for emp in Employee.browse(data['emp']):
                res[0]['data'].append({
                    'emp': emp.name,
                    'display': self._get_leaves_summary(data['date_from'], data['date_to'], emp.id, data['holiday_type']),
                    'sum': self.sum,
                    'sum_work': self._get_day_work(emp),
                    'sum_absence': self.get_count_absence_em(emp, data['date_from'], data['date_to']),
                    'sum_late': self.get_count_late_em(emp, data['date_from'], data['date_to'])
                })
        return res

    def _get_holidays_status(self):
        res = []
        for holiday in self.env['hr.holidays.status'].search([]):
            res.append({'color': holiday.color_name, 'name': holiday.name})
        return res

    def _get_data_from_report_emp(self, data):
        # print('data: '+str(data))
        res = []
        Employee = self.env['hr.employee']
        if 'depts' in data:
            # print('depts')
            # print(data['depts'])
            for department in self.env['hr.department'].browse(data['depts']):
                res.append({'dept' : department.name, 'data': [], 'color': self._get_day(data['date_from'], data['date_to'])})
                # print(Employee.search([('department_id', '=', department.id)]))
                for emp in Employee.search([('department_id', '=', department.id)]):
                    res[len(res)-1]['data'].append({
                        'emp': emp.name,
                        'display': self._get_leaves_summary(data['date_from'], data['date_to'], emp.id, data['holiday_type']),
                        'sum': self.sum,
                        'sum_work': self._get_day_work(emp),
                        'sum_absence': self.get_count_absence_em(emp, data['date_from'], data['date_to']),
                        'sum_late': self.get_count_late_em(emp, data['date_from'], data['date_to'])
                    })
        elif 'emp' in data:
            # print('emp')
            res.append({'data':[]})
            for emp in Employee.browse(data['emp']):
                res[0]['data'].append({
                    'emp': emp.name,
                    'display': self._get_leaves_summary(data['date_from'], emp.id, data['holiday_type']),
                    'sum': self.sum,
                    'sum_work': self._get_day_work(emp),
                    'sum_absence': self.get_count_absence_em(emp, data['date_from'], data['date_to']),
                    'sum_late': self.get_count_late_em(emp, data['date_from'], data['date_to'])
                })
        # print('res: '+str(res))
        return res

    def _get_data_from_report_excel(self, data):
        # print('data: '+str(data))
        res = []
        domain = []
        emp_id = []
        dept_id =[]
        Employee = self.env['hr.employee']
        if 'depts' in data:
            print('depts')
            print(data)
            if 'emp' in data:
                if len(data['emp'])>0:
                    domain.append(('id','in',data['emp']))
                if 'operating_unit_id' in data:
                    if data['operating_unit_id']:
                        domain.append(('operating_unit_id', '=', data['operating_unit_id'][0]))
            # print(data['depts'])
            x = 0
            for department in self.env['hr.department'].browse(data['depts']):
                dept_id.append(department.id)
                res.append({'dept' : department.name, 'data': [], 'color': self._get_day(data['date_from'], data['date_to'])})

                if x > 0:
                    domain.pop()
                    domain.append(('department_id', '=', department.id))
                else:
                    domain.append(('department_id', '=', department.id))
                print(domain)
                emp_ids = Employee.search(domain)
                print(emp_ids)
                x +=1
                for emp in emp_ids:#Employee.search([('department_id', '=', department.id)]):
                    res[len(res)-1]['data'].append({
                        'empid': emp,
                        'emp': emp.name,
                        'employee_code': emp.employee_code,
                        'display': self._get_leaves_summary(data['date_from'], data['date_to'], emp.id, data['holiday_type']),
                        'emp_ids':emp_ids,
                        'sum': self.sum,
                        'sum_work': self._get_day_work(emp),
                        'sum_absence':self.get_count_absence_em(emp, data['date_from'], data['date_to']),
                        'sum_late': self.get_count_late_em(emp, data['date_from'], data['date_to'])
                    })
                    emp_id.append(emp.id)
            # employee not deparment not print 23-09-2019 ....................
            if 'depts' in data:

                if len(data['depts'])== len(res):
                    res.append({'dept':'ไม่ระบุ', 'data': [],
                                'color': self._get_day(data['date_from'], data['date_to'])})

                    domain2 = []
                    if 'operating_unit_id' in data:
                        if data['operating_unit_id']:
                            domain2.append(('operating_unit_id', '=', data['operating_unit_id'][0]))
                    # print(emp_id)
                    # print(dept_id)
                    domain2.append(('id', 'not in', emp_id))
                    domain2.append(('department_id', 'not in', dept_id))
                    # print(domain2)
                    # print(Employee.search(domain2))
                    for emp in Employee.search(domain2):
                        res[len(res)-1]['data'].append({
                            'empid': emp,
                            'emp': emp.name,
                            'employee_code': emp.employee_code,
                            'display': self._get_leaves_summary(data['date_from'], data['date_to'], emp.id,
                                                                data['holiday_type']),
                            'emp_ids': Employee.search([('id', 'not in', emp_id),('department_id','=',False)]),
                            'sum': self.sum,
                            'sum_work': self._get_day_work(emp),
                            'sum_absence':self.get_count_absence_em(emp, data['date_from'], data['date_to']),
                            'sum_late': self.get_count_late_em(emp, data['date_from'], data['date_to'])
                           })
        elif 'emp' in data:
            print('emp')
            res.append({'data':[]})
            # emp_ids = Employee.search([('department_id', '=', department.id)])
            for emp in Employee.browse(data['emp']):
                res[0]['data'].append({
                    'empid': emp,
                    'emp': emp.name,
                    'employee_code': emp.employee_code,
                    'display': self._get_leaves_summary(data['date_from'], emp.id, data['holiday_type']),
                    'sum': self.sum,
                    'sum_work': self._get_day_work(emp),
                    'sum_absence':self.get_count_absence_em(emp, data['date_from'], data['date_to']),
                    'sum_late':self.get_count_late_em(emp, data['date_from'], data['date_to'])
                })
        # print('res: '+str(res))
        return res

    @api.multi
    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        # if not data.get('depts'):
        #     raise UserError(_('You have to select at least one Department. And try again.'))
        # print(data['depts'])
        if len(data['depts'])>0:
            # print('1')
            departments = self.env['hr.department'].browse(data['depts'])#
        else:
            # print('2')
            depts = []
            for x in self.env['hr.department'].search([]):
                depts.append(x.id)
            # print(depts)
            data['depts'] = depts
            # print(data['depts'])
            departments = self.env['hr.department'].browse(data['depts'])
        # print(departments)
        datas = {
            'ids': [],
            'model': 'hr.department',
            'form': data
        }
        # print(datas)

        holidays = self.env['hr.holidays'].browse(self.ids)

        get_data = {
            # 'doc_ids': self.ids,
            # 'doc_model': holidays_report.model,
            'docs': holidays,
            # 'get_header_info': self._get_header_info(data['form']['date_from'], data['form']['holiday_type']),
            # 'get_day': self._get_day(data['form']['date_from']),
            # 'get_months': self._get_months(data['form']['date_from']),
            'get_data_from_report': self._get_data_from_report_excel(datas['form']),
            'get_holidays_status': self._get_holidays_status(),
            'departments':departments,
            'data_in_form':data,
        }
        print('get_data: '+str(get_data))

        return self.print_report_excel(get_data)


    @api.multi
    def print_report_excel(self,get_data):

        result_data = get_data
        print('result_data:'+str(result_data))
        data_in_form = result_data['data_in_form']
        # print(result_data['get_data_from_report'])
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

        worksheet.write_merge(0, 1, 0, 3, self.env.user.company_id.name, for_left)
        worksheet.write_merge(0, 1, 5, 8, "รายงานประวัติการลางาน/ขาดงาน", GREEN_TABLE_HEADER)
        worksheet.write_merge(2, 3, 0, 2, "[ข้อสรุป]", for_left)
        worksheet.write_merge(2, 3, 5, 8, "ตั้งแต่วันที่ "+str(data_in_form['date_from']), for_center_bold)
        worksheet.write_merge(2, 3, 10, 12, "ตั้งแต่วันที่ "+str(data_in_form['date_to']), for_center_bold)
        #
        type_leave = self.env['hr.holidays.status'].search([])
        # worksheet.write(4, 0, 'รหัส', for_center_bold)
        worksheet.write_merge(4, 5, 0, 1, "แผนก", for_center_bold)
        worksheet.write_merge(4, 5, 2, 3, "รหัส", for_center_bold)
        worksheet.write_merge(4, 5, 4, 5, "ชื่อ-นามสกุล", for_center_bold)
        worksheet.write_merge(4, 5, 6, 7, "", for_center_bold)
        col = 8
        col_nex = 9
        for line in type_leave:
            # worksheet.write(7, 4, '', for_left_bold_no_border)
            worksheet.write_merge(4, 5, col, col_nex, str(line.name)+str(' วัน-ชม.:นาที'), for_center_bold)
            col += 2
            col_nex += 2
        worksheet.write_merge(4, 5, col, col_nex,'ขาดงาน ' , for_center_bold)
        worksheet.write_merge(4, 5, col+2, col_nex+2, 'สาย ' + str('วัน-ชม.:นาที'), for_center_bold)
        # print(result_data['data_in_form']['depts'])
        Employee = self.env['hr.employee']
        row = 6
        for x in result_data['get_data_from_report']:
                worksheet.write_merge(row, row, 0, 1, x['dept'], for_center_bold)
                for n in x['data']:
                    worksheet.write_merge(row+1, row+1, 2, 3, n['employee_code'], for_center_bold)
                    worksheet.write_merge(row+1, row+1, 4, 5, n['emp'], for_center_bold)
                    sum = float(n['sum'])
                    sum_str = str(sum).split('.')
                    hout = 0
                    if len(sum_str)> 1:
                        if int(sum_str[1])>0:
                            # print(sum_str[1])
                            hout = '0.'+str(sum_str[1])
                            hout = float(hout) * 8
                    # print('hout:'+str(hout))
                    sum_hout = self.get_time_from_float(hout)
                    # print(sum_hout)
                    worksheet.write_merge(row+1, row+1, 6, 7,'รวม '+str(n['sum'])+' '+str(sum_hout )+'/'+str(n['sum_work'])+' วัน', for_center_bold)
                    col_2 = 8
                    col_nex_2 = 9
                    for l in type_leave:
                        t_data = self._get_leaves_summary(result_data['data_in_form']['date_from'],
                                                          result_data['data_in_form']['date_to'],n['empid'].id,
                                                          result_data['data_in_form']['holiday_type'])
                        c,hout_l,sum_l = self.get_count_leave_type(t_data, result_data['data_in_form']['date_from'],
                                                      result_data['data_in_form']['date_to'],n['empid'],l.color_name)


                        sum_hout_l = self.get_time_from_float(hout_l)
                        worksheet.write_merge(row+1, row+1, col_2, col_nex_2,str(sum_l)+'-'+str(sum_hout_l), for_center_bold)
                        col_2 += 2
                        col_nex_2 += 2
                    row += 1
                    # absence
                    # absence = self.get_count_absence_em(n['empid'],result_data['data_in_form']['date_from'],result_data['data_in_form']['date_to'])
                    worksheet.write_merge(row , row, col_2, col_nex_2, n['sum_absence'],for_center_bold)
                    worksheet.write_merge(row, row, col_2+2, col_nex_2+2, '0 - 00:'+str(n['sum_late']), for_center_bold)
                    # end
                row += 1
                # print(x['data'])

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

    def get_count_absence_em(self,empid, date_from, date_to):
        # print('get_count_absence_em')
        # print(str(date_from)+str(date_to)+str(empid))
        count = 0
        if  empid and  date_from and  date_to:

            # working_schedule_id = empid.resource_calendar_id.shift.employee_working_schedule_ids

            working_schedule_id = self.env['employee.working.schedule'].search([('date','>=',str(date_from)),
                                                            ('date','<=',str(date_to)),
                                                            ('employee_shift_id','=',empid.resource_calendar_id.shift.id)
                                                                                ])

            public_holidays = empid.resource_calendar_id.shift.public_holidays_type
            # print('11111111111')
            # print(public_holidays.line_ids.browse('2019-01-01'))
            # print(public_holidays.line_ids.browse(str(date_from)))
            # print('2222222')
            if working_schedule_id:
                # print('return count')
                for schedule_id in working_schedule_id:
                    # print(schedule_id.date)
                    date_form = str(schedule_id.date)+' 00:00:00'
                    date_end = str(schedule_id.date) + ' 23:59:59'
                    attendance = self.env['hr.attendance'].search([('employee_id','=',empid.id),
                                                                   ('check_in','>=',date_form),
                                                                   ('check_in','<=',date_end)])
                    # print(len(attendance))
                    if not attendance and public_holidays:
                        holidays_public = self.env['hr.holidays.public.line'].search([('date','>=',schedule_id.date),
                                                                                      ('date','<=',schedule_id.date),
                                                                                      ('holidays_id','=',public_holidays.id)
                                                                                      ])
                        if not holidays_public:
                            # print(str(empid.name)+' absend:'+str(schedule_id.date))
                            count = count + 1

                        # print(public_holidays.line_ids.browse('2019-01-01'))
                        # print(public_holidays.line_ids.browse(str(date_from)))
        # print('[--------------------------')
        # print(count)
        # print('--------------------------]')
        return count


    def get_count_late_em(self,empid, date_from, date_to):
        # print('get_count_late_em')
        print(str(date_from)+str(date_to)+str(empid))
        if empid.contract_id:
            if empid.contract_id[0].late_structure_id.hr_late_structure_rule_ids:
                begin_after = empid.contract_id[0].late_structure_id.hr_late_structure_rule_ids[0].begin_after
            else:
                begin_after = 0.08 # 5 minute
        else:
            begin_after = 0.08  # 5 minute

        count = 0
        late_count = 0
        if  empid and  date_from and  date_to:
            # print(schedule_id.date)
            date_form = str(date_from)+' 00:00:00'
            date_end = str(date_to) + ' 23:59:59'
            attendance = self.env['hr.attendance'].search([('employee_id','=',empid.id),
                                                           ('check_in','>=',date_form),
                                                           ('check_in','<=',date_end)])
            # print(str(date_from) + str(date_to) + str(empid))
            # print(attendance)
            moring = False
            afternoon = False
            is_day = False
            for atten_id in attendance:
                weekday = self._get_weekday(atten_id.check_in)#.strftime('%Y-%m-%d').weekday()
                # work_hour = self.late_count(empid, weekday[1], atten_id.check_in, atten_id.check_out)
                # print(weekday)
                tz = pytz.timezone('Asia/Bangkok')
                check_date = pytz.utc.localize(datetime.strptime(atten_id.check_in, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                # print(check_date)
                check_date = str(check_date).split('+')
                # print(check_date)
                check_date = str(check_date[0]).split(' ')
                # print(check_date)
                check_date = check_date[0]
                print(check_date)
                check_date = datetime.strptime(str(check_date), '%Y-%m-%d')

                if not is_day :
                    print('is_day 1')
                    tz = pytz.timezone('Asia/Bangkok')
                    check_in_date = pytz.utc.localize(datetime.strptime(atten_id.check_in, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                    check_in_date = str(check_in_date).split('+')
                    check_in_date = str(check_in_date[0]).split(' ')
                    check_in_date = check_in_date[0]
                    is_day = datetime.strptime(str(check_in_date), '%Y-%m-%d')
                    # print(str(is_day) + ' ' + str(check_date))
                    if not moring and not afternoon:
                        print('moring')
                        moring = True
                        # print(weekday[1])
                        working_hours = self.env['resource.calendar.attendance'].search([('dayofweek','=',weekday[1]),
                                                                                         ('calendar_id','=',empid.resource_calendar_id.id),
                                                                                         ])
                        # print(working_hours)
                        if working_hours:
                            if len(working_hours)>0:
                                working_hour = working_hours[0]
                                tz = pytz.timezone('Asia/Bangkok')
                                sing_in_date = pytz.utc.localize(datetime.strptime(atten_id.check_in, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                                sing_in_date = str(sing_in_date).split('+')
                                sing_in_date = sing_in_date[0]
                                structure_sing_in_date = str(sing_in_date).split(' ')

                                hour_from = self.get_time_from_float(working_hours[0].hour_from)
                                begin_afters = str(self.get_time_from_float(begin_after)).split(':')
                                hour_froms = str(hour_from).split(':')
                                hour_froms = str(hour_froms[0])+':'+str(begin_afters[1])
                                # print(hour_froms)
                                structure_sing_in_date = str(structure_sing_in_date[0]) + ' ' + str(hour_froms) + ':'+str(00)
                                structure_sing_in_date = datetime.strptime(str(structure_sing_in_date), '%Y-%m-%d %H:%M:%S')
                                sing_in_date = datetime.strptime(str(sing_in_date), '%Y-%m-%d %H:%M:%S')
                                # print(str(sing_in_date)+' '+str(structure_sing_in_date))
                                difference = relativedelta(sing_in_date, structure_sing_in_date)
                                days = difference.days
                                hours = difference.hours
                                minutes = difference.minutes
                                seconds = 0
                                # print(difference)
                                # print(str(days)+str(hours)+str(minutes))
                                if int(minutes) > int(begin_afters[1]):
                                    print(str(sing_in_date)+' '+str(structure_sing_in_date))
                                    print(difference)
                                    print(minutes)
                                    late_count += minutes
                                # print({'hour_from': 8.0, 'hour_to': 12.0})

                    elif moring and not afternoon:
                        print('afternoon')
                        afternoon = True
                        working_hours = self.env['resource.calendar.attendance'].search([('dayofweek', '=', weekday[1]),
                                                                                         ('calendar_id', '=',
                                                                                          empid.resource_calendar_id.id),
                                                                                         ])
                        if working_hours:
                            if len(working_hours)>1:
                                working_hour = working_hours[1]
                                tz = pytz.timezone('Asia/Bangkok')
                                sing_in_date = pytz.utc.localize(datetime.strptime(atten_id.check_in, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                                sing_in_date = str(sing_in_date).split('+')
                                sing_in_date = sing_in_date[0]
                                structure_sing_in_date = str(sing_in_date).split(' ')
                                hour_from = self.get_time_from_float(working_hours[1].hour_from)
                                begin_afters = str(self.get_time_from_float(begin_after)).split(':')
                                hour_froms = str(hour_from).split(':')
                                hour_froms = str(hour_froms[0]) + ':' + str(begin_afters[1])
                                # print(begin_afters)
                                structure_sing_in_date = str(structure_sing_in_date[0]) + ' ' + str(hour_froms) + ':'+str(00)
                                structure_sing_in_date = datetime.strptime(str(structure_sing_in_date), '%Y-%m-%d %H:%M:%S')
                                sing_in_date = datetime.strptime(str(sing_in_date), '%Y-%m-%d %H:%M:%S')
                                # print(str(sing_in_date)+' '+str(structure_sing_in_date))
                                difference = relativedelta(sing_in_date, structure_sing_in_date)
                                days = difference.days
                                hours = difference.hours
                                minutes = difference.minutes
                                seconds = 0
                                # print(difference)
                                # print(str(days)+str(hours)+str(minutes))
                                if int(minutes) > int(begin_afters[1]):
                                    late_count += minutes
                                # print({'hour_from': 13.0, 'hour_to': 17.0})

                if is_day == check_date:
                    print('is_day 2')
                    # print(str(is_day)+' '+str(check_date))
                    if not moring and not afternoon:
                        print('moring')
                        moring = True
                        working_hours = self.env['resource.calendar.attendance'].search([('dayofweek', '=', weekday[1]),
                                                                                         ('calendar_id', '=',
                                                                                          empid.resource_calendar_id.id),
                                                                                         ])
                        # print(working_hours)
                        if working_hours:
                            if len(working_hours)>0:
                                working_hour = working_hours[0]
                                tz = pytz.timezone('Asia/Bangkok')
                                sing_in_date = pytz.utc.localize(datetime.strptime(atten_id.check_in, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                                sing_in_date = str(sing_in_date).split('+')
                                sing_in_date = sing_in_date[0]
                                structure_sing_in_date = str(sing_in_date).split(' ')
                                hour_from = self.get_time_from_float(working_hours[0].hour_from)
                                begin_afters = str(self.get_time_from_float(begin_after)).split(':')
                                hour_froms = str(hour_from).split(':')
                                hour_froms = str(hour_froms[0]) + ':' + str(begin_afters[1])
                                structure_sing_in_date = str(structure_sing_in_date[0]) + ' ' + str(hour_froms) + ':'+str(00)
                                structure_sing_in_date = datetime.strptime(str(structure_sing_in_date), '%Y-%m-%d %H:%M:%S')
                                sing_in_date = datetime.strptime(str(sing_in_date), '%Y-%m-%d %H:%M:%S')
                                # print(str(sing_in_date)+' '+str(structure_sing_in_date))
                                difference = relativedelta(sing_in_date, structure_sing_in_date)
                                days = difference.days
                                hours = difference.hours
                                minutes = difference.minutes
                                seconds = 0
                                # print(difference)
                                # print(str(days)+str(hours)+str(minutes))
                                if int(minutes) > int(begin_afters[1]):
                                    late_count += minutes
                                # print({'hour_from': 8.0, 'hour_to': 12.0})
                    elif moring and not afternoon:
                        print('afternoon')
                        afternoon = True
                        working_hours = self.env['resource.calendar.attendance'].search([('dayofweek', '=', weekday[1]),
                                                                                         ('calendar_id', '=',
                                                                                          empid.resource_calendar_id.id),
                                                                                         ])
                        # print(working_hours)
                        if working_hours:
                            if len(working_hours)>1:
                                working_hour = working_hours[1]
                                tz = pytz.timezone('Asia/Bangkok')
                                sing_in_date = pytz.utc.localize(datetime.strptime(atten_id.check_in, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                                sing_in_date = str(sing_in_date).split('+')
                                sing_in_date = sing_in_date[0]
                                structure_sing_in_date = str(sing_in_date).split(' ')
                                hour_from = self.get_time_from_float(working_hours[1].hour_from)
                                begin_afters = str(self.get_time_from_float(begin_after)).split(':')
                                hour_froms = str(hour_from).split(':')
                                hour_froms = str(hour_froms[0]) + ':' + str(begin_afters[1])
                                structure_sing_in_date = str(structure_sing_in_date[0]) + ' ' + str(hour_froms) + ':'+str(00)
                                structure_sing_in_date = datetime.strptime(str(structure_sing_in_date), '%Y-%m-%d %H:%M:%S')
                                sing_in_date = datetime.strptime(str(sing_in_date), '%Y-%m-%d %H:%M:%S')
                                # print(str(sing_in_date)+' '+str(structure_sing_in_date))
                                difference = relativedelta(sing_in_date, structure_sing_in_date)
                                days = difference.days
                                hours = difference.hours
                                minutes = difference.minutes
                                seconds = 0
                                # print(difference)
                                # print(str(days)+str(hours)+str(minutes))
                                if int(minutes) > int(begin_afters[1]):
                                    late_count += minutes
                                # print({'hour_from': 13.0, 'hour_to': 17.0})
                        # print({'hour_from': 13.0, 'hour_to': 17.0})
                        is_day = check_date
                        afternoon = False
                        moring = False
                        is_day = False






        print('[--------------------------')
        print(empid.name)
        print(late_count)
        m = 0
        h = 0
        d = 0

        if int(late_count) > 59:
            t = str(int(late_count)/60).split('.')
            m = t[1][0:2]
            h = t[0]
            # print(m[0:2])
            if int(t[0])>24:
                s = str(t[0]/24).split('.')
                d = s[0]
                h = s[1]
            if len(h)<2:
                h = '0'+str(h)
            if len(m)<2:
                # m =  m[0:2]
                m = '0'+str(m)
                #
            late_count = str(d)+'-'+str(h)+':' +str(int(m))
        else:
            if len(str(late_count))<2:
                late_count = '0'+str(late_count)
            late_count = '0-00:'+str(late_count)

        print(late_count)
        print('--------------------------]')

        return late_count

    # def late_count(self,empid,weekday,check_in,check_out):
    #     # print('late_count')
    #     tz = pytz.timezone('Asia/Bangkok')
    #     check_in = pytz.utc.localize(datetime.strptime(str(check_in), '%Y-%m-%d %H:%M:%S')).astimezone(tz)
    #     check_out = pytz.utc.localize(datetime.strptime(str(check_out), '%Y-%m-%d %H:%M:%S')).astimezone(tz)
    #     working_hours = empid.resource_calendar_id.attendance_ids
    #     check_in = str(check_in).split('+')
    #     check_in = check_in[0]
    #     check_out = str(check_out).split('+')
    #     check_out = check_out[0]
    #     # print(check_out)
    #     # print(datetime.strptime(str(check_out), '%Y-%m-%d %H:%M:%S')+ relativedelta(hours=1))
    #     date_out = datetime.strptime(str(check_out), '%Y-%m-%d %H:%M:%S')+ relativedelta(hours=1)
    #     # print(date_out)
    #     date_start = str(check_in).split(' ')
    #     # date_starts = date_start[0]
    #     date_ends = date_start[0]
    #     # today = date.today()
    #     # first_day = today.replace(day=1)
    #     working_day_hours = [{'hour_from': 8.0, 'hour_to': 12.0,'hour_from': 13.0, 'hour_to': 17.0}]
    #     for line in working_hours:
    #         # print(str(line.dayofweek)+' '+str(weekday))
    #         hour_from = self.get_time_from_float(line.hour_from)
    #         date_starts = str(date_start[0]) + ' ' + str(hour_from) + ':00'
    #         date_starts = datetime.strptime(str(date_starts), '%Y-%m-%d %H:%M:%S')
    #         hour_to = self.get_time_from_float(line.hour_to)
    #         date_ends = str(date_start[0]) + ' ' + str(hour_to) + ':00'
    #         date_ends = datetime.strptime(str(date_ends), '%Y-%m-%d %H:%M:%S')
    #         check_in = datetime.strptime(str(check_in), '%Y-%m-%d %H:%M:%S')
    #         check_out = datetime.strptime(str(check_out), '%Y-%m-%d %H:%M:%S')
    #
    #         if int(line.dayofweek) == int(weekday):# and check_in < date_ends and check_out >= date_ends
    #             # print('11:'+str(check_in)+' '+str(check_out))
    #             val = {'hour_from':line.hour_from,
    #                    'hour_to':line.hour_to}
    #             # print(val)
    #             working_day_hours.append(val)
    #         # elif int(line.dayofweek) == int(weekday):
    #         #     print('22:'+str(check_in) + ' ' + str(check_out))
    #         #     val = {'hour_from': line.hour_from,
    #         #            'hour_to': line.hour_to}
    #         #     print(val)
    #     # print(working_day_hours)
    #     return working_day_hours
    def get_count_leave_type(self,t_data,date_from,date_to,emp,color_name):
        count = 0
        hout_l = 0.0
        sum_l = 0.0
        start = str(date_from)+' 00:00:00'
        end = str(date_to)+' 23:59:59'
        holidays = self.env['hr.holidays'].search([('date_from','>=',start),
                                                   ('date_to','<=',end),
                                                   ('employee_id','=',emp.id),
                                                   ('holiday_status_id.color_name','=',color_name)])
        # print(holidays)
        # print(emp.name)
        # print(t_data)
        if t_data and color_name:
            for l in t_data:
                # print(l)
                if l['color'] != '#ababab' or l != '':
                    # print(str(l)+' '+str(color_name))
                    if l['color'] == color_name:
                        sum_l = float(l['number_of_days_temp'])
                        sum_str_l = str(l['number_of_days_temp']).split('.')
                        hout_l = 0
                        if len(sum_str_l) > 1:
                            if int(sum_str_l[1]) > 0:
                                # print(sum_str_l[1])
                                hout_l = '0.' + str(sum_str_l[1])
                                hout_l = float(hout_l) * 8
                        sum_l += l['number_of_days_temp']
                        count += 1

        # print(count)
        return count,hout_l,sum_l

    def get_time_from_float(self,float_time):
        # print "time_from_float=========="
        str_time = str(float_time)
        try:
            str_time.index(".")
            str_hour = str_time.split('.')[0]
            str_minute = int(round((float('0.'+str_time.split('.')[1]) * 60), 0))
            if (str_minute < 10):
                str_minute = "0" + str(str_minute)
            else:
                str_minute = str(str_minute)
        except ValueError:
            str_hour = "0"
            str_minute = "00"

        # print str_hour+":"+str_minute
        # print "=========================="
        if len(str(str_hour))<2:
            str_hour = "0"+str(str_hour)
        return str_hour+":"+str_minute

    def float_time_convert(float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return (factor * int(math.floor(val)), "{:0>2d}".format(int(round((val % 1) * 60))))

    @api.multi
    def hour_to_minute(self, timedelta):
        if timedelta:
            if ',' in str(timedelta):
                # print
                # 'hour step1 ' + str(timedelta)
                date_time = str(timedelta).split(',')
                days = str(date_time[0]).split(' ')
                times = str(date_time[1]).split(':')
                day = (float(days[0]) * 24) * 60
                hour = float(times[0]) * 60
                minute = float(times[1])
                # print
                # 'days ' + str(days)
                # print
                # 'day ' + str(day)
                # print
                # 'hour ' + str(hour)
                # print
                # 'minute ' + str(minute)
                # minutes = day + hour + minute
                # print
                # 'minutes ' + str(minutes)
                minute_to_hour = minutes / 60
                return minute_to_hour
            else:
                # print
                # 'hour step2 ' + str(timedelta)
                times = str(timedelta).split(':')
                hour = float(times[0]) * 60
                minute = float(times[1])
                # print
                # 'hour ' + str(hour)
                # print
                # 'minute ' + str(minute)
                minutes = hour + minute
                # print
                # 'minutes ' + str(minutes)
                minute_to_hour = minutes / 60
                return minute_to_hour

class HistoryHistoryleavesDeptExcel(models.TransientModel):

    _name = 'hr.history.leaves.dept.excel'

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
            'res_model': 'hr.history.leaves.dept',
            'target': 'new',
        }
