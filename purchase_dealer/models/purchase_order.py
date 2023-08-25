# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class dealer_purchase_order(models.Model):
    _name = 'dealer.purchase.order'
    _inherit = 'mail.thread'
    _order = 'id desc'

    @api.model
    def _default_operating_unit(self):
        return self.env.user.default_operating_unit_id

    @api.model
    def _default_purchase_order_type(self):
        return self.env.user.order_type

    @api.model
    def _default_purchase_type(self):
        return self.env.user.purchase_type

    @api.model
    def _prepare_purchase_order(self, picking_type,company, origin, purchase_type, order_type):
        if not self.branch_id.picking_type_id:
            raise UserError(_('Enter a Picking type in branch.'))

        supplier_company = self.env['res.company'].sudo().search([('so_from_po','=',True)],limit=1)
        print (supplier_company)

        supplier = supplier_company.partner_id

        matrix_id = self.env['purchase.approval.matrix'].search(
            [('purchase_type', '=', purchase_type.id), ('type', '=', 'PO')], limit=1)
        print ('-------MATRIX ID')
        print(matrix_id)
        # line.request_id.purchase_type
        if order_type:
            ''
        data = {
            'origin': origin,
            'partner_id': supplier.id,
            'fiscal_position_id': supplier.property_account_position_id and
                                  supplier.property_account_position_id.id or False,
            # 'picking_type_id': 24,
            'purchase_type': purchase_type.id,
            'operating_unit': self.branch_id.id,
            'company_id': company.id,
            'name': 'New',
            'matrix_id': matrix_id.id,
            'picking_type_id': self.branch_id.picking_type_id.id,
            'order_type': order_type.id,
            'new_note': origin,
            # 'assigned_to': assigned_to.id,
        }
        return data

    @api.model
    def _execute_purchase_line_onchange(self, vals):
        cls = self.env['purchase.order.line']
        onchanges_dict = {
            'onchange_product_id': self._get_purchase_line_onchange_fields(),
        }
        for onchange_method, changed_fields in onchanges_dict.items():
            if any(f not in vals for f in changed_fields):
                obj = cls.new(vals)
                getattr(obj, onchange_method)()
                for field in changed_fields:
                    vals[field] = obj._fields[field].convert_to_write(
                        obj[field], obj)

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        # print("def _prepare_purchase_order_line")
        product = item.product_id
        # Keep the standard product UOM for purchase order so we should
        # convert the product quantity to this UOM
        qty = item.product_uom_id._compute_quantity(
            item.product_qty, product.uom_po_id or product.uom_id)
        # Suggest the supplier min qty as it's done in Odoo core
        # min_qty = item.line_id._get_supplier_min_qty(product, po.partner_id)
        # qty = 0
        vals = {
            'name': product.name,
            # 'pr_id': item.line_id.request_id.id,
            'order_id': po.id,
            'product_id': product.id,
            'product_uom': item.product_uom_id.id,
            'price_unit': item.product_id.standard_price,
            'product_qty': item.product_qty,
            # 'account_analytic_id': item.line_id.analytic_account_id.id,
            # 'purchase_request_lines': [(4, item.line_id.id)],
            'date_planned': self.date_order,

            # 'move_dest_ids': [(4, x.id) for x in item.line_id.move_dest_ids]
        }
        # self._execute_purchase_line_onchange(vals)
        # if vals:
        #     vals.update({'product_uom': item.product_uom_id.id,
        #                  'price_unit': item.product_id.standard_price, })

        return vals

    @api.model
    def _get_purchase_line_name(self, order, line):
        # product_lang = line.product_id.with_context({
        #     'lang': self.supplier_id.lang,
        #     'partner_id': self.supplier_id.id,
        # })
        name = line.product_id.display_name
        # if product_lang.description_purchase:
        #     name += '\n' + product_lang.description_purchase
        return name

    @api.model
    def _get_order_line_search_domain(self, order, item):
        vals = self._prepare_purchase_order_line(order, item)
        name = self._get_purchase_line_name(order, item)
        order_line_data = [('order_id', '=', order.id),
                           ('name', '=', name),
                           ('product_id', '=', item.product_id.id or False),
                           ('product_uom', '=', item.product_uom_id.id),
                           ('account_analytic_id', '=', False),
                           ]
        # if self.sync_data_planned:
        #     order_line_data += [
        #         ('date_planned', '=', item.line_id.date_required)
        #     ]
        if not item.product_id:
            order_line_data.append(('name', '=', item.name))
        return order_line_data

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('dealer.order') or _('New')
        return super(dealer_purchase_order,self).create(vals)

    @api.multi
    def action_confirm(self):
        res = []
        purchase_obj = self.env['purchase.order']
        po_line_obj = self.env['purchase.order.line']
        ############
        pr_line_obj = self.env['purchase.request.line']

        purchase = False

        check_order_type = False
        before_order_type = False
        # for line in self.item_ids:
        #     # print(line.request_id.order_type.name)
        #     if not before_order_type:
        #         before_order_type = line.request_id.order_type.id
        #     if before_order_type != line.request_id.order_type.id:
        #         check_order_type = True
        # if check_order_type:
        #     # print('not check_order_type')
        #     raise UserError(_('There are different purchase order types. Cannot do the transaction.'))
        #
        # else:
        if self.purchase_order_id:
            if self.purchase_order_id.state in ('purchase', 'done', 'approved'):
                raise UserError(_('Purchase Order in Purchase, Approve and Done state is not allow to add more product'))
            else:
                self.purchase_order_id.order_line.sudo().unlink()

        for item in self.item_ids:
            # line = item.line_id
            if item.product_qty <= 0.0:
                continue
            if self.purchase_order_id:
                purchase = self.purchase_order_id
            if not purchase:
                po_data = self._prepare_purchase_order(24,self.env.user.company_id,self.note,self.purchase_type,self.order_type)

                purchase = purchase_obj.create(po_data)
                purchase._get_allow_group()
                if purchase.assigned_to:
                    purchase.update({'user_check_id':purchase.assigned_to.id})

            # Look for any other PO line in the selected PO with same
            # product and UoM to sum quantities instead of creating a new
            # po line
            domain = self._get_order_line_search_domain(purchase, item)
            available_po_lines = po_line_obj.search(domain)
            new_pr_line = True

            po_line_data = self._prepare_purchase_order_line(purchase, item)
            po_line = po_line_obj.create(po_line_data)
            res.append(purchase.id)
            # print ('PO NUMBER')
            # print (purchase.name)
            self.purchase_order_id = purchase.id
            self.state = 'confirm'

        #start to confirm order automatically
        if self.env.user.company_id.is_auto_confirm_po and self.purchase_order_id:
            user_id = self.env['res.users'].sudo().search([('name','like','admin_'),('company_id','=',self.env.user.company_id.id)],limit=1)
            if user_id:
                self.purchase_order_id.write({'user_check-id':user_id.id,'assigned_to':user_id.id})
                self.purchase_order_id.sudo().button_confirm()
                self.purchase_order_id.sudo().button_approve()
                self.purchase_order_id.write({'user_check_id': user_id.id, 'assigned_to': user_id.id})
            else:
                raise UserError(
                    _('ไมพบ User Admin ของสาขานี้'))






    @api.multi
    def get_product_list(self):
        self.item_ids.sudo().unlink()
        product_ids = self.env['product.product'].search([('is_dealer_order_available','=',True)])
        for product in product_ids:
            val = {
                'product_id': product.id,
                'product_qty': 0,
                'product_uom_id': product.uom_id.id,
                'dealer_order_id': self.id,
            }
            self.env['dealer.purchase.order.line'].create(val)



    date_order = fields.Datetime('Order Date', required=True, index=True, copy=False, default=fields.Datetime.now)
    branch_id = fields.Many2one('operating.unit',default=_default_operating_unit,string='Branch')
    name = fields.Char(string='Purchase Number')
    item_ids = fields.One2many('dealer.purchase.order.line','dealer_order_id',string='Dealer Purchase Order ID')
    state = fields.Selection([('new','New'),('confirm','Confirm')],default='new', string='State')
    note = fields.Text(string='Note')
    purchase_order_id = fields.Many2one('purchase.order',string='Purchase Order')
    order_type = fields.Many2one('purchase.order.type',string='Purchase Order Type',default=_default_purchase_order_type)
    purchase_type = fields.Many2one('purchase.type', string='Purchase Type',default=_default_purchase_type)


class dealer_purchase_order_line(models.Model):
    _name = 'dealer.purchase.order.line'

    product_id = fields.Many2one('product.product',string='Product')
    product_qty = fields.Integer(string='QTY')
    product_uom_id = fields.Many2one('product.uom',string='Product UOM')
    dealer_order_id = fields.Many2one('dealer.purchase.order',string='Dealder Order ID')