# -*- coding: utf-8 -*-
# Copyright (C) 2021-today ITAAS (Dev K.IT)
from operator import itemgetter

from odoo import api, models, fields, _
from datetime import datetime, timedelta, date, time
from odoo.exceptions import UserError
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class VehiclesInServiceReport(models.TransientModel):
    _name = 'vehicles.in.service.report'

    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    project_id = fields.Many2one('project.project',string='Branch')
    car_status = fields.Selection([('1', "สีปกติ"),('2', "สีเหลือง"),('3', "สีแดง")], string="สถานะรถ")

    @api.model
    def default_get(self, fields):
        res = super(VehiclesInServiceReport, self).default_get(fields)
        curr_date = datetime.now()
        curr_month = curr_date.month
        from_date = datetime(curr_date.year, curr_month, 1).date() or False
        to_date = datetime(curr_date.year, curr_month, curr_date.day).date() or False
        res.update({'date_from': str(from_date),
                    'date_to': str(to_date),
                    })
        return res


    def _prepare_report_data(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_ids': self.company_ids or False,
        }
        data['form'].update(data)
        return data


    def print_report_excel(self):
        [data] = self.read()
        datas = {'form': data}

        str2d = fields.Date.from_string
        date_from = str2d(self.date_from)
        date_to = str2d(self.date_to)
        # backorder_summary = self.get_property_counting(date_from, date_to,)
        date_from_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
        report_file = "รายงานจำนวนรถเข้าใช้บริการ" + str(date_from_obj.strftime("%d/%m/%Y")) + "-" + str(date_to_obj.strftime("%d/%m/%Y"))
        self.env.ref('itaas_vehicles_in_service_report.vis_report_xls').report_file = report_file
        return self.env.ref('itaas_vehicles_in_service_report.vis_report_xls').report_action(self, data=datas, config=False)

    # def get_so_and_do_line(self, date_from, date_to, partner=False):
    #     domain = [
    #         ('order_id.date_order', '>=', date_from),
    #         ('order_id.date_order', '<=', date_to),
    #         ('order_id.state', 'in', ['sale','done'])
    #     ]
    #     if partner:
    #         domain += [('order_id.partner_id', 'in', partner.ids)]
    #
    #     sale = self.env['sale.order.line'].search(domain)
    #     return sale.sorted(key=lambda a: a.order_id.date_order)

    def get_vehicles_in_service(self, date_from, date_to, project_id=False, car_status=False):

        # datetime_from = self.convert_usertz_to_utc(datetime.combine(self.date_from, time.min)).strftime(
        #     DEFAULT_SERVER_DATETIME_FORMAT)
        # datetime_to = self.convert_usertz_to_utc(datetime.combine(self.date_to, time.max)).strftime(
        #     DEFAULT_SERVER_DATETIME_FORMAT)

        domain = [
            ('date_deadline', '>=', date_from),
            ('date_deadline', '<=', date_to),
            ('state', '=', 'done')
        ]
        if project_id:
            domain += [('project_id', 'in', project_id.ids)]

        print('domain ',domain)
        project_task = self.env['project.task'].search(domain)
        return project_task

    def convert_usertz_to_utc(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = user_tz.localize(date_time).astimezone(tz)
        # date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time


class VehiclesInServiceReportXls(models.AbstractModel):
    _name = 'report.itaas_vehicles_in_service_report.vis_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        print('test generate_xlsx_report')
        for_left = workbook.add_format({'align': 'left'})
        for_left_border = workbook.add_format({'align': 'left', 'border': True})
        for_left_bold = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True})
        for_left_bold_border = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True, 'border': True})

        for_right = workbook.add_format({'align': 'right'})
        for_right_border = workbook.add_format({'align': 'right', 'border': True})
        for_right_bold_border = workbook.add_format({'align': 'right', 'border': True, 'bold': True})
        for_right_border_num_format = workbook.add_format({'align': 'right', 'border': True, 'num_format': '#,##0.00'})
        for_right_bold_border_num_format = workbook.add_format(
            {'align': 'right', 'border': True, 'bold': True, 'num_format': '#,##0.00'})

        for_center = workbook.add_format({'align': 'center'})
        for_center_bold = workbook.add_format({'align': 'center', 'bold': True})
        for_center_border = workbook.add_format({'align': 'center', 'border': True})
        for_center_bold_border = workbook.add_format({'valign': 'vcenter','align': 'center', 'bold': True, 'border': True})
        for_center_border_num_format = workbook.add_format({'align': 'center', 'border': True, 'num_format': '#,##0.00'})

        for_center_date = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy'})
        for_center_date1 = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy HH:MM'})

        # def convert_utc_to_usertz(date_time):
        #     if not date_time:
        #         return ''
        #     user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        #     tz = pytz.timezone('UTC')
        #     date_time = tz.localize(fields.Datetime.from_string(date_time)).astimezone(user_tz)
        #     date_time = date_time.strftime('%d/%m/%Y %H:%M')
        #
        #     return date_time

        company_id = self.env.user.company_id
        project_task_ids = lines.get_vehicles_in_service(lines.date_from, lines.date_to, project_id=lines.project_id, car_status=lines.car_status)
        # category_ids = asset_ids.mapped('category_id')
        # print('asset_ids:',asset_ids)
        worksheet = workbook.add_worksheet('รายงานจำนวนรถเข้าใช้บริการ')
        # company_address = company_id.get_company_full_address_text()

        i_row = 0
        i_col = 0
        i_row += 2
        worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'ว.ด.ปี', for_center_bold_border)
        i_col += 1
        worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'ลูกค้าชื่อ', for_center_bold_border)
        i_col += 1
        worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'Redeem สาขา', for_center_bold_border)
        i_col += 1
        worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'ทะเบียนรถ', for_center_bold_border)

        product_coupon_ids = project_task_ids.mapped('coupon_id').mapped('product_id').filtered(lambda x: x.is_coupon and x.type == 'service')
        i_col = 3
        for product in product_coupon_ids:
            i_col += 1
            worksheet.write(i_row + 1, i_col, product.name or ' ', for_center_bold_border)
        i_col += 1
        worksheet.write(i_row + 1, i_col, 'ระดับสี', for_center_bold_border)

        worksheet.merge_range(0, 0, 0, 4 + len(product_coupon_ids), 'รายงานรถเข้าใช้บริการ', for_center_bold_border)
        worksheet.merge_range(1, 0, 1, 4 + len(product_coupon_ids), strToDate(lines.date_from).strftime("%d/%m/%Y") + " - " + strToDate(lines.date_to).strftime("%d/%m/%Y"), for_center_bold_border)

        if len(product_coupon_ids) == 1:
            worksheet.write(i_row, 4, 'งานบริการ', for_center_bold_border)
            i_col = 5
        else:
            worksheet.merge_range(i_row, 4, i_row, i_col, 'งานบริการ', for_center_bold_border)
            i_col += 1

        worksheet.write(i_row, i_col, ' ', for_center_bold_border)

        i_row += 1
        project_ids = project_task_ids.mapped('project_id')
        for project in project_ids:
            project_task_by_project = project_task_ids.filtered(lambda x: x.project_id == project)
            print('project_task_by_project ',project_task_by_project)
            partner_ids = project_task_by_project.mapped('partner_id')
            print('partner_ids ', partner_ids)
            for partner in partner_ids:
                project_task_by_project_partner = project_task_by_project.filtered(lambda x: x.partner_id == partner)
                plate_number_ids = project_task_by_project.mapped('plate_number_id')
                for plate_number in plate_number_ids:
                    project_task_by_project_partner_plate_number = project_task_by_project_partner.filtered(lambda x: x.plate_number_id == plate_number)
                    date_deadline_list = set(project_task_by_project_partner_plate_number.mapped('date_deadline'))
                    print('date_deadline_list ',date_deadline_list)
                    for date_deadline in date_deadline_list:
                        project_task_by_project_partner_plate_number_date_deadline = project_task_by_project_partner_plate_number.filtered(lambda x: x.date_deadline == date_deadline)
                        product_count = []
                        for product in product_coupon_ids:
                            project_task_product_coupon = project_task_by_project_partner_plate_number_date_deadline.filtered(lambda x: x.coupon_id.product_id == product)
                            product_count.append(len(project_task_product_coupon))
                        print('product_count:', product_count)
                        max_count = max(product_count)
                        print('max:', max_count)

                        if lines.car_status:
                            if lines.car_status == '1' and max_count != 1:
                                continue
                            elif lines.car_status == '2' and max_count != 2:
                                continue
                            elif lines.car_status == '3' and max_count < 3:
                                continue

                        i_row += 1
                        i_col = 0
                        worksheet.write(i_row, i_col, date_deadline or ' ', for_center_date)
                        i_col += 1
                        worksheet.write(i_row, i_col, partner.name or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, project.name or ' ', for_left_border)
                        i_col += 1
                        worksheet.write(i_row, i_col, plate_number.name or ' ', for_left_border)

                        for product in product_coupon_ids:
                            project_task_product_coupon = project_task_by_project_partner_plate_number_date_deadline.filtered(lambda x: x.coupon_id.product_id == product)
                            i_col += 1
                            worksheet.write(i_row, i_col, len(project_task_product_coupon), for_left_border)

                        i_col += 1
                        if max_count > 2:
                            worksheet.write(i_row, i_col, 'สีแดง', for_left_border)
                        elif max_count > 1:
                            worksheet.write(i_row, i_col, 'สีเหลือง', for_left_border)
                        else:
                            worksheet.write(i_row, i_col, 'สีปกติ', for_left_border)

        workbook.close()