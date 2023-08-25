# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from datetime import datetime, date
from odoo.exceptions import UserError


class sale_order(models.Model):

    _inherit = "sale.order"

    auto_generated = fields.Boolean(string='Auto Generated Sales Order', copy=False)
    auto_purchase_order_id = fields.Many2one('purchase.order', string='Source Purchase Order', readonly=True, copy=False)

    @api.multi
    def action_confirm(self):
        """ Generate inter company purchase order based on conditions """
        print('action_confirm inter_company_rules ; ')
        res = super(sale_order, self).action_confirm()
        for order in self:
            if not order.company_id: # if company_id not found, return to normal behavior
                continue
            # if company allow to create a Purchase Order from Sales Order, then do it !
            company = self.env['res.company']._find_company_from_partner(order.partner_id.id)
            if company and company.po_from_so and (not order.auto_generated):
                order.inter_company_create_purchase_order(company)

            # if order.auto_purchase_order_id:
            #     picking_ids = order.picking_ids.filtered(lambda x: x.state not in ['done','cancel'])
            #     for picking in picking_ids:
            #         print("picking:",picking)
            #         print("picking:",picking.location_id.display_name)
            #         print("c:",picking.move_lines)
            #         picking.action_assign()
            #     picking.update({'force_date': picking.scheduled_date})
            #     for move in picking.move_lines:
            #         print('move:', move)
            #         print('reserved_availability:',move.reserved_availability)
            #         print('product_uom_qty:',move.product_uom_qty)
            #         print('quantity_done:', move.quantity_done)
            #         move.update({'quantity_done': move.reserved_availability})
            # picking_ids.sudo().button_validate()

        return res

    @api.one
    def inter_company_create_purchase_order(self, company):
        """ Create a Purchase Order from the current SO (self)
            Note : In this method, reading the current SO is done as sudo, and the creation of the derived
            PO as intercompany_user, minimizing the access right required for the trigger user
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id, company_id=company.id)
        PurchaseOrder = self.env['purchase.order']
        company_partner = self.company_id and self.company_id.partner_id or False
        if not company or not company_partner.id:
            return

        # find user for creating and validating SO/PO from company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise Warning(_('Provide one user for intercompany relation for % ') % company.name)
        # check intercompany user access rights
        if not PurchaseOrder.sudo(intercompany_uid).check_access_rights('create', raise_exception=False):
            raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

        # create the PO and generate its lines from the SO
        PurchaseOrderLine = self.env['purchase.order.line']
        # read it as sudo, because inter-compagny user can not have the access right on PO
        po_vals = self.sudo()._prepare_purchase_order_data(company, company_partner)
        purchase_order = PurchaseOrder.sudo(intercompany_uid).create(po_vals[0])
        for line in self.order_line.sudo():
            po_line_vals = self._prepare_purchase_order_line_data(line, self.date_order, purchase_order.id, company)
            PurchaseOrderLine.sudo(intercompany_uid).create(po_line_vals)

        # write customer reference field on SO
        if not self.client_order_ref:
            self.client_order_ref = purchase_order.name

        # auto-validate the purchase order if needed
        if company.auto_validation:
            purchase_order.sudo(intercompany_uid).button_confirm()

    @api.one
    def _prepare_purchase_order_data(self, company, company_partner):
        """ Generate purchase order values, from the SO (self)
            :param company_partner : the partner representing the company of the SO
            :rtype company_partner : res.partner record
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # find location and warehouse, pick warehouse from company object
        PurchaseOrder = self.env['purchase.order']
        warehouse = company.warehouse_id and company.warehouse_id.company_id.id == company.id and company.warehouse_id or False
        if not warehouse:
            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))

        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'), ('warehouse_id', '=', warehouse.id)
        ], limit=1)
        if not picking_type_id:
            intercompany_uid = company.intercompany_user_id.id
            picking_type_id = PurchaseOrder.sudo(intercompany_uid)._default_picking_type()
        res = {
            'name': self.env['ir.sequence'].sudo().next_by_code('purchase.order'),
            'origin': self.name,
            'partner_id': company_partner.id,
            'picking_type_id': picking_type_id.id,
            'date_order': self.date_order,
            'company_id': company.id,
            'fiscal_position_id': company_partner.property_account_position_id.id,
            'payment_term_id': company_partner.property_supplier_payment_term_id.id,
            'auto_generated': True,
            'auto_sale_order_id': self.id,
            'partner_ref': self.name,
            'currency_id': self.currency_id.id
        }
        return res

    @api.model
    def _prepare_purchase_order_line_data(self, so_line, date_order, purchase_id, company):
        """ Generate purchase order line values, from the SO line
            :param so_line : origin SO line
            :rtype so_line : sale.order.line record
            :param date_order : the date of the orgin SO
            :param purchase_id : the id of the purchase order
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # price on PO so_line should be so_line - discount
        price = so_line.price_unit - (so_line.price_unit * (so_line.discount / 100))

        # computing Default taxes of so_line. It may not affect because of parallel company relation
        taxes = so_line.tax_id
        if so_line.product_id:
            taxes = so_line.product_id.supplier_taxes_id

        # fetch taxes by company not by inter-company user
        company_taxes = taxes.filtered(lambda t: t.company_id == company)
        if purchase_id:
            po = self.env["purchase.order"].sudo(company.intercompany_user_id).browse(purchase_id)
            company_taxes = po.fiscal_position_id.map_tax(company_taxes, so_line.product_id, po.partner_id)

        quantity = so_line.product_id and so_line.product_uom._compute_quantity(so_line.product_uom_qty, so_line.product_id.uom_po_id) or so_line.product_uom_qty
        price = so_line.product_id and so_line.product_uom._compute_price(price, so_line.product_id.uom_po_id) or price
        return {
            'name': so_line.name,
            'order_id': purchase_id,
            'product_qty': quantity,
            'product_id': so_line.product_id and so_line.product_id.id or False,
            'product_uom': so_line.product_id and so_line.product_id.uom_po_id.id or so_line.product_uom.id,
            'price_unit': price or 0.0,
            'company_id': company.id,
            'date_planned': so_line.order_id.commitment_date or date_order,
            'taxes_id': [(6, 0, company_taxes.ids)],
        }


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_done(self):
        res = super(StockPicking, self).action_done()
        # print('self.sale_id.auto_purchase_order_id', self.sale_id.sudo().auto_purchase_order_id.name)
        # print('selffffL',self)
        if self.sale_id.sudo().auto_purchase_order_id:
            picking_ids = self.sale_id.sudo().auto_purchase_order_id.picking_ids.filtered(lambda x: x.state not in ['done','cancel'])
            # print('picking_ids ',picking_ids)

            for picking in picking_ids:
                # print("picking_name:",picking.name)
                # print("picking_location:",picking.location_id.display_name)
                # print("picking_move_lines:",picking.move_lines)
                for move in picking.move_lines:
                    so_move_line = self.move_line_ids.filtered(lambda x: x.product_id == move.product_id)
                    move.move_line_ids.unlink()
                    for so_ml in so_move_line:
                        val = {'product_id': so_ml.product_id.id,
                               'lot_id': so_ml.lot_id.id or False,
                               'qty_done': so_ml.qty_done,
                               'move_id': move.id,
                               'location_id': move.picking_id.location_id.id,
                               'location_dest_id': move.picking_id.location_dest_id.id,
                               'picking_id': move.picking_id.id,
                               'product_uom_id': so_ml.product_id.uom_id.id,
                               }
                        print('move_line_ids val ',val)
                        self.env['stock.move.line'].sudo().create(val)

                check_quantity = True
                picking.sudo().action_assign()
                picking.update({'force_date': picking.scheduled_date})
                for move in picking.move_lines:
                    print('move:', move)
                    print('reserved_availability:',move.reserved_availability)
                    print('product_uom_qty:',move.product_uom_qty)
                    print('quantity_done:', move.quantity_done)
                    if move.product_uom_qty != move.reserved_availability:
                        check_quantity = False
                    print('check_quantity:', check_quantity)
                    print('picking button_validate')
                    # for move_line in move.move_line_ids:
                    #     line = self.move_line_ids.filtered(lambda x: x.product_id == move.product_id)
                    #     # print('gggggggg:',line.lot_id.name)
                    #     move_line.update({
                    #         'lot_id':line.lot_id.id,
                    #         'qty_done':line.qty_done
                    #     })
                    # print('move_line:',move_line.location_dest_id.name)

                if check_quantity:
                    # move.update({'quantity_done': move.reserved_availability})
                    picking.sudo().create_evaluation_in_vendors()
                    picking.sudo().button_validate()

        # print('end action_done')
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    def _quantity_done_set(self):
        quantity_done = self[0].quantity_done  # any call to create will invalidate `move.quantity_done`
        for move in self:
            move_lines = move._get_move_lines()
            if not move_lines:
                if quantity_done:
                    # do not impact reservation here
                    move_line = self.env['stock.move.line'].create(dict(move._prepare_move_line_vals(), qty_done=quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
            elif len(move_lines) == 1:
                move_lines[0].qty_done = quantity_done
            else:
                raise UserError("Cannot set the done quantity from this stock move, work directly with the move lines. [%s] " % (move.picking_id.name))
