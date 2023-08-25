# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models,_
from datetime import datetime,timedelta,date
import dateutil.parser

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class SaleOrder(models.Model):
    _inherit = 'sale.order'







    def _get_order_type(self):
        return self.env['sale.order.type'].search([], limit=1)

    type_id = fields.Many2one(
        comodel_name='sale.order.type', string='Type', default=_get_order_type)

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        sale_type = (self.partner_id.sale_type or
                     self.partner_id.commercial_partner_id.sale_type)
        if sale_type:
            self.type_id = sale_type

    @api.multi
    @api.onchange('type_id')
    def onchange_type_id(self):
        for order in self:
            if order.type_id.warehouse_id:
                order.warehouse_id = order.type_id.warehouse_id
            if order.type_id.picking_policy:
                order.picking_policy = order.type_id.picking_policy
            if order.type_id.payment_term_id:
                order.payment_term_id = order.type_id.payment_term_id.id
            if order.type_id.pricelist_id:
                order.pricelist_id = order.type_id.pricelist_id.id
            if order.type_id.incoterm_id:
                order.incoterm = order.type_id.incoterm_id.id
            if order.type_id.operating_unit_id:
                order.operating_unit_id = order.type_id.operating_unit_id.id

    @api.multi
    def match_order_type(self):
        order_types = self.env['sale.order.type'].search([])
        for order in self:
            for order_type in order_types:
                if order_type.matches_order(order):
                    order.type_id = order_type
                    order.onchange_type_id()
                    break

    @api.multi
    def _action_confirm(self):
        print('_action_confirm:')
        res = super(SaleOrder, self)._action_confirm()
        print('res;', res)
        self.write({
            'confirmation_date': self.date_order
        })
        return res

    @api.model
    def create(self, vals):
        print('create_ADDAONS')
        # if vals.get('name', _('New')) == _('New'):
        #     if 'company_id' in vals:
        #         vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order') or _('New')
        #     else:
        #         vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        # result = super(SaleOrder, self).create(vals)
        result = super(models.Model, self).create(vals)
        dt = datetime.strptime(result.date_order, '%Y-%m-%d %H:%M:%S')
        dt = dt.date()
        dt = dt.strftime("%Y-%m-%d")
        sale_type = self.env['sale.order.type'].browse(result.type_id.id)
        result.name = sale_type.sequence_id.with_context(ir_sequence_date=dt).next_by_id()
        return result


    # @api.model
    # def create(self, vals):
    #     res = super(SaleOrder, self).create(vals)
    #     print('xxxxxxxxxxxxxxxxxxxxx create')
    #     if vals.get('name', '/') == 'NEW'and vals.get('type_id'):
    #         sale_type = self.env['sale.order.type'].browse(vals['type_id'])
    #         if sale_type.sequence_id:
    #             print('ssssssssss:',self.date_order)
    #             vals['name'] = sale_type.sequence_id.with_context(ir_sequence_date=self.date_order).next_by_id()
    #     return res

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.type_id.journal_id:
            res['journal_id'] = self.type_id.journal_id.id
        if self.type_id:
            res['sale_type_id'] = self.type_id.id
        return res
