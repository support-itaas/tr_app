# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError

class PurchaseRequestLineMakePurchaseOrderItem(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order.item"

    keep_unit_price = fields.Boolean(string='Copy Unit Price',default=True,)

class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    date_order = fields.Datetime('Order Date', required=True, default=fields.Datetime.now, \
                                 help="Depicts the date where the Quotation should be validated and converted into a purchase order.")


