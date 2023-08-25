# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    order_type = fields.Many2one('purchase.order.type', string="Purchase Order Type",required=True)
    po_return = fields.Boolean('Return PO', related='order_type.po_return', store=True)

    @api.onchange('partner_id')
    def onchange_partner_id_purchase_order_type(self):
        if self.partner_id.purchase_type:
            self.order_type = self.partner_id.purchase_type.id

    @api.onchange('order_type')
    def onchange_purchase_order_type(self):
        if self.order_type:
            if self.order_type.incoterm_id:
                self.incoterm_id = self.order_type.incoterm_id.id
            if self.order_type.picking_type_id:
                self.picking_type_id = self.order_type.picking_type_id.id




    @api.multi
    @api.constrains('po_return', 'partner_id')
    def _check_return_order(self):
        for po in self:
            if po.po_return == True and po.partner_id.customer == False:
                raise UserError(_("in return PO, vendor has to be set as customer also"))
        return True

    @api.multi
    @api.constrains('order_line.price_unit', 'order_line.po_return_line')
    def _check_return_order2(self):
        for line in self.order_line:
            if line.po_return_line == True and not line.price_unit == 0.0:
                raise UserError(_("in return PO, price has to be zero"))
        return True

    @api.multi
    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        if self.order_type.vendor_bill_journal_id:
            if not self.invoice_ids:
                default_journal_id = self.order_type.vendor_bill_journal_id.id
                if default_journal_id:
                    res['context']['default_journal_id'] = default_journal_id
        return res

    @api.model
    def create(self, vals):
        print('vvvvvvvvvvvvvvvvv',vals)
        # ref = vals.get('order_type', 'purchase_sequence_id')
        # print ('CREATE PURCHASE ORDER--')
        # print (vals)
        ref = False
        if vals.get('order_type'):
            ref = vals.get('order_type')
        elif vals.get('origin'):
            order_point_origin = vals['origin']
            print (order_point_origin)
            order_point = order_point_origin.split(',')
            print (order_point)
            if order_point:
                order_point_id = self.env['stock.warehouse.orderpoint'].search([('name','=',order_point[0])],limit=1)
                if order_point_id:
                    print ('order_point_id',order_point_id)
                    print ('order_point_id.order_type.id',order_point_id.order_type)
                    ref = order_point_id.order_type.id
                    vals['order_type'] = order_point_id.order_type.id
                    vals['purchase_type'] = order_point_id.purchase_type.id

        if ref:
            print ('-REF-')
            print (ref)
            order_type_id = self.env['purchase.order.type'].browse(ref)
            print('order_type_id ',order_type_id)
            date_order = str(vals.get('date_order')).split(' ')
            if order_type_id.purchase_sequence_id and not vals.get('date_order'):
                se_code = order_type_id.purchase_sequence_id.code
                print('1 se_code ',se_code)
                if vals.get('name', 'New') == 'New':
                    vals['name'] = order_type_id.purchase_sequence_id.next_by_id() or '/'
            elif vals.get('date_order'):
                if vals.get('name', 'New') == 'New':
                    vals['name'] = order_type_id.purchase_sequence_id.with_context(ir_sequence_date=date_order[0]).next_by_id() or '/'
                    # vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
            else:
                raise UserError(_('You don\'t  sequence. And try again.'))
                # if vals.get('name', 'New') == 'New':
                #     vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
        else:
            print ('---NO ORDER TYPE--')
        print('vals ',vals)
        return super(PurchaseOrder, self).create(vals)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    po_return_line = fields.Boolean('Return PO', related='order_id.order_type.po_return', store=True)

    @api.multi
    @api.constrains('price_unit', 'po_return_line')
    def _check_return_order_line(self):
        for record in self:
            if record.po_return_line == True and not record.price_unit == 0.0:
                raise UserError(_("in return PO, price has to be zero"))
        return True
