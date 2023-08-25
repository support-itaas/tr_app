# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

class AccountInvoice_inherit(models.Model):
    _inherit = "account.invoice"

    bill_to_id = fields.Many2one('res.partner', string='Bill to')

    @api.multi
    def action_move_create(self):
        print ('update bill to')
        result = super(AccountInvoice_inherit, self).action_move_create()
        for inv in self:
            if inv.move_id and inv.bill_to_id:
                ###########find move line same with account_id that mean it is account receiabale change to bill to
                move_line_account_id = inv.move_id.line_ids.filtered(lambda ml: ml.account_id == inv.account_id)
                if move_line_account_id:
                    ############# Update partner id of ar to bill to but the rest still be normal partner field
                    move_line_account_id.update({'partner_id': inv.bill_to_id.id})


        return result

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice_inherit, self).action_invoice_open()
        self.update_pos_session_to_entry()
        return res

    def update_pos_session_to_entry(self):
        for invoice in self:
            order_id = self.env['pos.order'].search([('name','=',invoice.origin)],limit=1)
            if order_id and order_id.session_id:
                invoice.move_id.update({'ref': order_id.session_id.name})
                invoice.move_id.line_ids.update({'ref': order_id.session_id.name})





class account_payment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        print ('------TR BILL TO----')
        super(account_payment, self).post()

        for payment in self:
            if payment.move_line_ids and payment.invoice_ids and payment.invoice_ids[0].bill_to_id:
                payment.update({'partner_id': payment.invoice_ids[0].bill_to_id.id})
                for move_line in payment.move_line_ids:
                    move_line.update({'partner_id': payment.invoice_ids[0].bill_to_id.id})

