# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo
import logging
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class pos_order(models.Model):
    _inherit = "pos.order"

    voucher_id = fields.Many2one('pos.voucher', 'Voucher')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(pos_order, self)._order_fields(ui_order)
        if ui_order.get('voucher_id', False):
            order_fields.update({
                'voucher_id': ui_order['voucher_id']
            })
        return order_fields

    @api.model
    def get_code(self, code):
        return self.env['barcode.nomenclature'].sudo().sanitize_ean(code)

    def _payment_fields(self, ui_paymentline):
        payment_fields = super(pos_order, self)._payment_fields(ui_paymentline)
        if ui_paymentline.get('voucher_id', None):
            payment_fields['voucher_id'] = ui_paymentline.get('voucher_id')
        return payment_fields

    def _prepare_bank_statement_line_payment_values(self, data):
        datas = super(pos_order, self)._prepare_bank_statement_line_payment_values(data)
        if data.get('voucher_id', None):
            datas['voucher_id'] = data['voucher_id']
        return datas


class pos_order_line(models.Model):
    _inherit = "pos.order.line"

    @api.model
    def create(self, vals):
        po_line = super(pos_order_line, self).create(vals)
        if po_line.product_id and po_line.product_id.is_voucher:
            voucher = self.env['pos.voucher'].create({
                'customer_id': po_line.order_id.partner_id.id if po_line.order_id.partner_id else None,
                'apply_type': 'fixed_amount',
                'method': 'general',
                'user_id': self.env.user.id,
                'source': po_line.order_id.name,
                'pos_order_line_id': po_line.id,
                'start_date': fields.Datetime.now(),
                'end_date': datetime.today() + timedelta(days=po_line.order_id.config_id.expired_days_voucher),
                'product_id': po_line.product_id.id,
                'value': po_line.price_subtotal_incl,
            })
            format_code = "%s%s%s" % ('999', voucher.id, datetime.now().strftime("%d%m%y%H%M"))
            code = self.env['barcode.nomenclature'].sanitize_ean(format_code)
            voucher.write({'code': code})
            _logger.info('cashier created new voucher id: %s' % voucher.id)
        return po_line
