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


class maintenance_report(models.TransientModel):
    _name = 'maintenance.report.detail'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    state = fields.Many2one('maintenance.stage' ,string="State")
    operating_unit_id = fields.Many2many('operating.unit', string='Operating Unit')


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

        if self.operating_unit_id and self.state:
            for i in  self.operating_unit_id:
                print('1')
                operating_ids = self.env['maintenance.request'].sudo().search([('operating_unit_id', '=', i.id),
                                                                        ('stage_id', '=' ,self.state.id),
                                                                        ('request_date' ,'>=',self.date_from),
                                                                        ('request_date' ,'<=',self.date_to)])
                print(operating_ids)
        elif not self.operating_unit_id and self.state:
            print('2')
            operating_ids = self.env['maintenance.request'].sudo().search([('stage_id', '=' ,self.state.id),
                                                                    ('request_date', '>=', self.date_from),
                                                                    ('request_date', '<=', self.date_to)]),
        else:
            print('3')
            operating_ids = self.env['maintenance.request'].sudo().search([('request_date', '>=', self.date_from),
                                                                    ('request_date', '<=', self.date_to)]),

        print('operating_ids:',operating_ids)
        print('===================')



        inv_row = 1

        # ----------------HEADDER-------------------------------------
        worksheet = workbook.add_sheet('Maintenance')

        worksheet.col(0).width = 3000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 10000
        worksheet.col(3).width = 4500
        worksheet.col(4).width = 6000
        worksheet.col(5).width = 6000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 4000
        worksheet.col(8).width = 4000
        worksheet.col(9).width = 4000
        worksheet.col(10).width = 4000

        worksheet.write_merge(0, 0, 0, 10, 'รายงานการซ่อมบำรุง', GREEN_TABLE_HEADER)
        worksheet.write(inv_row, 0, 'วันที่', for_center_bold)
        worksheet.write(inv_row, 1, 'Maintenance Request', for_center_bold)
        worksheet.write(inv_row, 2, 'รายละเอียดการแจ้งซ่อม', for_center_bold)
        worksheet.write(inv_row, 3, 'ผู้แจ้ง', for_center_bold)
        worksheet.write(inv_row, 4, 'สาขา', for_center_bold)
        worksheet.write(inv_row, 5, 'ผู้รับผิดชอบ', for_center_bold)
        worksheet.write(inv_row, 6, 'Repair No', for_center_bold)
        worksheet.write(inv_row, 7, 'รายการอะไหล่', for_center_bold)
        worksheet.write(inv_row, 8, 'ช่างผู้เข้าซ่อม', for_center_bold)
        worksheet.write(inv_row, 9, 'รายละเอียดการซ่อม', for_center_bold)
        worksheet.write(inv_row, 10, 'Point', for_center_bold)

        i = 0
        sum_point = 0
        for operating_id in operating_ids:
            print('operating_id:',operating_id)
            for operating in operating_id:
                print('operating:',operating)
                i += 1
                inv_row += 1
                worksheet.write(inv_row, 0, strToDate(operating.request_date).strftime("%d/%m/%Y") or '', for_center)
                worksheet.write(inv_row, 1, operating.name or '', for_center)
                worksheet.write(inv_row, 2, operating.description or '', for_center)
                worksheet.write(inv_row, 3, operating.employee_id.name or '', for_center)
                worksheet.write(inv_row, 4, operating.operating_unit_id.name or '', for_center)
                worksheet.write(inv_row, 5, operating.technician_user_id.name or '', for_center)
                if operating.repair_ids:
                    employee = ''
                    for operating_line in operating.repair_ids:
                        if operating_line.engineer1:
                            for emp in operating_line.engineer1:
                                employee += emp.name + ''
                        worksheet.write(inv_row, 6, operating_line.name or '', for_center)
                        worksheet.write(inv_row, 8, str(employee) or '', for_center)
                        worksheet.write(inv_row, 9, operating_line.internal_notes or '', for_center)
                        worksheet.write(inv_row, 10, operating_line.point or '', for_center)
                        sum_point += operating_line.point
                        if operating_line.operations:
                            for repair_ids in operating_line.operations:
                                worksheet.write(inv_row, 7, repair_ids.name or '', for_center)
                                inv_row += 1
                        else:
                            worksheet.write(inv_row, 7, '', for_center)
                            inv_row += 1

                    inv_row -= 1
                else:
                    worksheet.write(inv_row, 6, '', for_center)
                    worksheet.write(inv_row, 7, '', for_center)
                    worksheet.write(inv_row, 8, '', for_center)
                    worksheet.write(inv_row, 9, '', for_center)
                    worksheet.write(inv_row, 10, '', for_center)
        inv_row += 1
        worksheet.write(inv_row, 9, 'รวม', for_center_bold)
        worksheet.write(inv_row, 10, sum_point or '', for_center)

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE asset_excel_export CASCADE")
        wizard_id = self.env['maintenance.excel.export'].create(
            vals={'name': 'maintenance Report.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class maintenance_excel_export(models.TransientModel):
    _name = 'maintenance.excel.export'

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
            'res_model': 'maintenance.report.detail',
            'target': 'new',
        }


