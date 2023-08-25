# -*- coding: utf-8 -*-
import re
from io import BytesIO
import base64
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import xlwt
from xlwt import *
from odoo import fields, api, models
from odoo.tools.translate import _
from odoo.tools.misc import formatLang

class accounting_report(models.TransientModel):

     _inherit="accounting.report"
     xls_theme_id = fields.Many2one('color.xls.theme','XLS Theme')

     @api.multi
     def check_report_xls(self):
            current_obj = self
            data = {}
            data['form'] = self.read(['date_from',  'date_to', 'account_report_id', 'target_move','enable_filter','debit_credit','filter_cmp','date_from_cmp','date_to_cmp'])[0]
            target_move = dict(self.env['accounting.report'].fields_get(allfields=['target_move'])['target_move']['selection'])[current_obj.target_move]
            used_context = self._build_contexts(data)
            comparision_context = self._build_comparison_context(data)
            data['form']['comparison_context'] = dict(comparision_context, lang=self.env.context.get('lang', 'en_US'))
            data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
            account_res = self.env['report.account.report_financial'].get_account_lines(data.get('form'))
            #### From get lines ###
            fp = BytesIO()
            wb = xlwt.Workbook(encoding='utf-8')

            header_style = xlwt.XFStyle()
            font = xlwt.Font()
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            bg_color = current_obj.xls_theme_id.bg_color or 'black'
            pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
            font.height = int(current_obj.xls_theme_id.font_size)
            font.bold = current_obj.xls_theme_id.font_bold
            font.italic = current_obj.xls_theme_id.font_italic
            font_color = current_obj.xls_theme_id.font_color or 'white'
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
            bg_color = current_obj.xls_theme_id.column_bg_color or 'red'
            pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
            font.height = int(current_obj.xls_theme_id.column_font_size)
            font.bold = current_obj.xls_theme_id.column_font_bold
            font.italic = current_obj.xls_theme_id.column_font_italic
            font_color = current_obj.xls_theme_id.column_font_color or 'white'
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
            bg_color = current_obj.xls_theme_id.body_bg_color or 'gold'
            pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
            font.height = int(current_obj.xls_theme_id.body_font_size)
            font.bold = current_obj.xls_theme_id.body_font_bold
            font.italic = current_obj.xls_theme_id.body_font_italic
            font_color = current_obj.xls_theme_id.body_font_color or 'white'
            font.colour_index = xlwt.Style.colour_map[font_color]
            body_header_style.pattern = pattern
            body_header_style.font = font
            al3 = Alignment()
            al3.horz = current_obj.xls_theme_id.body_header_alignment
            body_header_style.alignment = al3

            date_from = self.date_from
            date_to = self.date_to

            final_arr_data = {}

            filename = self.account_report_id.name+'.xls'
            worksheet = wb.add_sheet(current_obj.account_report_id.name + ".xls")
            for i in range(1,10):
              column = worksheet.col(i)
              column.width = 235 * 30
              column = worksheet.col(0)
              column.width = 350 * 30
            if not current_obj.debit_credit and not current_obj.enable_filter:
                worksheet.write_merge(1,1,1,2, current_obj.account_report_id.name, header_style)

                if date_from or date_to:
                        worksheet.write(5, 2,"Date from:"+''+date_from , column_header_style)
                        worksheet.write(6, 2,"Date to:"+''+ date_to , column_header_style)

                worksheet.write(3, 1, "Target Moves:", column_header_style)
                worksheet.write(4, 1, target_move , body_header_style)

                worksheet.write(11, 1, "Name", column_header_style)
                worksheet.write(11, 2, "Balance", column_header_style)

                i=11
                for data in account_res:

                    if data['level'] != 0:
                        worksheet.write(i+1, 1, data['name'], column_header_style)
                        worksheet.write(i+1, 2, formatLang(self.env, data['balance'], currency_obj=current_obj.company_id.currency_id), column_header_style)
                  #  else:
                  #      worksheet.write(i+1, 0, data['name'], body_header_style)
                  #      worksheet.write(i+1, 1, data['balance'], body_header_style)
                    i+=1

            elif current_obj.enable_filter:
                worksheet.write_merge(1,1,1,2, current_obj.account_report_id.name, header_style)

                if date_from or date_to:
                        worksheet.write(5, 2,"Date from:"+''+date_from , column_header_style)
                        worksheet.write(6, 2,"Date to:"+''+ date_to , column_header_style)

                worksheet.write(3, 1, "Target Moves:", column_header_style)
                worksheet.write(4, 1, target_move , body_header_style)
                worksheet.write(11, 1, "Name", column_header_style)
                worksheet.write(11, 2, "Balance", column_header_style)
                worksheet.write(11, 3, current_obj.label_filter, column_header_style)

                i=11
                for data in account_res:
                    if data['level'] !=0:
                        worksheet.write(i+1, 1, data['name'], column_header_style)
                        worksheet.write(i+1, 2, formatLang(self.env, data['balance'], currency_obj=current_obj.company_id.currency_id), column_header_style)
                        worksheet.write(i+1, 3, formatLang(self.env, data['balance'], currency_obj=current_obj.company_id.currency_id), column_header_style)

                    i+=1
            else :
                worksheet.write_merge(1,1,1,2, current_obj.account_report_id.name, header_style)

                if date_from or date_to:
                        worksheet.write(5, 2,"Date from:"+''+date_from , column_header_style)
                        worksheet.write(6, 2,"Date to:"+''+ date_to , column_header_style)
                worksheet.write(3, 1, "Target Moves:", column_header_style)
                worksheet.write(4, 1, target_move , body_header_style)
                worksheet.write(11, 1, "Name", column_header_style)
                worksheet.write(11, 2, "Debit", column_header_style)
                worksheet.write(11, 3, "Credit", column_header_style)
                worksheet.write(11, 4, "Balance", column_header_style)
                i=11
                for data in account_res:
                    if data['level'] !=0 :
                        worksheet.write(i+1, 1, data['name'], body_header_style)
                        worksheet.write(i+1, 2, formatLang(self.env, data['debit'], currency_obj=current_obj.company_id.currency_id), body_header_style)
                        worksheet.write(i+1, 3,formatLang(self.env, data['credit'], currency_obj=current_obj.company_id.currency_id), body_header_style)
                        worksheet.write(i+1, 4, formatLang(self.env, data['balance'], currency_obj=current_obj.company_id.currency_id), body_header_style)


                    i+=1
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

accounting_report()
