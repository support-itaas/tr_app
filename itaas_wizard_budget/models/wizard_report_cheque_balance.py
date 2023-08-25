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


class wizard_report_cheque_balance(models.TransientModel):
    _name = 'wizard.report.cheque.balance'

    # date_from = fields.Date(string='Date From', required=True)
    type = fields.Selection([('pay','Payment'),('rec','Receive')])
    date_to = fields.Date(string='Date To', required=True)
    journal_ids = fields.Many2many('account.journal', string='Journal')

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
        for_left_head = xlwt.easyxf(
            "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")

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

        cheque_statement_ids = self.env['account.cheque.statement']

        pending_domain = [('issue_date', '<=', self.date_to),('state', '=', 'open'),('type','=',self.type)]
        done_domain = [('issue_date', '<=', self.date_to),('state', '=', 'confirm'),('type','=',self.type),'|',('account_voucher_id.date', '>', self.date_to),('move_new_id.date', '>',self.date_to)]

        if self.journal_ids:
            pending_domain.append(('journal_id', 'in', self.journal_ids.ids))
            done_domain.append(('journal_id', 'in', self.journal_ids.ids))

        pending_account_cheque_statement_ids = self.env['account.cheque.statement'].search(pending_domain,order='cheque_date')

        done_account_cheque_statement_ids = self.env['account.cheque.statement'].search(done_domain,order='cheque_date')

        if pending_account_cheque_statement_ids and done_account_cheque_statement_ids:
            cheque_statement_ids = pending_account_cheque_statement_ids + done_account_cheque_statement_ids
        elif pending_account_cheque_statement_ids:
            cheque_statement_ids = pending_account_cheque_statement_ids
        elif done_account_cheque_statement_ids:
            cheque_statement_ids = done_account_cheque_statement_ids



        # ----------------HEADDER-------------------------------------
        worksheet = workbook.add_sheet('รายงานคงเหลือ')
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

        worksheet.write_merge(1,1, 1, 8, 'รายงานคงเหลือเช็ค และ บัตรเครดิต', for_center_bold)
        worksheet.write_merge(2,2, 1, 8, 'ณ วันที่:' + strToDate(self.date_to).strftime("%d/%m/%Y") , for_center_bold)

        sum_all = 0
        inv_row = 3
        worksheet.write(inv_row, 1, 'Partner', for_left_head)
        worksheet.write(inv_row, 2, 'Cheque Date', for_left_head)
        worksheet.write(inv_row, 3, 'Amount', for_left_head)
        worksheet.write(inv_row, 4, 'Cheque Number', for_left_head)
        worksheet.write(inv_row, 5, 'Journal', for_left_head)
        worksheet.write(inv_row, 6, 'Reference', for_left_head)
        worksheet.write(inv_row, 7, 'Status', for_left_head)
        worksheet.write(inv_row, 8, 'วันที่ดำเนินการ', for_left_head)
        worksheet.write(inv_row, 9, 'รายการผ่านเช็ค', for_left_head)

        for statement_id in cheque_statement_ids:
            inv_row +=1
            try:
                worksheet.write(inv_row, 1, statement_id.partner_id.name, for_left)
                worksheet.write(inv_row, 2, strToDate(statement_id.issue_date).strftime("%d/%m/%Y"), for_left)
                worksheet.write(inv_row, 3, statement_id.amount, for_right)
                worksheet.write(inv_row, 4, statement_id.cheque_number, for_left)
                worksheet.write(inv_row, 5, statement_id.journal_id.name, for_left)
                worksheet.write(inv_row, 6, statement_id.move_id.name, for_left)
                worksheet.write(inv_row, 7, statement_id.state, for_left)
                if statement_id.state == 'confirm' and statement_id.account_voucher_id:
                    date = strToDate(statement_id.account_voucher_id.date).strftime("%d/%m/%Y")
                    ref = statement_id.account_voucher_id.number

                elif statement_id.state == 'confirm' and statement_id.move_new_id:
                    date = strToDate(statement_id.move_new_id.date).strftime("%d/%m/%Y")
                    ref = statement_id.move_new_id.name
                else:
                    date = ""
                    ref = ""
                worksheet.write(inv_row, 8, date, for_left)
                worksheet.write(inv_row, 9, ref, for_left)

                sum_all += statement_id.amount
            except:
                continue


        inv_row+=1
        worksheet.write_merge(inv_row, inv_row,1,2, 'SUM', for_left)

        worksheet.write(inv_row, 3, sum_all, for_right)


        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE wizard_report_cheque_excel_export CASCADE")
        wizard_id = self.env['wizard.report.cheque.excel.export'].create(
            vals={'name': 'รายงานคงเหลือเช็ค.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.report.cheque.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class wizard_report_cheque_excel_export(models.TransientModel):
    _name = 'wizard.report.cheque.excel.export'

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
            'res_model': 'wizard.report.cheque.balance',
            'target': 'new',
        }


