# -*- coding: utf-8 -*-
from unittest import result

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, AccessError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

# from odoo.fields import FailedValue
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, relativedelta, pytz, float_compare


class dealer_purchase_order(models.Model):
    _inherit = 'dealer.purchase.order'

    @api.multi
    def get_spare_part(self):
        print('aaaaaaaaaaaaaaaaa')
        self.item_ids.sudo().unlink()
        product_ids = self.env['product.product'].search([('is_dealer_order_available_get', '=', True)])

        for product in product_ids:
            val = {
                'product_id': product.id,
                'product_qty': 0,
                'product_uom_id': product.uom_id.id,
                'dealer_order_id': self.id,
            }
            self.env['dealer.purchase.order.line'].create(val)

    # @api.multi
    # def get_spare_part(self):
    #     print('get_spare_part')
    #     dealer_po_lines = self.item_ids.filtered(lambda m: m.product_id.is_dealer_order_available_get)
    #     if dealer_po_lines:
    #         val = {
    #             'branch_id': self.branch_id.id,
    #             'order_type': self.order_type.id,
    #             'purchase_order_id': self.purchase_order_id.id,
    #             'purchase_type': self.purchase_type.id,
    #         }
    #         dealer_po_id = self.env['dealer.purchase.order'].create(val)
    #         dealer_ids_done = self.env['dealer.purchase.order.line'].browse()
    #         for line in dealer_po_lines:
    #             print('==============')
    #             val_move = {
    #                 # 'dealer_po_id': dealer_po_id.id,
    #                 'dealer_order_id': dealer_po_id.id,
    #                 'product_id': line.product_id.id,
    #                 'product_qty': line.product_qty,
    #                 'product_uom_id': line.product_uom_id.id,
    #             }
    #             print('val_move :', val_move)
    #             dealer_id = self.env['dealer.purchase.order.line'].create(val_move)
    #             dealer_ids_done += dealer_id
    #
    #         dealer_ids_done._action_confirm()
    #

