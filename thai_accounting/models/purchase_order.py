#-*- coding: utf-8 -*-


from odoo import api, fields, models, _
from datetime import datetime, date
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
from datetime import datetime, timedelta

class purchase_order(models.Model):
    _inherit = "purchase.order"

    contact_person = fields.Many2one('res.partner', string="Contact Person")
    validate_uid = fields.Many2one('res.users', string="Authorized Person")
    validate_date = fields.Date(string="Validated Date")
    request_uid = fields.Many2one('res.users', string="Purchase Request")

    @api.multi
    def button_confirm(self):

        res = super(purchase_order, self).button_confirm()

        for order in self:
            order.write({'request_uid': self.env.user.id})
        return res

    @api.multi
    def button_approve(self):
        self.write({'state': 'purchase','validate_uid': self.env.user.id,'validate_date': date.today()})
        return super(purchase_order, self).button_approve()

    @api.multi
    def button_draft(self):
        self.write({'state': 'draft','validate_uid': False,'validate_date': False})
        return {}


class purchase_order_line(models.Model):
    _inherit = "purchase.order.line"

    discount_amount = fields.Float('Discount (Amount)', default=0.0)
    department_id = fields.Many2one('hr.department', string='แผนก')

    # get total description line
    def get_line(self, data):
        return data.count("\n")

        # option discount amount per unit or price sub total

    @api.depends('product_qty', 'price_unit', 'discount', 'taxes_id', 'discount_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the PO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_amount > 0.0:
                if self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'unit':
                    price -= line.discount_amount
                else:
                    price -= line.discount_amount / line.product_qty

            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })


