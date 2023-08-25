
import datetime
from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class WizardCoupon(models.Model):
    _inherit = 'wizard.coupon'

    # @api.multi
    # def button_redeem(self, plate_id=None, branch_id=None, order_date=None, car_clean=None, barcode=None):
    #     res = super(WizardCoupon, self).button_redeem(plate_id=plate_id, branch_id=branch_id, order_date=order_date, car_clean=car_clean, barcode=barcode)
    #     self.action_set_pos_session_bom()
    #     return res
    #
    # @api.multi
    # def action_set_pos_session_bom(self):
    #     self.session_id.stock_bom_ids.unlink()
    #
    #     if self.product_id.related_service_id and self.product_id.related_service_id.bom_ids:
    #         bom_line_ids = self.product_id.related_service_id.bom_ids[0].bom_line_ids
    #         print('bom_line_ids :',bom_line_ids)
    #         if self.session_id.stock_bom_ids and bom_line_ids:
    #             for bom in bom_line_ids:
    #                 stock_bom_id = self.session_id.stock_bom_ids.filtered(lambda x: x.product_id == bom.product_id and x.product_uom_id == bom.product_uom_id)
    #                 if stock_bom_id:
    #                     stock_bom_id.update({
    #                         'product_qty': stock_bom_id.product_qty + bom.product_qty,
    #                     })
    #                 else:
    #                     value = {
    #                         'session_id': self.session_id.id,
    #                         'product_id': bom.product_id.id,
    #                         'product_qty': bom.product_qty,
    #                         'product_uom_id': bom.product_uom_id.id,
    #                     }
    #                     self.env['pos.session.bom'].create(value)
    #
    #         else:
    #             for bom in bom_line_ids:
    #                 value = {
    #                     'session_id': self.session_id.id,
    #                     'product_id': bom.product_id.id,
    #                     'product_qty': bom.product_qty,
    #                     'product_uom_id': bom.product_uom_id.id,
    #                 }
    #                 self.env['pos.session.bom'].create(value)
