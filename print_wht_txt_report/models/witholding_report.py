# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

import base64
import xlwt
from io import StringIO

from datetime import datetime,date
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp.tools import misc

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))


# this is for tax report section
class PND53_Report(models.TransientModel):
    _inherit = 'pnd53.report'

    @api.multi
    def get_bank_report(self):
        print('get_bank_report')
        context = dict(self._context or {})
        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '#,###.00'
        cr, uid, context = self.env.args
        final_text = ""
        final_text_body = ""

        # PND 3 -----------------------------------------
        if self.report_type == 'personal':
            move_line_ids = self.env['account.move.line'].search(
                [('date_maturity', '>=', self.date_from), ('date_maturity', '<=', self.date_to),
                 ('wht_personal_company', '=', 'personal'), ('wht_type', '!=', False),
                 ('account_id.wht', '=', True)
                 ], order='date_maturity,wht_reference ASC')
            print('personal')
            print('move_line_ids:',move_line_ids)
            move_ids = ""
            inv_row = 1

            # ลำดับ|เลประจำตัวผู้เสียภาษีอากร|สาขา|คำนำหน้าชื่อ|ชื่อสกุล|ที่อยู่|วันเดือนปี|ประเภทเงินได้|อัตราภาษี|จำนวนเงินที่จ่าย|เงื่อนไขการหักภาษี
            for move in move_line_ids:
                move_ids += str(inv_row) + '|'
                if move.partner_id.vat:
                    move_ids += str(move.partner_id.vat[0:13]) + '|'
                else:
                    move_ids += '|'
                # move_ids += str(move.partner_id.branch_no[0:5] or '') + '|'

                # title_name = move.partner_id.title.name or ''
                # first_name = move.partner_id.name or ''
                # last_name = move.partner_id.last_name or ''
                #
                # move_ids += str(title_name[0:40]) + '|'
                # move_ids += str(first_name[0:100]) + '|' + str(last_name[0:80])


                move_ids += str(move.partner_id.title.name)[0:40] + '|'


                name_temp = move.partner_id.name.split(' ')
                first_name = ""
                last_name = ""
                if len(name_temp) > 1:
                    first_name = name_temp[0]
                    last_name = name_temp[1:]
                    last_name = ' '.join(last_name)

                else:
                    first_name = name_temp[0:]
                    last_name = ''
                    first_name = ' '.join(first_name)
                # last_name = ' '.join(last_name)
                print('first_name:',first_name)
                print('last_name:',last_name)
                move_ids += str(first_name)[0:100] + '|'
                move_ids += str(last_name)[0:80] + '|'

                partner_street = ""
                if move.partner_id.street:
                    partner_street += move.partner_id.street

                if move.partner_id.street2:
                    partner_street += move.partner_id.street2
                move_ids += partner_street[0:30] + '|'

                if move.partner_id.sub_district_id:
                    move_ids += move.partner_id.sub_district_id.name[0:30] + '|'
                else:
                    move_ids += '|'


                if move.partner_id.district_id:
                    move_ids += move.partner_id.district_id.name[0:30] + '|'
                else:
                    move_ids += '|'

                if move.partner_id.state_id:
                    move_ids += move.partner_id.state_id.name[0:40] + '|'
                else:
                    move_ids += '|'

                if move.partner_id.zip:
                    move_ids += move.partner_id.zip[0:5] + '|'
                else:
                    move_ids += '|'

                if move.date_maturity:
                    date_payment_text = datetime.strptime(move.date_maturity, "%Y-%m-%d").strftime('%d/%m/%Y')
                    date_payment_text = date_payment_text.split('/')
                    date = datetime.strptime(move.date_maturity, "%Y-%m-%d").date()
                    date_payment = date_payment_text[0] +'/'+ date_payment_text[1] + '/'+ str(date.year+543)

                if date_payment:
                    move_ids += date_payment + '|'
                else:
                    move_ids += '|'

                move_ids += str(move.name[0:200]) + '|'

                if move.wht_type:
                    wht_type_s = move.wht_type.split('%')
                    wht_type = '%.2f' % float(wht_type_s[0])

                    move_ids += str(wht_type) + '|'

                move_ids += '%.2f' % float(move.amount_before_tax) + '|'
                move_ids += '%.2f' % float(move.credit) + '|'

                if inv_row != len(move_line_ids):
                    move_ids += '1' + "\r\n"
                else:
                    move_ids += '1'

                final_text = final_text_body + str(move_ids)
                # print('final_text : ',final_text)
                inv_row += 1

        # PND 53 ----------------------------------------
        elif self.report_type == 'company':

            # worksheet = workbook.add_sheet('report')
            # worksheet_detail = workbook.add_sheet('report_detail')

            move_line_ids = self.env['account.move.line'].search(
                [('date_maturity', '>=', self.date_from), ('date_maturity', '<=', self.date_to),
                 ('wht_personal_company', '=', 'company'), ('wht_type', '!=', False),('account_id.wht', '=', True)], order='date_maturity,wht_reference ASC')
            print('company')
            print('move_line_ids:',move_line_ids)
            move_ids = ""
            inv_row = 1
            for move in move_line_ids:
                move_ids += str(inv_row) + '|'
                if move.partner_id.vat:
                    move_ids += str(move.partner_id.vat[0:13]) + '|'
                else:
                    move_ids += '|'

                move_ids += str(move.partner_id.branch_no[0:5] or '') + '|'

                #1
                # title_name = move.partner_id.title or ''
                # first_name = move.partner_id.name or ''
                #
                # move_ids += str(title_name[0:40]) + '|'
                # partner_name = str(first_name)
                # move_ids += partner_name[0:160] + '|'

                # 2
                #บริษัท ฟอลคอนอินดัสทรี่ จำกัด 3
                #บริษัท|ฟอลคอนอินดัสทรี่ จำกัด
                name_temp = move.partner_id.name.split(' ')
                if len(name_temp) > 1:
                    title_name = name_temp[0]
                    first_name = name_temp[1:]
                else:
                    title_name = ""
                    first_name = name_temp[0:]

                first_name = ' '.join(first_name)

                move_ids += str(title_name)[0:40] + '|'
                move_ids += str(first_name)[0:160] + '|'

                partner_street = ""
                if move.partner_id.street:
                    partner_street += move.partner_id.street

                if move.partner_id.street2:
                    partner_street += move.partner_id.street2
                move_ids += partner_street[0:30] + '|'

                if move.partner_id.sub_district_id:
                    move_ids += move.partner_id.sub_district_id.name[0:30] + '|'
                else:
                    move_ids += '|'

                if move.partner_id.district_id:
                    move_ids += move.partner_id.district_id.name[0:30] + '|'
                else:
                    move_ids += '|'

                if move.partner_id.state_id:
                    move_ids += move.partner_id.state_id.name[0:40] + '|'
                else:
                    move_ids += '|'

                if move.partner_id.zip:
                    move_ids += move.partner_id.zip[0:5] + '|'
                else:
                    move_ids += '|'


                if move.date_maturity:
                    date_payment_text = datetime.strptime(move.date_maturity, "%Y-%m-%d").strftime('%d/%m/%Y')
                    date_payment_text = date_payment_text.split('/')
                    date = datetime.strptime(move.date_maturity, "%Y-%m-%d").date()
                    date_payment = date_payment_text[0] + '/' + date_payment_text[1] + '/' + str(date.year + 543)

                if date_payment:
                    move_ids += date_payment + '|'
                else:
                    move_ids += '|'

                if move.name:
                    move_ids += str(move.name[0:200]) + '|'


                if move.wht_type:
                    wht_type_s = move.wht_type.split('%')
                    wht_type =  '%.2f' %float(wht_type_s[0])

                    move_ids += str(wht_type) + '|'


                move_ids += '%.2f' %float(move.amount_before_tax) + '|'
                move_ids += '%.2f' %float(move.credit) + '|'

                if inv_row != len(move_line_ids):
                    move_ids += '1' + "\r\n"
                else:
                    move_ids += '1'

                final_text = final_text_body + str(move_ids)

                inv_row += 1
        else:
            raise UserError(_('There is record this date range.'))
        print('final_text:',final_text)
        values = {
            'name': "Witholding Report",
            'datas_fname': 'witholding_report.txt',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.b64encode((final_text).encode("utf-8")),
        }
        attachment_id = self.env['ir.attachment'].sudo().create(values)
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }

    def get_partner_full_address_text(self, partner_id):
        address = []
        if partner_id.country_id.code == 'TH':
            if partner_id.street:
                address.append(str(partner_id.street))
            if partner_id.street2:
                address.append(str(partner_id.street2))

            if partner_id.state_id and partner_id.state_id.code == 'BKK':
                if partner_id.sub_district_id:
                    address.append('แขวง' + str(partner_id.sub_district_id.name))
                if partner_id.district_id:
                    address.append('เขต' + str(partner_id.district_id.name))
                elif partner_id.city:
                    address.append('เขต' + str(partner_id.city))

                if partner_id.state_id:
                    address.append(str(partner_id.state_id.name))
            else:
                if partner_id.sub_district_id:
                    address.append('ต.' + str(partner_id.sub_district_id.name))

                if partner_id.district_id:
                    address.append('อ.' + str(partner_id.district_id.name))
                elif partner_id.city:
                    address.append('อ.' + str(partner_id.city))

                if partner_id.state_id:
                    address.append('จ.' + str(partner_id.state_id.name))
        else:

            if partner_id.street:
                address.append(str(partner_id.street))
            if partner_id.street2:
                address.append(str(partner_id.street2))
            if partner_id.city:
                address.append(str(partner_id.city))
            if partner_id.state_id:
                address.append(str(partner_id.state_id.name))

        if partner_id.zip:
            address.append(str(partner_id.zip))
        # print('get_partner_full_address_text address : ',address)
        return address
