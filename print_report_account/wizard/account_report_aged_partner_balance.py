# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime,timedelta,date
from odoo import api, models, fields, _
from io import BytesIO
import xlwt
import time
import xlsxwriter
import base64
from datetime import datetime, date
from odoo.exceptions import UserError
from odoo.tools import misc
import operator
import locale
from odoo.tools import float_compare, float_is_zero

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class AccountAgedTrialBalance(models.TransientModel):
    _inherit = 'account.aged.trial.balance'

    user_id = fields.Many2one('res.users',string='Sale Person')
    partner_id = fields.Many2one('res.partner', string="Partner")
    is_detail = fields.Boolean(string='Show Detail')
    difference_period = fields.Boolean(string='Difference Period')
    period_text = fields.Char(string='Multiple Period')
    account_id = fields.Many2one('account.account',string='Account')
    is_excel = fields.Boolean(string='Excel')
    category_ids = fields.Many2many('res.partner.category',string='Customer Category')


    def _print_report(self, data):
        print ('_print_report')
        data['form'].update(self.read(['user_id', 'partner_id', 'is_detail','difference_period','period_text','category_ids'])[0])
        return super(AccountAgedTrialBalance, self)._print_report(data)

    @api.multi
    def generate_xlsx_report(self):
        fl = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        # currency = self.env.user.company_id.currency_id.symbol or ''
        sheet = workbook.add_sheet('Aging Report')
        ###############################################################3
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
        for_center.num_format_str = '@'

        for_left = xlwt.easyxf(
            "font: name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")

        for_left_bold = xlwt.easyxf(
            "font: bold 1, name  Times New Roman,color black,  height 180;  align: horiz left,vertical center; borders: top thin, bottom thin, left thin, right thin")

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

        ###############################################################3

        # format1 = workbook.add_format({'font_size': 16, 'align': 'vcenter', 'bg_color': '#D3D3D3', 'bold': True})
        # format1.set_font_color('#000080')
        # format2 = workbook.add_format({'font_size': 12})
        # format3 = workbook.add_format({'font_size': 10, 'bold': True})
        # format4 = workbook.add_format({'font_size': 10})
        # format5 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        # format1.set_align('center')
        # format2.set_align('left')
        # format3.set_align('left')
        # format4.set_align('center')

        sheet.write_merge(0, 0, 3, 9, 'Aged Partner Balance', for_center_bold)
        row = 4
        col = 0

        if self.result_selection == 'customer':
            account_type = ['12-01-01-01']
        elif self.result_selection == 'supplier':
            account_type = ['22-01-01-01']
        else:
            account_type = ['22-01-01-01', '12-01-01-01']

        date_from = self.date_from
        target_move = self.target_move
        period_length = self.period_length
        is_detail = self.is_detail
        difference_period = self.difference_period
        period_text = self.period_text
        res = {}
        start = strToDate(date_from)
        if self.difference_period:
            periods = self.period_text.split(',')
            if len(periods) < 4:
                raise UserError(_('Period is not correct %s') % (self.period_text))
            lenght = 0
            for i in range(5)[::-1]:
                # print ('PRINT I',i)
                if i!=0:
                    stop = start - relativedelta(days=int(periods[lenght]))
                    period_length = periods[lenght]
                lenght+=1

                if i == 4:
                    name_from = '0'
                    name_to = period_length
                    name_to_str = "-" + name_to
                elif i != 0:
                    name_from = str(int(name_to) + 1)
                    name_to = str(int(period_length) + int(name_to))
                    name_to_str = "-" + name_to
                else:
                    name_from = str(int(name_to) + 1)
                    name_to = ""
                    name_to_str = ""


                res[str(i)] = {
                    'name': str(name_from) + str(name_to_str),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop - relativedelta(days=1)
        else:
            for i in range(5)[::-1]:
                stop = start - relativedelta(days=period_length - 1)
                print('START', start)
                print('STOP', stop)
                res[str(i)] = {
                    'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop - relativedelta(days=1)


        print ('-------RES')
        print (res)

        age_balance_obj = self.env['report.account.report_agedpartnerbalance']

        if self.partner_id:
            partner_id = self.partner_id.id
            user_id = False
        elif self.category_ids:
            all_partner_ids = []
            partner_ids_1 = self.env['res.partner'].search([('category_id','in',self.category_ids.ids)])
            if partner_ids_1:
                for pn in partner_ids_1:
                    all_partner_ids.append(pn.id)


            partner_id = all_partner_ids
            user_id = False
        elif self.user_id:
            all_partner_ids = []
            # partner_ids_1 = self.env['res.partner'].search([('user_id','=',self.user_id.id)])
            # if partner_ids_1:
            #     for pn in partner_ids_1:
            #         all_partner_ids.append(pn.id)

            invoice_partner_ids_2 = self.env['account.invoice'].search([('user_id', '=', self.user_id.id)])


            if invoice_partner_ids_2:
                for pn_inv in invoice_partner_ids_2:
                    if pn_inv.partner_id.id not in all_partner_ids:
                        all_partner_ids.append(pn_inv.partner_id.id)

            user_id = self.user_id.id
            partner_id = all_partner_ids
            if not partner_id:
                raise UserError(_("ไม่มีรายการของพนักงานขายคนนี้"))
        else:
            user_id = False
            partner_id = False

        movelines, total, dummy = age_balance_obj._get_partner_move_lines(account_type, date_from, target_move,period_length,partner_id,is_detail,user_id,difference_period,period_text)


        for partner in dummy:
            for line in dummy[partner]:
                line['intervals'] = {
                    '0': 0,
                    '1': 0,
                    '2': 0,
                    '3': 0,
                    '4': 0,
                    '5': 0,
                    'total': 0
                }
                line['intervals'][str(line['period'] - 1)] = line['amount']
                line['intervals']['total'] += line['amount']

        # form = data['form']
        print (row)
        print (col)

        sheet.write_merge(1, 1, 3, 5, 'Start Date :', for_center)
        sheet.write_merge(1, 1, 6, 9, date_from, for_center)

        sheet.write_merge(2, 2, 3, 5, 'Period Length (days) :', for_center)
        sheet.write_merge(2, 2, 6, 9, self.period_length, for_center)

        account_type = ""
        if self.result_selection == 'customer':
            account_type += "Receivable Accounts"
        elif self.result_selection == 'supplier':
            account_type += "Payable Accounts"
        else:
            account_type += "Receivable & Payable Accounts"
        target_move = ""
        if self.target_move == 'all':
            target_move += "All Entries"
        else:
            target_move += "All Posted Entries"

        sheet.write_merge(row, row, 3, 5, "Partner's :", for_center)
        sheet.write_merge(row, row, 6, 9, account_type, for_center)
        row += 1
        sheet.write_merge(row, row, 3, 5, 'Report Type :', for_center)
        sheet.write_merge(row, row, 6, 9,
                          "EXCEL", for_center)
        row += 2
        # constructing the table
        sheet.write_merge(row, row, col, col+2, "Partners", for_center)
        # sheet.set_column(col+2, col+9, 10)
        sheet.write(row, col+3, "Sales Person", for_center)
        sheet.write(row, col+4, "Date", for_center)
        sheet.write(row, col+5, "Due Date", for_center)
        sheet.write(row, col + 6, "Not Due", for_center)

        # sheet.write(row, col + 7, '1', for_center)
        # sheet.write(row, col + 8, '2', for_center)
        # sheet.write(row, col + 9, '3', for_center)
        # sheet.write(row, col + 10,'4', for_center)
        # sheet.write(row, col + 11,'5', for_center)

        sheet.write(row, col+7, res['4']['name'], for_center)
        sheet.write(row, col+8, res['3']['name'], for_center)
        sheet.write(row, col+9, res['2']['name'], for_center)
        sheet.write(row, col+10, res['1']['name'], for_center)
        sheet.write(row, col+11, res['0']['name'], for_center)
        sheet.write(row, col+12, "Total / (Over Due Date)", for_center)
        sheet.write(row, col+13, "ตั้งค่าเผื่อหนี้สังสัยจะสูญ", for_center)


        row += 2
        sheet.write_merge(row, row, col, col+2, "Account Total", for_center)
        if total:
            sheet.write(row, col + 6,
                        "{0:,.2f}".format(total[6]) and total[6] or '',
                        for_right)
            sheet.write(row, col + 7,
                        "{0:,.2f}".format(total[4]) and total[4] or '',
                        for_right)
            sheet.write(row, col + 8,
                        "{0:,.2f}".format(total[3]) and total[3] or '',
                        for_right)
            sheet.write(row, col + 9,
                        "{0:,.2f}".format(total[2]) and total[2] or '',
                        for_right)
            sheet.write(row, col + 10,
                        "{0:,.2f}".format(total[1]) and total[1] or '',
                        for_right)
            sheet.write(row, col + 11,
                        "{0:,.2f}".format(total[0]) and total[0] or '',
                        for_right)
            sheet.write(row, col + 12,
                        "{0:,.2f}".format(total[5]) and total[5] or '',
                        for_right)

        row += 1
        for partner in movelines:
            sheet.write_merge(row, row, col, col + 2, partner['name'], for_center)
            sheet.write(row, col + 6,
                        "{0:,.2f}".format(partner['direction']) and partner['direction'] or '',
                        for_right)
            sheet.write(row, col + 7,
                        "{0:,.2f}".format(partner['4']) and partner['4'] or '',
                        for_right)
            sheet.write(row, col + 8,
                        "{0:,.2f}".format(partner['3']) and partner['3'] or '',
                        for_right)
            sheet.write(row, col + 9,
                        "{0:,.2f}".format(partner['2']) and partner['2'] or '',
                        for_right)
            sheet.write(row, col + 10,
                        "{0:,.2f}".format(partner['1']) and partner['1'] or '',
                        for_right)
            sheet.write(row, col + 11,
                        "{0:,.2f}".format(partner['0']) and partner['0'] or '',
                        for_right)
            sheet.write(row, col + 12,
                        "{0:,.2f}".format(partner['total']) and partner['total'] or '',
                        for_right)
            row += 1

            if is_detail:
                for line in dummy[partner['partner_id']]:
                    if line['amount'] != 0:
                        if line['line'].invoice_id:
                            sheet.write_merge(row,row,col, col + 2, line['line'].invoice_id.number, for_center)

                            sheet.write(row, col + 3,
                                        line['line'].invoice_id.partner_shipping_id.name or '',
                                        for_right)


                            # sheet.write(row, col + 3,
                            #             line['line'].invoice_id.user_id.name or '',
                            #             for_right)
                            sheet.write(row, col + 4,
                                        strToDate(line['line'].invoice_id.date_invoice).strftime('%d/%m/%Y') or '',
                                        for_right)
                            if line['line'].invoice_id.date_due:
                                date_due = line['line'].invoice_id.date_due
                            else:
                                date_due = line['line'].invoice_id.date_invoice

                            if line['line'].invoice_id and line['line'].invoice_id.is_extra_no_paid:
                                sheet.write(row, col + 13,'ตั้งค่าเผื่อหนี้สังสัยจะสูญ',for_left)




                            sheet.write(row, col + 5,
                                        strToDate(date_due).strftime('%d/%m/%Y') or '',
                                        for_right)
                        else:
                            sheet.write_merge(row, row, col, col + 2, '',for_right)
                            sheet.write(row, col + 3,'',for_right)
                            sheet.write(row, col + 4,'',for_right)
                            sheet.write(row, col + 5,'',for_right)

                        sheet.write(row, col + 6,
                                    "{0:,.2f}".format(line['intervals'].get('5')) and line['intervals'].get('5') or '',
                                    for_right)
                        sheet.write(row, col + 7,
                                    "{0:,.2f}".format(line['intervals'].get('4')) and line['intervals'].get('4') or '',
                                    for_right)
                        sheet.write(row, col + 8,
                                    "{0:,.2f}".format(line['intervals'].get('3')) and line['intervals'].get('3') or '',
                                    for_right)
                        sheet.write(row, col + 9,
                                    "{0:,.2f}".format(line['intervals'].get('2')) and line['intervals'].get('2') or '',
                                    for_right)
                        sheet.write(row, col + 10,
                                    "{0:,.2f}".format(line['intervals'].get('1')) and line['intervals'].get('1') or '',
                                    for_right)
                        sheet.write(row, col + 11,
                                    "{0:,.2f}".format(line['intervals'].get('0')) and line['intervals'].get('0') or '',
                                    for_right)
                        sheet.write(row, col + 12,
                                    str(line['over_due']) and line['over_due'] or '',
                                    for_right)
                        row += 1
            row += 1



        #-------------------------------------------------------------------------#
        workbook.save(fl)
        fl.seek(0)

        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        self._cr.execute("TRUNCATE aging_partner_export CASCADE")
        wizard_id = self.env['aging.partner.export'].create(
            vals={'name': 'Aging Report.xls', 'report_file': ctx['report_file']})
        # print wizard_id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'aging.partner.export',
            'target': 'new',
            'context': ctx,
            'res_id': wizard_id.id,
        }


class aging_partner_export(models.TransientModel):
    _name = 'aging.partner.export'

    report_file = fields.Binary('File')
    name = fields.Char(string='File Name', size=32)

    @api.multi
    def action_back_export(self):
        if self._context is None:
            self._context = {}
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.aged.trial.balance',
            'target': 'new',
        }
