# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
from datetime import datetime, date

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Refund
    'in_refund': 'in_invoice',          # Vendor Refund
}

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # allow_cancel = fields.Boolean(string='Allow Cancel',related='company_id.allow_cancel')
    allow_cancel = fields.Boolean(string='Allow Cancel',
                                  default=lambda self: self.env.user.company_id.allow_cancel)

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        adj_moves = self.env['account.move']

        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.adjust_move_id:
                adj_moves += inv.adjust_move_id
            if inv.payment_move_line_ids:
                raise UserError(_(
                    'You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

            # if inv.tax_inv_generated:
            #     raise UserError(_(
            #         'You cannot cancel an invoice which is tax invoice generated. You need to cancel tax invoice first.'))

        # First, set the invoices as cancelled and detach the move ids

        number = self.number
        tax_inv_no = self.tax_inv_no
        self.write({'state': 'cancel', 'move_id': False, })
        self.write({'number': number})
        self.write({'tax_inv_no': tax_inv_no})

        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        if adj_moves:
            adj_moves.button_cancel()

        return True

    @api.multi
    def tax_invoice_cancel(self):
        moves = self.env['account.move']
        adj_moves = self.env['account.move']

        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.adjust_move_id:
                adj_moves += inv.adjust_move_id
            if inv.payment_move_line_ids:
                raise UserError(_(
                'You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled and detach the move ids

        tax_inv_no = self.tax_inv_no
        self.write({'tax_inv_no': tax_inv_no})
        self.write({'tax_inv_generated': False})
        self.write({'tax_inv_date':False})
        if adj_moves:
            adj_moves.reverse_moves(datetime.now(), adj_moves.journal_id or False)
        self.write({'adjust_move_id': False})

        return True
