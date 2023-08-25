# -*- coding: utf-8 -*-
# Copyright (C) 2021-today ITAAS (Dev K.IT)
from operator import itemgetter

from odoo import api, models, fields, _
from datetime import datetime, timedelta, date, time
from odoo.exceptions import UserError
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta

class PropertyCountingReport(models.TransientModel):
    _name = 'property.counting.report'

    date_from = fields.Date('Date from')
    date_to = fields.Date('Date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    category_id = fields.Many2one('account.asset.category', string="Category")
    department_id = fields.Many2one('hr.department', string="Department")

    @api.model
    def default_get(self, fields):
        res = super(PropertyCountingReport, self).default_get(fields)
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
        backorder_summary = self.get_property_counting(date_from, date_to,)
        date_from_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
        report_file = "การตรวจนับทรัพย์สิน" + str(date_from_obj.strftime("%d/%m/%Y")) + "-" + str(date_to_obj.strftime("%d/%m/%Y"))
        self.env.ref('itaas_property_counting_report.pc_report_xls').report_file = report_file
        return self.env.ref('itaas_property_counting_report.pc_report_xls').report_action(self, data=datas, config=False)

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

    def get_property_counting(self, date_from, date_to, category_id=False, department_id=False):

        # datetime_from = self.convert_usertz_to_utc(datetime.combine(self.date_from, time.min)).strftime(
        #     DEFAULT_SERVER_DATETIME_FORMAT)
        # datetime_to = self.convert_usertz_to_utc(datetime.combine(self.date_to, time.max)).strftime(
        #     DEFAULT_SERVER_DATETIME_FORMAT)

        domain = [
            # ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]
        if category_id:
            domain += [('category_id', 'in', category_id.ids)]
        if department_id:
            domain += [('department_id', 'in', department_id.ids)]
        print('domain ',domain)
        asset = self.env['account.asset.asset'].search(domain)
        return asset

    def convert_usertz_to_utc(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = user_tz.localize(date_time).astimezone(tz)
        # date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time


class PropertyCountingReportXls(models.AbstractModel):
    _name = 'report.itaas_property_counting_report.pc_report_xls'
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

        asset_ids = lines.get_property_counting(lines.date_from, lines.date_to, category_id=lines.category_id, department_id=lines.department_id)
        category_ids = asset_ids.mapped('category_id')
        print('asset_ids:',asset_ids)
        worksheet = workbook.add_worksheet('การตรวจนับทรัพย์สิน')
        company_address = company_id.get_company_full_address_text()
        i_row = 0
        i_col = 0
        worksheet.merge_range(i_row, i_col, i_row, i_col + 2, company_id.name, for_center_bold_border)

        i_row += 1
        date_to_obj = datetime.strptime(lines.date_to, '%Y-%m-%d')
        worksheet.merge_range(i_row, i_col, i_row, i_col + 2,'ณ วันที่ ' + str(date_to_obj.strftime("%d/%m/%Y")), for_center_bold_border)

        i_row += 2
        i_col = 0
        worksheet.write(i_row, i_col, 'ลำดับ', for_center_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'รหัส', for_center_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'รายการทรัพย์สิน', for_center_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'ราคาซื้อ', for_center_bold_border)
        i_col += 1
        worksheet.merge_range(i_row, i_col, i_row, i_col + 1, 'ตรวจนับทรัพย์สิน', for_center_bold_border)
        i_col += 2
        worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'หมายเหตุ', for_center_bold_border)

        i_row += 1
        i_col = 4
        worksheet.write(i_row, i_col, 'มี', for_center_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'ไม่มี', for_center_bold_border)

        for cate in category_ids:
            asset_by_cate = asset_ids.filtered(lambda m: m.category_id == cate)
            number = 0
            i_row += 1
            i_col = 0
            worksheet.merge_range(i_row, i_col, i_row, i_col + 2, cate.name, for_left_border)
            i_col = 4
            worksheet.write(i_row, i_col, ' ', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_center_bold_border)

            for asset in asset_by_cate:
                i_row += 1
                i_col = 0
                number += 1
                worksheet.write(i_row, i_col, number, for_center_border)
                i_col += 1
                worksheet.write(i_row, i_col, asset.code or ' ', for_center_border)
                i_col += 1
                worksheet.write(i_row, i_col, asset.name or ' ', for_center_border)
                i_col += 1
                worksheet.write(i_row, i_col, asset.asset_purchase_price or ' ', for_center_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_center_bold_border)
                i_col += 1
                worksheet.write(i_row, i_col, ' ', for_center_bold_border)

            i_row += 1
            i_col = 0
            worksheet.merge_range(i_row, i_col, i_row, i_col + 2,'รวม', for_center_bold_border)
            i_col = 4
            worksheet.write(i_row, i_col, ' ', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_center_bold_border)
            i_col += 1
            worksheet.write(i_row, i_col, ' ', for_center_bold_border)

        workbook.close()