# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    voucher_id = fields.Many2one('pos.voucher', 'Voucher', readonly=1)

    @api.model
    def create(self, vals):
        statement_line = super(account_bank_statement_line, self).create(vals)
        if statement_line.voucher_id:
            _logger.info('register payment with voucher code: %s' % statement_line.voucher_id)
            if statement_line.voucher_id.apply_type == 'percent':
                statement_line.voucher_id.write({'state': 'used', 'use_date': fields.Datetime.now()})
                self.env['pos.voucher.use.history'].create({
                    'voucher_id': statement_line.voucher_id.id,
                    'value': statement_line.amount,
                    'used_date': fields.Datetime.now()
                })
            else:
                amount = statement_line.amount
                value = statement_line.voucher_id.value
                _logger.info('voucher value: %s' % value)
                _logger.info('used value: %s' % amount)
                if (value - amount) <= 0:
                    statement_line.voucher_id.write({'state': 'used', 'use_date': fields.Datetime.now()})
                else:
                    statement_line.voucher_id.write({'value': (value - amount)})
                self.env['pos.voucher.use.history'].create({
                    'voucher_id': statement_line.voucher_id.id,
                    'value': statement_line.amount,
                    'used_date': fields.Datetime.now()
                })
        return statement_line
