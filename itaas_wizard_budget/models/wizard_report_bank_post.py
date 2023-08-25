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


class wizard_report_bank_post(models.TransientModel):
    _name = 'wizard.report.bank.post'

    # date_from = fields.Date(string='Date From', required=True)
    journal_ids = fields.Many2many('account.journal',string='Journal')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To', required=True)
    type = fields.Selection([('pending','Pending'),('done','Done'),('all','All')],string='Type')

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

        bank_statement_ids = self.env['account.bank.statement.line']
        domain_pending = [('pos_statement_id','!=',False),('date', '<=', self.date_to),('is_not_post', '!=', True),('is_done', '!=', True)]
        domain_done = [('pos_statement_id', '!=', False), ('date', '<=', self.date_to), ('is_not_post', '!=', True),('is_done', '=', True),('account_voucher_id.date', '>', self.date_to)]


        if self.journal_ids:
            domain_pending.append(('journal_id', 'in', self.journal_ids.ids))
            domain_done.append(('journal_id', 'in', self.journal_ids.ids))

        if self.type == 'pending':
            # domain.append(('is_done', '!=', True))
            pending_bank_statement_ids = self.env['account.bank.statement.line'].search(domain_pending,order='date,pos_config')
            done_bank_statement_after_date_ids = False
        elif self.type == 'done':
            pending_bank_statement_ids = False
            # domain.append(('is_done', '=', True))
            # domain.append(('account_voucher_id.date', '>', self.date_to))
            done_bank_statement_after_date_ids = self.env['account.bank.statement.line'].search(domain_done,order='date,pos_config')
        elif self.type == 'all':
            # domain_pending = domain
            # domain_done = domain
            # domain_pending.append(('is_done', '!=', True))
            # domain_done.append(('is_done', '=', True))
            # domain_done.append(('account_voucher_id.date', '>', self.date_to))
            print ('DOMAIN')
            # print (domain)
            print (domain_done)
            print (domain_pending)
            pending_bank_statement_ids = self.env['account.bank.statement.line'].search(domain_pending, order='date,pos_config')
            done_bank_statement_after_date_ids = self.env['account.bank.statement.line'].search(domain_done, order='date,pos_config')


        if pending_bank_statement_ids and done_bank_statement_after_date_ids:
            bank_statement_ids = pending_bank_statement_ids + done_bank_statement_after_date_ids
        elif pending_bank_statement_ids:
            bank_statement_ids = pending_bank_statement_ids
        elif done_bank_statement_after_date_ids:
            bank_statement_ids = done_bank_statement_after_date_ids

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

        worksheet.write_merge(1, 1, 1, 9, 'รายงานคงเหลือบัตรเครดิต,เงินสด,ลูกหนี้เงินขาด-ศูนย์บริการ', for_center_bold)
        worksheet.write_merge(2, 2, 1, 9, 'ณ วันที่:' + strToDate(self.date_to).strftime("%d/%m/%Y"), for_center_bold)

        sum_all = 0
        inv_row = 3
        worksheet.write(inv_row, 1, 'Branch', for_left_head)
        worksheet.write(inv_row, 2, 'Date', for_left_head)
        worksheet.write(inv_row, 3, 'Amount', for_left_head)
        worksheet.write(inv_row, 4, 'Reference', for_left_head)
        worksheet.write(inv_row, 5, 'Note', for_left_head)
        worksheet.write(inv_row, 6, 'Journal', for_left_head)
        worksheet.write(inv_row, 7, 'POS statement', for_left_head)
        worksheet.write(inv_row, 8, 'Status', for_left_head)
        worksheet.write(inv_row, 9, 'วันที่นำฝาก', for_left_head)
        worksheet.write(inv_row, 10, 'GL#1', for_left_head)
        worksheet.write(inv_row, 11, 'GL#2', for_left_head)

        for statement_id in bank_statement_ids:
            inv_row += 1

            worksheet.write(inv_row, 1, statement_id.pos_config.sudo().name, for_left)
            worksheet.write(inv_row, 2, strToDate(statement_id.date).strftime("%d/%m/%Y"), for_left)
            worksheet.write(inv_row, 3, statement_id.amount, for_right)
            worksheet.write(inv_row, 4, statement_id.name, for_left)
            worksheet.write(inv_row, 5, statement_id.note, for_left)
            worksheet.write(inv_row, 6, statement_id.journal_id.name, for_left)
            worksheet.write(inv_row, 7, statement_id.statement_id.name, for_left)
            worksheet.write(inv_row, 8, statement_id.is_done, for_left)
            if statement_id.is_done and statement_id.account_voucher_id:
                date = strToDate(statement_id.account_voucher_id.date).strftime("%d/%m/%Y")
            else:
                date = ""
            worksheet.write(inv_row, 9, date, for_left)

            if statement_id.journal_entry_ids.sudo():
                try:
                    worksheet.write(inv_row, 10, statement_id.journal_entry_ids[0].sudo().move_id.name, for_left)
                except:
                    worksheet.write(inv_row, 10, "GL NOT FOUND", for_left)

            else:
                worksheet.write(inv_row, 10, "", for_left)

            if statement_id.account_voucher_id and statement_id.account_voucher_id.date <= self.date_to:

                worksheet.write(inv_row, 11, statement_id.account_voucher_id.number, for_left)
            elif statement_id.account_voucher_id:
                worksheet.write(inv_row, 11, statement_id.account_voucher_id.number, for_left)
            else:
                worksheet.write(inv_row, 11, "", for_left)


            sum_all += statement_id.amount

        inv_row += 1
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
        self._cr.execute("TRUNCATE wizard_report_bank_post_excel_export CASCADE")
        wizard_id = self.env['wizard.report.bank.post.excel.export'].create(
            vals={'name': 'รายงานคงเหลือบัตรเครดิต.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.report.bank.post.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }

    @api.multi
    def print_report_movement(self):
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

        bank_statement_ids = self.env['account.bank.statement.line']
        # domain_pending = [('pos_statement_id','!=',False),('date', '<=', self.date_to),('is_not_post', '!=', True),('is_done', '!=', True)]
        # domain_done = [('pos_statement_id', '!=', False), ('date', '<=', self.date_to), ('is_not_post', '!=', True),('is_done', '=', True),('account_voucher_id.date', '>', self.date_to)]

        domain = [('pos_statement_id', '!=', False), ('date', '<=', self.date_to), ('is_not_post', '!=', True)]

        if self.date_from:
            domain.append(('date', '>=', self.date_from))
            if self.journal_ids:
                account_id = self.journal_ids[0].default_debit_account_id
                if account_id:
                    params_2 = (self.date_from,account_id.id)
                    redeem_query = """SELECT aml.debit,aml.credit
                                                                                               FROM account_move_line AS aml
                                                                                               JOIN account_move m ON aml.move_id = m.id
                                                                                               WHERE aml.date < %s and m.state = 'posted' and aml.account_id = %s
                                                                                                """

                    self.env.cr.execute(redeem_query, params_2)
                    res = self.env.cr.fetchall()
                    print ('RES',res)
                    balance = sum(line[0] - line[1] for line in res)
                else:
                    balance = 0

            else:
                balance = 0
        else:
            balance = 0

        if self.journal_ids:
            # domain_pending.append(('journal_id', 'in', self.journal_ids.ids))
            # domain_done.append(('journal_id', 'in', self.journal_ids.ids))
            domain.append(('journal_id', 'in', self.journal_ids.ids))
            # print ('DOMAIN')
            # print (domain)

        # if self.type == 'pending':
        #     # domain.append(('is_done', '!=', True))
        #     pending_bank_statement_ids = self.env['account.bank.statement.line'].search(domain_pending,order='date,pos_config')
        #     done_bank_statement_after_date_ids = False
        # elif self.type == 'done':
        #     pending_bank_statement_ids = False
        #     # domain.append(('is_done', '=', True))
        #     # domain.append(('account_voucher_id.date', '>', self.date_to))
        #     done_bank_statement_after_date_ids = self.env['account.bank.statement.line'].search(domain_done,order='date,pos_config')
        # elif self.type == 'all':
        #     # domain_pending = domain
        #     # domain_done = domain
        #     # domain_pending.append(('is_done', '!=', True))
        #     # domain_done.append(('is_done', '=', True))
        #     # domain_done.append(('account_voucher_id.date', '>', self.date_to))
        #     print ('DOMAIN')
        #     # print (domain)
        #     print (domain_done)
        #     print (domain_pending)
        #     pending_bank_statement_ids = self.env['account.bank.statement.line'].search(domain_pending, order='date,pos_config')
        #     done_bank_statement_after_date_ids = self.env['account.bank.statement.line'].search(domain_done, order='date,pos_config')
        bank_statement_ids = self.env['account.bank.statement.line'].sudo().search(domain, order='date,pos_config')


        # if pending_bank_statement_ids and done_bank_statement_after_date_ids:
        #     bank_statement_ids = pending_bank_statement_ids + done_bank_statement_after_date_ids
        # elif pending_bank_statement_ids:
        #     bank_statement_ids = pending_bank_statement_ids
        # elif done_bank_statement_after_date_ids:
        #     bank_statement_ids = done_bank_statement_after_date_ids



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

        worksheet.write_merge(1,1, 1, 9, 'รายงานคงเหลือบัตรเครดิต,เงินสด,ลูกหนี้เงินขาด-ศูนย์บริการ', for_center_bold)
        worksheet.write_merge(2,2, 1, 9, 'ณ วันที่:' + strToDate(self.date_to).strftime("%d/%m/%Y") , for_center_bold)

        sum_all = 0
        inv_row = 3
        worksheet.write(inv_row, 1, 'Branch', for_left_head)
        worksheet.write(inv_row, 2, 'Date', for_left_head)
        worksheet.write(inv_row, 3, 'Amount', for_left_head)
        worksheet.write(inv_row, 4, 'Reference', for_left_head)
        worksheet.write(inv_row, 5, 'Note', for_left_head)
        worksheet.write(inv_row, 6, 'Journal', for_left_head)
        worksheet.write(inv_row, 7, 'POS statement', for_left_head)
        worksheet.write(inv_row, 8, 'Status', for_left_head)
        worksheet.write(inv_row, 9, 'วันที่นำฝาก', for_left_head)
        worksheet.write(inv_row, 10, 'GL#1', for_left_head)
        worksheet.write(inv_row, 11, 'GL#2', for_left_head)
        worksheet.write(inv_row, 12, 'Balance', for_left_head)

        #balance line
        inv_row +=1
        worksheet.write(inv_row, 1, 'Balance ยกมา', for_left)
        worksheet.write(inv_row, 2, (strToDate(self.date_from) - relativedelta(days=1)).strftime("%d/%m/%Y"), for_left)
        worksheet.write(inv_row, 3, balance, for_right)
        worksheet.write(inv_row, 4, '', for_left)
        worksheet.write(inv_row, 5, '', for_left)
        worksheet.write(inv_row, 6, '', for_left)
        worksheet.write(inv_row, 7, '', for_left)
        worksheet.write(inv_row, 8, '', for_left)
        worksheet.write(inv_row, 9, '', for_left)
        worksheet.write(inv_row, 10, '', for_left)
        worksheet.write(inv_row, 11, '', for_left)
        worksheet.write(inv_row, 12, balance, for_right)

        #
        print ('bank_statement_ids',bank_statement_ids)
        for statement_id in bank_statement_ids:
            inv_row +=1
            value_in = statement_id.amount
            value_out = 0
            worksheet.write(inv_row, 1, statement_id.pos_config.sudo().name, for_left)
            worksheet.write(inv_row, 2, strToDate(statement_id.date).strftime("%d/%m/%Y"), for_left)
            worksheet.write(inv_row, 3, statement_id.amount, for_right)
            worksheet.write(inv_row, 4, statement_id.name, for_left)
            worksheet.write(inv_row, 5, statement_id.note, for_left)
            worksheet.write(inv_row, 6, statement_id.journal_id.name, for_left)
            worksheet.write(inv_row, 7, statement_id.statement_id.name, for_left)
            worksheet.write(inv_row, 8, statement_id.is_done, for_left)
            if statement_id.is_done and statement_id.account_voucher_id:
                date = strToDate(statement_id.account_voucher_id.date).strftime("%d/%m/%Y")
            else:
                date = ""
            worksheet.write(inv_row, 9, date, for_left)

            if statement_id.journal_entry_ids.sudo():
                try:
                    worksheet.write(inv_row, 10, statement_id.journal_entry_ids[0].sudo().move_id.name, for_left)
                except:
                    worksheet.write(inv_row, 10, "GL NOT FOUND", for_left)

            else:
                worksheet.write(inv_row, 10, "", for_left)

            if statement_id.account_voucher_id and statement_id.account_voucher_id.date <= self.date_to:
                value_out = statement_id.amount
                worksheet.write(inv_row, 11, statement_id.account_voucher_id.number, for_left)
            elif statement_id.account_voucher_id:
                worksheet.write(inv_row, 11, statement_id.account_voucher_id.number, for_left)
            else:
                worksheet.write(inv_row, 11, "", for_left)

            # print ('Balance before', balance)
            # print ('value_in', value_in)
            # print ('value_out', value_out)
            # current = value_in - value_out
            # print ('Current',current)
            balance += (value_in - value_out)
            # print ('Balance after', balance)
            worksheet.write(inv_row, 12, balance, for_right)
            # sum_all += statement_id.amount

        inv_row+=1
        # worksheet.write_merge(inv_row, inv_row,1,2, 'SUM', for_left)

        # worksheet.write(inv_row, 3, sum_all, for_right)


        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE wizard_report_bank_post_excel_export CASCADE")
        wizard_id = self.env['wizard.report.bank.post.excel.export'].create(
            vals={'name': 'รายงานคงเหลือบัตรเครดิต.xls', 'report_file': ctx['report_file']})

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.report.bank.post.excel.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class wizard_report_bank_post_excel_export(models.TransientModel):
    _name = 'wizard.report.bank.post.excel.export'

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
            'res_model': 'wizard.report.bank.post',
            'target': 'new',
        }


