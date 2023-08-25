# -*- coding: utf-8 -*-

from openerp import fields, api, models
from openerp.tools.translate import _
from openerp.osv import osv
import xlwt
from xlwt import *
import StringIO
import cStringIO
import base64
import xlrd
import time
from collections import OrderedDict
from openerp.tools.misc import formatLang


class AccountPaperBalanceReport(models.TransientModel):
    _inherit = 'account.paperbalance.report'

    xls_theme_id = fields.Many2one('color.xls.theme', 'XLS Theme')

    @api.multi
    def print_xls_report(self):

        current_obj = self
        display_account = self.display_account
        target_move = self.target_move

        data = {}
        accounts = self.env['account.account'].search([])

        data['form'] = self.read(['date_from', 'date_to', 'target_move'])[0]

        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        account_res = self.env['report.account.report_trialbalance'].with_context(
            data['form'].get('used_context'))._get_accounts(accounts, display_account)
        target_move = \
        dict(self.env['account.balance.report'].fields_get(allfields=['target_move'])['target_move']['selection'])[
            current_obj.target_move]
        display_account = dict(
            self.env['account.balance.report'].fields_get(allfields=['display_account'])['display_account'][
                'selection'])[current_obj.display_account]
        fp = cStringIO.StringIO()
        wb = xlwt.Workbook(encoding='utf-8')

        header_style = xlwt.XFStyle()
        font = xlwt.Font()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        bg_color = current_obj.xls_theme_id.bg_color or 'white'
        pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
        font.height = int(current_obj.xls_theme_id.font_size)
        font.bold = current_obj.xls_theme_id.font_bold
        font.italic = current_obj.xls_theme_id.font_italic
        font_color = current_obj.xls_theme_id.font_color or 'green'
        font.colour_index = xlwt.Style.colour_map[font_color]
        header_style.pattern = pattern
        header_style.font = font
        al3 = Alignment()
        al3.horz = current_obj.xls_theme_id.header_alignment or 0x02
        header_style.alignment = al3

        column_header_style = xlwt.XFStyle()
        font = xlwt.Font()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        bg_color = current_obj.xls_theme_id.column_bg_color or 'white'
        pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
        font.height = int(current_obj.xls_theme_id.column_font_size)
        font.bold = current_obj.xls_theme_id.column_font_bold
        font.italic = current_obj.xls_theme_id.column_font_italic
        font_color = current_obj.xls_theme_id.column_font_color or 'black'
        font.colour_index = xlwt.Style.colour_map[font_color]
        column_header_style.pattern = pattern
        column_header_style.font = font
        al3 = Alignment()
        al3.horz = current_obj.xls_theme_id.column_header_alignment
        column_header_style.alignment = al3

        body_header_style = xlwt.XFStyle()
        font = xlwt.Font()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        bg_color = current_obj.xls_theme_id.body_bg_color or 'white'
        pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
        font.height = int(current_obj.xls_theme_id.body_font_size)
        font.bold = current_obj.xls_theme_id.body_font_bold
        font.italic = current_obj.xls_theme_id.body_font_italic
        font_color = current_obj.xls_theme_id.body_font_color or 'black'
        font.colour_index = xlwt.Style.colour_map[font_color]
        body_header_style.pattern = pattern
        body_header_style.font = font
        al3 = Alignment()
        al3.horz = current_obj.xls_theme_id.body_header_alignment
        body_header_style.alignment = al3

        final_data = {}
        filename = 'Trial Balance.xls'
        worksheet = wb.add_sheet(filename)

        column = worksheet.col(2)
        column.width = 300 * 30
        column = worksheet.col(1)
        column.width = 235 * 30
        column = worksheet.col(0)
        column.width = 235 * 30
        column = worksheet.col(3)
        column.width = 235 * 30
        column = worksheet.col(4)
        column.width = 235 * 30
        column = worksheet.col(5)
        column.width = 235 * 30

        # account_obj = self.pool['account.account'].browse(cr, uid, data['form']['chart_account_id'])
        company_name = self.company_id.name
        header = company_name + ':Trial Balance'
        worksheet.write_merge(0, 0, 0, 8, header, header_style)
        header_list = ['Display Account:', 'Target Moves:']
        header_data_list = OrderedDict({'Display Account:': display_account, 'Target Moves:': target_move})
        row = col = 1
        period_location = []
        for key in header_list:
            worksheet.write(row, col, key, column_header_style)
            row += 1
            worksheet.write(row, col, header_data_list[key], body_header_style)
            row -= 1
            col += 1
        # sending row cursor after 3 new rows
        row += 6
        col = 1
        body_header_list = ['Code', 'Account', 'Debit', 'Credit', 'Balance']
        for header in body_header_list:
            worksheet.write(row, col, header, column_header_style)
            col += 1
        # Getting Body DATA===================================================
        row += 1
        col = 1
        #      final_data = self.get_data(cr, uid, data, context=context)
        #      current_obj = self.browse(cr, uid, ids, context = context)

        for data in account_res:
            #         if data['type'] == "view":
            #            worksheet.write(row, col, data['code'], column_header_style)
            #           col+=1
            #           worksheet.write(row, col, data['name'], column_header_style)
            #           col+=1
            #           worksheet.write(row, col, data['debit'], column_header_style)
            #           col+=1
            #           worksheet.write(row, col, data['credit'], column_header_style)
            #           col+=1
            #           worksheet.write(row, col, data['balance'], column_header_style)
            #
            #      else:

            worksheet.write(row, col, data['code'], body_header_style)
            col += 1
            worksheet.write(row, col, data['name'], body_header_style)
            col += 1
            worksheet.write(row, col,
                            formatLang(self.env, data['debit'], currency_obj=current_obj.company_id.currency_id),
                            body_header_style)
            col += 1
            worksheet.write(row, col,
                            formatLang(self.env, data['credit'], currency_obj=current_obj.company_id.currency_id),
                            body_header_style)
            col += 1
            worksheet.write(row, col,
                            formatLang(self.env, data['balance'], currency_obj=current_obj.company_id.currency_id),
                            body_header_style)
            col = 1
            row += 1
        wb.save(fp)
        out = base64.encodestring(fp.getvalue())
        final_arr_data = {}
        final_arr_data['file_stream'] = out
        final_arr_data['name'] = filename
        create_id = self.env['account.report.view'].create(final_arr_data)
        return {
            'nodestroy': True,
            'res_id': create_id.id,
            'name': filename,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.report.view',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }