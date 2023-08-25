# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from datetime import datetime
import xlwt
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar
from odoo.tools import float_compare, float_is_zero
from datetime import datetime,date
import locale
from io import BytesIO

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class hr_report(models.TransientModel):
    _name = 'hr.report'

    report_type = fields.Selection([('type_1', 'สปส. 1-10 ส่วนที่ 1'),
                                    ('type_2', 'สปส. 1-10 ส่วนที่ 2'),
                                    ('type_3', 'แบบยื่นรายการภาษีเงินได้ หัก ณ ที่จ่าย'),
                                    ('type_4', 'แบบยื่นรายการภาษีเงินได้ หัก ณ ที่จ่าย (ใบแนบ)'),
                                    ('type_5', 'แบบยื่นรายงานภาษีเงินได้ หัก ณ ที่จ่าย ภ.ง.ด. 1ก'),
                                    ('type_6', 'แบบยื่นรายการภาษีเงินได้ หัก ณ ที่จ่าย ภ.ง.ด. 1ก (ใบแนบ)'),
                                    ('type_7', 'รายการ กท. 20 ประจำปี'),
                                    ('type_8', 'สปส. 1-02'),
                                    ('type_9', 'สปส. 1-03 (สำหรับผู้ที่เคยยื่นแล้ว)'),
                                    ('type_10', 'สปส. 6-09'),
                                    ('type_11', 'กองทุนสำรองเลี้ยงชีพ'),
                                    ('type_12', 'Export ภงด 1'),
                                    ('type_13', 'Export SSO'),
                                    ('type_13', 'Export SSO'),
                                    ('type_14', 'หนังสือรับรองการหัก ณ ที่จ่าย 50 (ทวิ)')],
                                   string='Form Name', required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.user.company_id.id)
    wage_type = fields.Selection(
        [('monthly', 'Monthly'), ('daily', 'Daily')], string='Wage Type')
    fiscal_id = fields.Many2one('hr.fiscalyear', string='Fiscal Year')

    period_id = fields.Many2one('hr.period', string='Period')
    con_branch_id = fields.Many2one('contract.branch', string='Contract Branch')

    @api.model
    def default_get(self, fields):
        res = super(hr_report, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, curr_date.month, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def print_hr_report(self, data):
        data['form'] = self.read(['report_type','date_from','date_to','company_id','fiscal_id','period_id','wage_type','con_branch_id'])[0]
        if data['form']['report_type'] == 'type_1':
            return self.env.ref('report_hr.sps1_10_1_period').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_2':
            return self.env.ref('report_hr.sps1_10_2_period').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_3':
            return self.env.ref('report_hr.pd_1_1_report_period').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_4':
            return self.env.ref('report_hr.pd_1_2_report_period').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_5':
            return self.env.ref('report_hr.pngd_1kor_report').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_6':
            return self.env.ref('report_hr.pngd_1kor_nap_report').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_7':
            return self.env.ref('report_hr.kortor20kor_report').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_8':
            return self.env.ref('report_hr.sps1_02_report').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_9':
            return self.env.ref('report_hr.sps1_03_2_report').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_10':
            return self.env.ref('report_hr.sps6_09_report').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_11':
            return self.env.ref('report_hr.pvd_report').report_action(self, data=data, config=False)
        elif data['form']['report_type'] == 'type_14':
            return self.env.ref('report_hr.teejai_50_all_report').report_action(self, data=data, config=False)

    @api.multi
    def get_bank_report(self):

        context = dict(self._context or {})
        file_type = context.get('file')

        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')

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
        final_text = ""
        final_text_body = ""

        # -------------------------------------- PND 1 ----------------------------------------
        if self.report_type == 'type_12':

            payslip_ids = self.env['hr.payslip'].search([('date_from', '>=', self.date_from),
                                                         ('date_from', '<=', self.date_to),
                                                         ('state', '=', 'done')], order='date_payment ASC')

            # | 1 ฟิก | 1 ลำดับ | 3200500344615เลขปปช | 0000000000 ฟิก | นาย | ไชยา | สุริยาพรพันธุ์ | 30112563 | 54100.00 | 1379.00 | 1 |
            slip_ids = ""
            inv_row = 1
            for slip in payslip_ids:
                slip_ids += '|401N|'
                slip_ids += str(inv_row) + '|'
                slip_ids += str(slip.employee_id.identification_id) + '|'
                slip_ids += '0000000000|'
                slip_ids += str(slip.employee_id.title.name) + '|'
                slip_ids += str(slip.employee_id.first_name) + '|'
                slip_ids += str(slip.employee_id.last_name) + '|'

                if slip.date_payment:
                    date = datetime.strptime(slip.date_payment, "%Y-%m-%d").date()
                    if len(str(date.day)) < 2:
                        day = '0' + str(date.day)
                    else:
                        day =str(date.day)
                    if len(str(date.month)) < 2:
                        month = '0' + str(date.month)
                    else:
                        month = str(date.month)
                    date_payment = day + month + str(date.year+543)

                slip_ids += date_payment + '|'
                slip_ids += str(locale.format("%.2f", float(slip.sum_total_tax + slip.summary_for_tax_one))) + '|'
                slip_ids += str(locale.format("%.2f", float(slip.deduct02))) + '|'
                slip_ids += '1|' + "\r\n"

                final_text = final_text_body + str(slip_ids)

                inv_row += 1

        # ------------------------------------ End PND 1 -------------------------------------------------

        else:
            raise UserError(_('There is record this date range.'))

        values = {
            'name': "PND 1 Report",
            'datas_fname': 'PND_1_report.txt',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.b64encode((final_text).encode("utf-8")),
        }
        attachment_id = self.env['ir.attachment'].sudo().create(values)
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }

    def mb_substr(self, txt, start, length=None, encoding="UTF-8"):
        # print(txt)
        # print("0000000000")
        # print(base64.b64encode((txt[0:30]).encode("utf-8")))

        # u_s = txt.decode(encoding)
        # Str = Str.encode('base64', 'strict');

        return txt[0:30]
        # return (u_s[start:(start + length)] if length else u_s[start:]).encode(encoding)

    def get_sso_report(self):
        print("get_sso_report")
        date_strat = self.period_id.date_start
        date_end = self.period_id.date_end

        payslip_ids = self.env['hr.payslip'].search(
            [('date_from', '>=', date_strat),
             ('date_to', '<=', date_end)]
            , order='date_payment ASC')

        payslip_con_ids = payslip_ids.filtered(lambda x: x.contract_id.con_branch_id == self.con_branch_id)

        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet(self.con_branch_id.name)

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

        inv_row = 0

        if payslip_con_ids:
            worksheet.write(inv_row, 0, 'เลขปรจำประชาชน', for_center_bold)
            worksheet.write(inv_row, 1, 'คำนำหน้าชื่อ', for_center_bold)
            worksheet.write(inv_row, 2, 'ชื่อผู้ประกันตน', for_center_bold)
            worksheet.write(inv_row, 3, 'นามสกุลผู้ประกันตน', for_center_bold)
            worksheet.write(inv_row, 4, 'ค่าจ้าง', for_center_bold)
            worksheet.write(inv_row, 5, 'จำนวนเงินสมทบ', for_center_bold)
            inv_row = 1
            for pay in payslip_con_ids:
                worksheet.write(inv_row, 0, pay.employee_id.sso_id or "-", for_right)
                worksheet.write(inv_row, 1, pay.employee_id.title.shortcut or "-", for_right)
                worksheet.write(inv_row, 2, pay.employee_id.first_name or "-", for_right)
                worksheet.write(inv_row, 3, pay.employee_id.last_name or "-", for_right)
                worksheet.write(inv_row, 4, pay.sum_total_sso, for_right)
                worksheet.write(inv_row, 5, pay.deduct09, for_right)
                inv_row += 1
        else:
            raise UserError(_('There is record this date range.'))

        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE sso_excel_export CASCADE")

        wizard_id = self.env['sso.excel.export'].create(vals={'name': 'export_sso.xls',
                                                              'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sso.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

class sso_excel_export(models.TransientModel):
    _name = 'sso.excel.export'

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
            'res_model': 'hr.report',
            'target': 'new',
        }