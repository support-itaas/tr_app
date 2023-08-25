# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from operator import itemgetter
from io import BytesIO
from odoo import models, fields, api, _
from datetime import datetime,date
import xlwt
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))


class Pos_report_detail(models.TransientModel):
    _name = 'pos.report.detail'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    branch = fields.Many2one('pos.config' ,string="สาขา")


    @api.multi
    def print_report(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        font = xlwt.Font()
        font.bold = True
        font.bold = True
        for_right = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz right,vertical center;")
        for_right.num_format_str = '#,##0.00'
        # for_right_bold = xlwt.easyxf(
        #     "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz right,vertical center; borders: top thin, bottom thin, left thin, right thin")
        # for_right_bold.num_format_str = '#,###.00'
        for_center = xlwt.easyxf(
            "font: name  Times New Roman, color black,  height 180; align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")
        for_center_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman, color black, height 180;  align: horiz center,vertical center,wrap on; borders: top thin, bottom thin, left thin, right thin")
        for_left_bold_no_border = xlwt.easyxf(
            "font: name  Times New Roman, color black, height 200;  align: horiz left,vertical center;")

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
        print('xxx:',self.branch.name)
        pos_ids = self.env['pos.order'].search([('date_order', '>=',self.date_from ),('date_order', '<=', self.date_to),
                                                ('config_id.name', '=', self.branch.name)])

        print('pos_ids:',pos_ids)
        print('===================')

        inv_row = 6

        # ----------------HEADDER-------------------------------------
        worksheet = workbook.add_sheet('Pos')
        worksheet.write_merge(0, 0, 0, 10, 'รายงานต้นทุน Pos', GREEN_TABLE_HEADER)
        worksheet.write(1, 0, 'บริษัท', for_center_bold)
        worksheet.write(1, 1, self.env.user.company_id.name, for_center_bold)
        worksheet.write(2, 0, 'วันที่', for_center_bold)
        worksheet.write(2, 1, self.date_from, for_center_bold)
        worksheet.write(2, 2, 'ถึงวันที่', for_center_bold)
        worksheet.write(2, 3, self.date_to, for_center_bold)
        worksheet.write(3, 0, 'สาขา', for_center_bold)
        worksheet.write(3, 1, self.branch.name, for_center_bold)

        worksheet.write(5, 0, 'ลำดับ', for_center_bold)
        worksheet.write(5, 1, 'รหัสสินค้า', for_center_bold)
        worksheet.write(5, 2, 'รายละเอียด', for_center_bold)
        worksheet.write(5, 3, 'หน่วยนับ', for_center_bold)
        worksheet.write(5, 4, 'ปริมาณขายสุทธิ', for_center_bold)
        worksheet.write(5, 5, 'มูลค่าขาย', for_center_bold)
        worksheet.write(5, 6, '(%)', for_center_bold)
        worksheet.write(5, 7, 'ต้นทุนขายสุทธิ', for_center_bold)
        worksheet.write(5, 8, 'กำไรขึ้นต้น', for_center_bold)
        worksheet.write(5, 9, '(%)', for_center_bold)

        pos_all = []
        pos_product = []
        pos_value = []
        real = []
        count = 0

        qty = 0
        total = 0
        percent = 0
        for pos_id in pos_ids:
            for pos_line in pos_id.lines:
                percent += pos_line.price_subtotal_incl
                pos_all.append(pos_line)

        index = 0
        standard = 0
        sub_total = 0
        print('percent:',percent)
        for pos in pos_all:
            if pos.product_id.id not in pos_product:
                print('order_id:',pos.order_id.name)
                total += pos.price_subtotal_incl
                pos_product.append(pos.product_id.id)

                if pos.order_id.picking_id and pos.order_id.picking_id.state == 'done' and pos.order_id.picking_id.move_lines.filtered(lambda t: t.product_id == pos.product_id):
                    move_line_ids = pos.order_id.picking_id.move_lines.filtered(lambda t: t.product_id == pos.product_id)
                    standard = abs(move_line_ids[0].value)
                    if not standard:
                        standard = 1

                elif pos.product_id.standard_price:
                    standard = pos.product_id.standard_price
                else:
                    standard = 1



                profit = pos.price_subtotal_incl / standard
                value = {'product_ref': pos.product_id.default_code,
                         'prduct_name': pos.product_id.name,
                         'product_id': pos.product_id.id,
                         'product_uom': pos.product_id.uom_id.name,
                         'qty':  pos.qty,
                         'total': pos.price_subtotal_incl,
                         'percent': pos.price_subtotal_incl / percent  ,
                         'cost': standard,
                         'profit': profit,
                         'percent_total': profit / standard,
                         }
                pos_value.append(value)
            else:
                for i in pos_value:
                    if i['product_id'] == pos.product_id.id:
                        if pos.order_id.picking_id and pos.order_id.picking_id.state == 'done' and pos.order_id.picking_id.move_lines.filtered(
                                lambda t: t.product_id == pos.product_id):
                            move_line_ids = pos.order_id.picking_id.move_lines.filtered(
                                lambda t: t.product_id == pos.product_id)
                            standard = abs(move_line_ids[0].value)
                            if not standard:
                                standard = 1

                        elif pos.product_id.standard_price:
                            standard = pos.product_id.standard_price
                        else:
                            standard = 1
                        profit = pos.price_subtotal_incl / standard
                        i['qty'] = i['qty'] + pos.qty
                        i['total'] = i['total'] + pos.price_subtotal_incl
                        i['percent'] = i['percent'] + (pos.price_subtotal_incl / percent)
                        i['profit'] = i['profit'] + profit
                        i['percent_total'] = i['percent_total'] + profit / standard

            print('xxxxxxxxxxxxx')
            print(len(real))

        for pos_real in pos_value:
            count += 1

            worksheet.write(inv_row, 0, count, for_center)
            worksheet.write(inv_row, 1, pos_real['product_ref'] or '', for_center)
            worksheet.write(inv_row, 2, pos_real['prduct_name'] or '', for_center)
            worksheet.write(inv_row, 3, pos_real['product_uom'] or '', for_center)
            worksheet.write(inv_row, 4, pos_real['qty'] or '', for_right)
            worksheet.write(inv_row, 5, pos_real['total'] or '', for_right)
            worksheet.write(inv_row, 6, pos_real['percent'] or '', for_right)
            worksheet.write(inv_row, 7, pos_real['cost'] or '', for_right)
            worksheet.write(inv_row, 8, pos_real['profit'] or '', for_right)
            worksheet.write(inv_row, 9, pos_real['percent_total'] or '', for_right)

            inv_row += 1






        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['pos.excel.export'].create(
            vals={'name': 'Pos Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class maintenance_excel_export(models.TransientModel):
    _name = 'pos.excel.export'

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
            'res_model': 'pos.report.detail',
            'target': 'new',
        }


