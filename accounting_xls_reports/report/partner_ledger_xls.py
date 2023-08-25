# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.tools.translate import _
import base64
from io import BytesIO
import datetime
import xlwt
from xlwt import *
from odoo.tools.misc import formatLang

class account_report_partner_ledger(models.TransientModel):
    _inherit = 'account.report.partner.ledger'

    xls_theme_id = fields.Many2one('color.xls.theme','XLS Theme')
    partner_ids = fields.Many2many('res.partner', 'partner_ledger_partner_rel', 'id', 'partner_id', string='Partners')

    @api.multi
    def print_xls_report(self):


          style1 = xlwt.easyxf("font: bold on,height 250;align: horiz center; pattern: pattern solid, fore_colour white;")
          style2 = xlwt.easyxf("font: bold on,height 220;align: horiz left; pattern: pattern solid, fore_colour white;")
          style3 = xlwt.easyxf("font: bold off;align: horiz left; pattern: pattern solid, fore_colour white;")
          style4= xlwt.easyxf("font: bold on,height 220;align: horiz right; pattern: pattern solid, fore_colour white;")
          style5 = xlwt.easyxf("font: bold off;align: horiz right; pattern: pattern solid, fore_colour white;")

          workbook = xlwt.Workbook(encoding="utf-8")
          wb = workbook.add_sheet('Partner Ledger Report')
          filename = "Partner ledger.xls"
          wiz_obj = self
          current_obj = self

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

          data = {}
          data['computed'] = {}
          data['form'] = self.read(['target_move','result_selection','reconciled','date_from','date_to','journal_ids','partner_ids'])[0]
          used_context = self._build_contexts(data)
          data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))

          obj_partner = self.env['res.partner']
          query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
          data['computed']['move_state'] = ['draft', 'posted']
          if data['form'].get('target_move', 'all') == 'posted':
              data['computed']['move_state'] = ['posted']
          result_selection = data['form'].get('result_selection', 'customer')
          if result_selection == 'supplier':
              data['computed']['ACCOUNT_TYPE'] = ['payable']
          elif result_selection == 'customer':
              data['computed']['ACCOUNT_TYPE'] = ['receivable']
          else:
              data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

          if result_selection == 'supplier':
              self.env.cr.execute("""
                SELECT a.id
                FROM account_account a
                WHERE a.code = '22-01-01-01' and a.internal_type IN %s
                AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
          else:
              self.env.cr.execute("""
                              SELECT a.id
                              FROM account_account a
                              WHERE a.code = '12-01-01-01' and a.internal_type IN %s
                              AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))

          data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
          print ('accccoooo-ids',data['computed']['account_ids'])
          if data['form'].get('partner_ids'):
              print ('partner',data['form'].get('partner_ids'))
              partner_ids = data['form'].get('partner_ids')
          else:
              params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
              reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '
              query = """
                SELECT DISTINCT "account_move_line".partner_id
                FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
                WHERE "account_move_line".partner_id IS NOT NULL
                    AND "account_move_line".account_id = account.id
                    AND am.id = "account_move_line".move_id
                    AND am.state IN %s
                    AND "account_move_line".account_id IN %s
                    AND NOT account.deprecated
                    AND """ + query_get_data[1]

              # print ('query---',query)
              # print('params---', params)
              self.env.cr.execute(query, tuple(params))
              # test = self.env.cr.dictfetchall()
              # print ('Test resul---',test)
              # partner_ids = []
              # all = self.env.cr.dictfetchall()
              # print ('Allll---',all)
              # for res in all:
              #     partner_ids.append(res['partner_id'])
              #
              partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
              print('partner_ids',partner_ids)

          partners = obj_partner.browse(partner_ids)
          # partners = sorted(partners, key=lambda x: (x.ref, x.name))
          partners = sorted(partners, key=lambda x: (x.name))

          #-------------------------------------------------------------------------
          #                         HEADER In Excelself.cr.execute(

          #-------------------------------------------------------------------------
          #wiz_obj = self.browse(cr,uid,ids)[0]
          target = {
                  'posted':"All Posted Entries",
                  'all':"All Entries",
                  'draft':"All UnPosted Entries"
                  }

          Journals = ''
          journal_ids = []

          for journal in wiz_obj.journal_ids:

              Journals = Journals + journal.code + ','

              journal_ids.append(journal.id)
          wb.write_merge(0,0,2,5,"Partner Ledger Report",header_style)
          wb.write_merge(2,2,2,2,'Company',column_header_style)
          #wb.write_merge(2,2,3,3,header,style2)
          if wiz_obj.date_from:
              wb.write_merge(2,2,3,3, "Start Date:"+ wiz_obj.date_from,column_header_style)
          if wiz_obj.date_to:
              wb.write_merge(3,3,3,3, "End Date:"+ wiz_obj.date_to,body_header_style)
          wb.write_merge(2,2,4,4,'Target Moves',column_header_style)
          wb.write_merge(3,3,2,2, self.company_id.name or " ",body_header_style)
          wb.write_merge(3,3,4,4,target[wiz_obj.target_move] or " ",body_header_style)

          if wiz_obj.result_selection == 'customer':
              ACCOUNT_TYPE = ['receivable']
          else:
              ACCOUNT_TYPE = ['payable']




          columns = ['Date','Journal','Account','Entry Label','Debit','Credit','Balance']
          k = 1
          for i in columns:
              wb.write_merge(5,6,k,k,i,column_header_style)
              first_col = wb.col(k)
              first_col.width = 235 * 30
              k = k+1


          i= 7
          for record in partners:
             i=i+1
             wb.write_merge(i,i,1,1,str(record.ref or '')+'-'+str(record.name),column_header_style)
             wb.write_merge(i,i,5,5,formatLang(self.env, self.env['report.account.report_partnerledger']._sum_partner(data, record, 'debit')),column_header_style)
             wb.write_merge(i,i,6,6,formatLang(self.env, self.env['report.account.report_partnerledger']._sum_partner(data, record, 'credit')),column_header_style)
             wb.write_merge(i,i,7,7,formatLang(self.env, self.env['report.account.report_partnerledger']._sum_partner(data, record, 'debit - credit')),column_header_style)
             i=i+1
             for line in self.env['report.account.report_partnerledger']._lines(data,record):

                wb.write_merge(i,i,1,1,line['date'] or " ",body_header_style)
                wb.write_merge(i,i,5,5,formatLang(self.env, line['debit']),body_header_style)
                wb.write_merge(i,i,6,6,formatLang(self.env, line['credit']),body_header_style)
                wb.write_merge(i,i,7,7,formatLang(self.env, line['progress']),body_header_style)

                wb.write_merge(i,i,2,2,line['code'] or " ",body_header_style)
                wb.write_merge(i,i,3,3,line['a_code'] or " ",body_header_style)
                wb.write_merge(i,i,4,4,line['displayed_name'] or " ",body_header_style)


                i= i+1
          fp = BytesIO()
          workbook.save(fp)
          out = base64.encodestring(fp.getvalue())
          final_arr_data = {}
          final_arr_data['file_stream'] = out
          final_arr_data['name'] = filename
          pl_report_id=self.env['account.report.view'].create(final_arr_data)

          return {
            'res_id'   : pl_report_id.id,
            'name'     : filename,
            'view_mode': 'form',
            'res_model': 'account.report.view',
            'type'     :'ir.actions.act_window',
            }
