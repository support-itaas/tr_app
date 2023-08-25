# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class purchase_order(models.Model):

    _inherit = "purchase.order"

    auto_generated = fields.Boolean(string='Auto Generated Purchase Order', copy=False)
    auto_sale_order_id = fields.Many2one('sale.order', string='Source Sales Order', readonly=True, copy=False)

    @api.multi
    def button_approve(self, force=False):
        """ Generate inter company sales order base on conditions."""
        # res = super(purchase_order, self).button_approve(force=force)
        res = super(purchase_order, self).button_approve()
        for order in self:
            # get the company from partner then trigger action of intercompany relation
            company_rec = self.env['res.company']._find_company_from_partner(order.partner_id.id)
            if company_rec and company_rec.so_from_po and (not order.auto_generated):
                order.inter_company_create_sale_order(company_rec)
        return res


    @api.one
    def inter_company_create_sale_order(self, company):
        """ Create a Sales Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo, and the creation of the derived
            SO as intercompany_user, minimizing the access right required for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """

        print ('---inter_company_create_sale_order---')
        self = self.with_context(force_company=company.id)
        SaleOrder = self.env['sale.order']

        # find user for creating and validation SO/PO from partner company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise Warning(_('Provide at least one user for inter company relation for % ') % company.name)
        # check intercompany user access rights
        if not SaleOrder.sudo(intercompany_uid).check_access_rights('create', raise_exception=False):
            raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

        # check pricelist currency should be same with SO/PO document
        company_partner = self.company_id.partner_id.sudo(intercompany_uid)
        if self.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
            raise Warning(_('You cannot create SO from PO because sale price list currency is different than purchase price list currency.'))

        # create the SO and generate its lines from the PO lines
        SaleOrderLine = self.env['sale.order.line']
        # read it as sudo, because inter-compagny user can not have the access right on PO
        sale_order_data = self.sudo()._prepare_sale_order_data(self.name, company_partner, company, self.dest_address_id and self.dest_address_id.id or False)
        sale_order = SaleOrder.sudo(intercompany_uid).create(sale_order_data[0])
        # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
        for line in self.order_line.sudo():
            so_line_vals = self._prepare_sale_order_line_data(line, company, sale_order.id)
            SaleOrderLine.sudo(intercompany_uid).create(so_line_vals)
            # SaleOrderLinenew = SaleOrderLine.sudo(intercompany_uid).create(so_line_vals)
            # SaleOrderLinenew.sudo()._onchange_discount()

        # write vendor reference field on PO
        if not self.partner_ref:
            self.partner_ref = sale_order.name

        #Validation of sales order
        if company.auto_validation:
            sale_order.sudo(intercompany_uid).action_confirm()

    @api.one
    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        """ Generate the Sales Order values from the PO
            :param name : the origin client reference
            :rtype name : string
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param direct_delivery_address : the address of the SO
            :rtype direct_delivery_address : res.partner record
        """
        partner_addr = partner.sudo().address_get(['invoice', 'delivery', 'contact'])
        warehouse = company.warehouse_id and company.warehouse_id.company_id.id == company.id and company.warehouse_id or False
        ########### Add by JA-16/09/2020 #########
        partner_invoice_id = self.operating_unit_id.partner_id
        partner_shipping_id = self.operating_unit_id.partner_id
        team_id = self.env['crm.team'].search([('company_id','=',company.id),('name','=','Sales')],limit=1)
        ######### find ou of partner_id ###########3
        ou_for_sale_id = self.env['operating.unit'].sudo().search([('partner_id','=',self.partner_id.id)],limit=1)

        # print (ou_for_sale_id.name)
        # print(ou_for_sale_id.company_id.name)
        ########### Add by JA-16/09/2020 #########
        if not warehouse:
            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))
        return {
            'name': self.env['ir.sequence'].sudo().next_by_code('sale.order') or '/',
            'company_id': company.id,
            'warehouse_id': warehouse.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_invoice_id.id,
            'partner_shipping_id': partner_shipping_id.id,
            'team_id':team_id.id,
            'date_order': self.date_order,
            'fiscal_position_id': partner.property_account_position_id.id,
            'user_id': False,
            'auto_generated': True,
            'operating_unit_id':ou_for_sale_id.id or False,
            'auto_purchase_order_id': self.id,
        }

    @api.model
    def _prepare_sale_order_line_data(self, line, company, sale_id):
        """ Generate the Sales Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param sale_id : the id of the SO
        """
        # it may not affected because of parallel company relation
        price = line.price_unit or 0.0
        taxes = line.taxes_id
        if line.product_id:
            taxes = line.product_id.taxes_id
        company_taxes = [tax_rec for tax_rec in taxes if tax_rec.company_id.id == company.id]
        if sale_id:
            so = self.env["sale.order"].sudo(company.intercompany_user_id).browse(sale_id)
            company_taxes = so.fiscal_position_id.map_tax(company_taxes, line.product_id, so.partner_id)
        quantity = line.product_id and line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id) or line.product_qty
        price = line.product_id and line.product_uom._compute_price(price, line.product_id.uom_id) or price


        product_id = line.product_id and line.product_id or False
        product_uom = line.product_id and line.product_id.uom_id or line.product_uom
        discount = self._get_discount(sale_id, product_id, quantity, product_uom)

        return {
            'name': line.name,
            'order_id': sale_id,
            'product_uom_qty': quantity,
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'price_unit': price,
            'customer_lead': line.product_id and line.product_id.sale_delay or 0.0,
            'company_id': company.id,
            'discount': discount,
            'tax_id': [(6, 0, company_taxes.ids)],
        }

    def _get_discount(self, sale_id, product_id, product_uom_qty, product_uom):
        sale_id = self.env['sale.order'].sudo().browse(sale_id)
        product = product_id.with_context(
            lang=sale_id.partner_id.lang,
            partner=sale_id.partner_id.id,
            quantity=product_uom_qty,
            date=sale_id.date_order,
            pricelist=sale_id.pricelist_id.id,
            uom=product_uom.id
        )

        product_context = dict(self.env.context, partner_id=sale_id.partner_id.id, date=sale_id.date_order,
                               uom=product_uom.id)

        price, rule_id = sale_id.pricelist_id.with_context(product_context).get_product_price_rule(
            product_id, product_uom_qty or 1.0, sale_id.partner_id)
        new_list_price, currency_id = self.env['sale.order.line'].with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                                                         product_uom_qty,
                                                                                                                         product_uom,
                                                                                                                         sale_id.pricelist_id.id)
        print('new_list_price :', new_list_price)
        if new_list_price != 0:
            if sale_id.pricelist_id.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(
                    new_list_price, sale_id.pricelist_id.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            print('discount :', discount)
            if discount > 0:
                return discount

        return 0.0