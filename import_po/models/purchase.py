# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.addons import decimal_precision as dp

class PurchaseOrderLine_inherit(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'
    _order = 'order_id, sequence, id'

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     res = super(PurchaseOrderLine_inherit, self).onchange_product_id()
    #     # print('dfddfddfdf')
    #     # print(res)
    #     result = {}
    #     if not self.product_id:
    #         return result
    #
    #     # Reset date, price and quantity since _onchange_quantity will provide default values
    #     self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #     self.price_unit = self.product_qty = 0.0
    #     self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
    #     result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
    #     # print(self.price_unit)
    #     product_lang = self.product_id.with_context(
    #         lang=self.partner_id.lang,
    #         partner_id=self.partner_id.id,
    #     )
    #     self.name = product_lang.display_name
    #     if product_lang.description_purchase:
    #         self.name += '\n' + product_lang.description_purchase
    #
    #     fpos = self.order_id.fiscal_position_id
    #     if self.env.uid == SUPERUSER_ID:
    #         company_id = self.env.user.company_id.id
    #         self.taxes_id = fpos.map_tax(
    #             self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
    #     else:
    #         self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)
    #
    #     self._suggest_quantity()
    #     self._onchange_quantity()
    #
    #     return result
    #
    # # ----------------------------
    # @api.onchange('product_qty', 'product_uom')
    # def _onchange_quantity(self):
    #     res = super(PurchaseOrderLine_inherit, self)._onchange_quantity()
    #     if not self.product_id:
    #         return
    #
    #     seller = self.product_id._select_seller(
    #         partner_id=self.partner_id,
    #         quantity=self.product_qty,
    #         date=self.order_id.date_order and self.order_id.date_order[:10],
    #         uom_id=self.product_uom)
    #
    #     if seller or not self.date_planned:
    #         self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #
    #     if not seller:
    #         return
    #
    #     # print('seller')
    #     # print(seller)
    #     # HDPH-KW15-002   product.supplierinfo(18522,)
    #     price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.fob_price,
    #                                                                          self.product_id.supplier_taxes_id,
    #                                                                          self.taxes_id,
    #                                                                          self.company_id) if seller else 0.0
    #     if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
    #         price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)
    #
    #     if seller and self.product_uom and seller.product_uom != self.product_uom:
    #         price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
    #
    #     self.price_unit = price_unit