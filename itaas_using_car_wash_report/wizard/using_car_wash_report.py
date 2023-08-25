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

class UsingCarWashReport(models.TransientModel):
    _name = 'using.car.wash.report'

    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    project_id = fields.Many2one('project.project',string='Branch')

    @api.model
    def default_get(self, fields):
        res = super(UsingCarWashReport, self).default_get(fields)
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
        report_file = "รายงานการใช้น้ำยาล้างรถ" + str(date_from_obj.strftime("%d/%m/%Y")) + "-" + str(date_to_obj.strftime("%d/%m/%Y"))
        self.env.ref('itaas_using_car_wash_report.ucw_report_xls').report_file = report_file
        return self.env.ref('itaas_using_car_wash_report.ucw_report_xls').report_action(self, data=datas, config=False)

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

    def get_using_car_wash(self, date_from, date_to, project_id=False):

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


class UsingCarWashReportXls(models.AbstractModel):
    _name = 'report.itaas_using_car_wash_report.ucw_report_xls'
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

        project_task_ids = lines.get_using_car_wash(lines.date_from, lines.date_to, project_id=lines.project_id)
        # category_ids = asset_ids.mapped('category_id')
        # print('asset_ids:',asset_ids)
        worksheet = workbook.add_worksheet('รายงานการใช้น้ำยาล้างรถ')
        # company_address = company_id.get_company_full_address_text()
        i_row = 0
        i_col = 0
        worksheet.merge_range(i_row, 0, i_row, 11, 'รายงานการใช้น้ำยาล้างรถ', for_center_bold_border)
        i_row += 1
        worksheet.merge_range(i_row, 0, i_row, 11, strToDate(lines.date_from).strftime("%d/%m/%Y") + " - " + strToDate(lines.date_to).strftime("%d/%m/%Y"), for_center_bold_border)

        i_row += 1
        worksheet.write(i_row, i_col, 'สาขา', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'สินค้า', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'ยกมา', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'หน่วย(ยกมา)', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'จำนวนรถ', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'จำนวนน้ำยา', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'หน่วย(น้ำยา)', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'คงเหลือ / แกลลอน', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'Min น้ำยา', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'จำนวนต่ำกว่า  Min', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'Max น้ำยา', for_left_bold_border)
        i_col += 1
        worksheet.write(i_row, i_col, 'Order', for_left_bold_border)

        # print("project_task_ids:", project_task_ids)
        # coupon_ids = project_task_ids.filtered(lambda x: x.coupon_id).mapped('coupon_id')
        # print("coupon_ids:", coupon_ids)
        # product_coupon = coupon_ids.product_id.filtered(lambda x: x.is_coupon)
        # print("product_coupon:", product_coupon)
        # ref_product_counpon = product_coupon.mapped('related_service_id')
        # print("ref_product_counpon:", ref_product_counpon)
        # bom_ref_product_counpon = ref_product_counpon.mapped('bom_ids')
        # print("bom_ref_product_counpon:", bom_ref_product_counpon)
        # bom_line_ref_product_counpon = bom_ref_product_counpon.mapped('bom_line_ids')
        # print("bom_line_ref_product_counpon:",bom_line_ref_product_counpon)

        project_ids = project_task_ids.mapped('project_id')
        for project in project_ids:
            project_task_by_project = project_task_ids.filtered(lambda x: x.project_id == project)
            location_id = project_task_by_project[0].picking_id.location_id
            print('location_id:', location_id)
            coupon_ids = project_task_by_project.mapped('coupon_id')
            print("coupon_ids:", coupon_ids)
            product_coupon = coupon_ids.mapped('product_id').filtered(lambda x: x.is_coupon)
            print("product_coupon:", product_coupon)
            ref_product_counpon = product_coupon.mapped('related_service_id')
            print("ref_product_counpon:", ref_product_counpon)
            bom_ref_product_counpon = ref_product_counpon.mapped('bom_ids')
            print("bom_ref_product_counpon:", bom_ref_product_counpon)
            bom_line_ref_product_counpon = bom_ref_product_counpon.mapped('bom_line_ids')
            product_bom_line = bom_line_ref_product_counpon.mapped('product_id')
            for pb in product_bom_line:
                move_line_in_ids = self.env['stock.move.line'].search([('state', '=', 'done'),
                                                                       ('date', '<', lines.date_from),
                                                                       ('product_id', '<', pb.id),
                                                                       ('location_id', '=', location_id.id),
                                                                       ])
                move_line_out_ids = self.env['stock.move.line'].search([('state', '=', 'done'),
                                                                        ('date', '<', lines.date_from),
                                                                        ('product_id', '<', pb.id),
                                                                        ('location_dest_id', '=', location_id.id),
                                                                        ])
                qty = sum(move_line_in_ids.mapped('qty_done')) - sum(move_line_out_ids.mapped('qty_done'))
                print('qty:', qty)
                min_qy = pb.reordering_min_qty
                max_qty = pb.reordering_max_qty
                print('min_qy:', min_qy)
                print('max_qty:', max_qty)

                bom_line = bom_line_ref_product_counpon.filtered(lambda x: x.product_id == pb)
                uom_bom = bom_line.mapped('product_uom_id')
                for uom in uom_bom:
                    bom_line_by_uom = bom_line.filtered(lambda x: x.product_uom_id == uom)
                    product_qty = sum(bom_line_by_uom.mapped('product_qty'))
                    i_row += 1
                    i_col = 0
                    worksheet.write(i_row, i_col, project.name or ' ', for_left_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, pb.display_name or ' ', for_left_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, qty or ' ', for_right_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, pb.uom_id.name or ' ', for_left_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, len(project_task_by_project) or ' ', for_right_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, product_qty * len(project_task_by_project) or ' ', for_right_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, uom.name or ' ', for_left_border)
                    i_col += 1
                    # จำนวน onhand ไปหน่วย bom
                    qty_to_boml = pb.uom_id._compute_quantity(qty, uom)
                    min_qy_to_boml = pb.uom_id._compute_quantity(min_qy, uom)
                    max_qy_qty_to_boml = pb.uom_id._compute_quantity(max_qty, uom)
                    print('qty_to_boml ', qty_to_boml)
                    qty_remain = qty_to_boml - (product_qty * len(project_task_by_project))
                    # # จำนวน onhand ไปหน่วย onhand
                    qty_remain = uom._compute_quantity(qty_remain, pb.uom_id)
                    worksheet.write(i_row, i_col, qty_remain or ' ', for_right_border)

                    i_col += 1
                    worksheet.write(i_row, i_col, min_qy or ' ', for_right_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, qty_remain - min_qy or ' ', for_right_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, max_qty or ' ', for_right_border)
                    i_col += 1
                    worksheet.write(i_row, i_col, max_qty - (qty_remain - min_qy) or ' ', for_right_border)


            # if bom_line_ref_product_counpon:
            #     for line in bom_line_ref_product_counpon:
            #         i_row += 1
            #         i_col = 0
            #         worksheet.write(i_row, i_col, project.name or ' ', for_left_border)
            #         i_col += 1
            #         worksheet.write(i_row, i_col, line.product_id.display_name or ' ', for_left_border)
            #         i_col += 1
            #         qty = line.product_id.with_context(to_date=lines.date_to).qty_at_date
            #         print('qty:', qty)
            #         worksheet.write(i_row, i_col, qty or ' ', for_right_border)
            #         i_col += 1
            #         worksheet.write(i_row, i_col, line.product_id.uom_id.name or ' ', for_left_border)
            #         i_col += 1
            #         worksheet.write(i_row, i_col, len(project_task_by_project) or ' ', for_right_border)
            #         i_col += 1
            #         worksheet.write(i_row, i_col, line.product_qty * len(project_task_by_project) or ' ', for_right_border)
            #         i_col += 1
            #         worksheet.write(i_row, i_col, line.product_uom_id.name or ' ', for_left_border)
            #
            #         i_col += 1
            #         # จำนวน onhand ไปหน่วย bom
            #         qty_to_boml = line.product_id.uom_id._compute_quantity(qty, line.product_uom_id)
            #         print('qty_to_boml ', qty_to_boml)
            #         qty_remain = qty_to_boml - (line.product_qty * len(project_task_by_project))
            #         # # จำนวน onhand ไปหน่วย onhand
            #         qty_remain = line.product_uom_id._compute_quantity(qty_remain, line.product_id.uom_id)
            #         worksheet.write(i_row, i_col, qty_remain or ' ', for_right_border)

        workbook.close()