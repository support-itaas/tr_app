# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from datetime import datetime, timedelta, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove_journalEntry(models.Model):
    _inherit = 'account.move'

    cheque_amount = fields.Float(string="Amount")
    cheque_type = fields.Selection([('paid','เช็คจ่าย'),('receive','เช็ครับ')], string='Cheque type')
    note_text = fields.Text('สมุด')

    def create_cheque(self):
        print('create_cheque')

        if self.cheque_type == 'paid':
            cheque_type = 'pay'
        elif self.cheque_type == 'receive':
            cheque_type = 'rec'

        cheque = self.line_ids.filtered(lambda x: x.account_id.is_cheque == True)
        # print('Cheque:',cheque)
        if self.env['account.cheque.statement'].search([('cheque_number','=',self.cheque_number)],limit=1):
            raise UserError(_("เช็คหมายเลขนี้มีอยู่แล้ว"))

        if not self.cheque_number:
            raise UserError(_("กรุณาใส่รายละเอียดของเช็คก่อนทำรายการ"))
        val = {
            'amount': self.cheque_amount ,
            'partner_id' : self.partner_id.id or '',
            'account_id': cheque and cheque.account_id.id or False,
            'cheque_bank': self.cheque_bank.id or '',
            'cheque_branch': self.cheque_branch or '',
            'cheque_number': self.cheque_number or '',
            'cheque_date': self.cheque_date or '',
            'issue_date': date.today() or '',
            'move_id': self.id or '',
            'type': cheque_type or '',
            'journal_id': self.journal_id.id or ''
        }
        # print('val:',val)
        self.env['account.cheque.statement'].create(val)


