# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MaterialPurchaseRequisition(models.Model):
    _name = "material.purchase.requisition"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'sequence'
    _order = 'create_date desc'

    @api.model
    def create(self , vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('material.purchase.requisition') or '/'
        return super(MaterialPurchaseRequisition, self).create(vals)

    @api.model
    def default_get(self, flds):
        result = super(MaterialPurchaseRequisition, self).default_get(flds)
        if self.env.user.employee_ids:
            result['employee_id'] = self.env.user.employee_ids[0].id
        result['requisition_date'] = datetime.now()
        return result

    def get_action_url(self):
        """
        Return a short link to the audit form view
        eg. http://localhost:8069/?db=prod#id=1&model=mgmtsystem.audit
        """
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url',
            default='http://localhost:8069'
        )
        url = ('{}/web#db={}&id={}&model={}').format(
            base_url,
            self.env.cr.dbname,
            self.id,
            self._name
        )
        return url

    @api.multi
    def confirm_requisition(self):
        res = self.write({'state':'department_approval',
                          'confirmed_by_id':self.env.user.id,
                          'confirmed_date' : datetime.now()
                          })

        recipient_ids = []
        if self.requisition_responsible_id:
            recipient_ids.append(self.requisition_responsible_id.partner_id.id)

        if self.department_id and self.department_id.manager_id:
            user_id = self.department_id.manager_id.user_id
            if user_id:
                if user_id.partner_id.id not in recipient_ids:
                    recipient_ids.append(user_id.partner_id.id)

        template_id = self.env['ir.model.data'].get_object_reference(
            'bi_material_purchase_requisitions',
            'email_to_manager_purchase_requisition')[1]

        # print('recipient_ids : ',recipient_idsnot recipient_ids or )
        if (not self.department_id.manager_id.work_email and not self.requisition_responsible_id.partner_id.email) or \
                not self.employee_id.work_email:
            raise UserError(_('Please setup email employee , department manager or requisition responsible'))

        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.employee_id.name + ' <' + self.employee_id.work_email + '>'
            values['email_to'] = self.department_id.manager_id.work_email
            values['email_cc'] = self.requisition_responsible_id.partner_id.email
            # values['recipient_ids'] = [(6,0,recipient_ids)]
            values['res_id'] = self.id
            values['author_id'] = self.employee_id.user_id.partner_id.id or self.create_uid.partner_id.id
            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.sudo().create(values)
            # print('msg_id : ', msg_id)
            if msg_id:
                msg_id.send()

        return res

    @api.multi
    def department_approve(self):
        res = self.write({
            'state':'ir_approve',
            'department_manager_id':self.env.user.id,
            'department_approval_date' : datetime.now()
        })
        template_id = self.env['ir.model.data'].get_object_reference(
            'bi_material_purchase_requisitions',
            'email_manager_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.env.user.partner_id.email
            values['email_to'] = self.employee_id.work_email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])
        return res

    @api.multi
    def action_cancel(self):
        res = self.write({
            'state':'cancel',
        })
        return res

    @api.multi
    def action_received(self):
        res = self.write({
            'state':'received',
            'received_date' : datetime.now()
        })
        return res

    @api.multi
    def action_reject(self):
        res = self.write({
            'state':'cancel',
            'rejected_date' : datetime.now(),
            'rejected_by' : self.env.user.id
        })
        return res

    @api.multi
    def action_reset_draft(self):
        res = self.write({
            'state':'new',
        })
        return res

    @api.multi
    def action_approve(self):
        res = self.write({
            'state':'approved',
            'approved_by_id':self.env.user.id,
            'approved_date' : datetime.now()
        })
        template_id = self.env['ir.model.data'].get_object_reference(
            'bi_material_purchase_requisitions',
            'email_user_purchase_requisition')[1]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = self.employee_id.work_email
            values['email_to'] = self.employee_id.work_email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            #request.env.uid = 1
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.send([msg_id])

        self.create_picking_po()
        return res

    @api.multi
    def create_picking_po(self):
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']
        stock_picking_type_obj = self.env['stock.picking.type']

        for line in self.requisition_line_ids:
            if line.requisition_action == 'purchase_order':
                for vendor in line.vendor_id:
                    pur_order = purchase_order_obj.search([('requisition_po_id','=',self.id),('partner_id','=',vendor.id)])
                    picking_type_ids = stock_picking_type_obj.search([('code', '=', 'incoming')])
                    if not picking_type_ids:
                        raise UserError(_('Please setup incoming picking type'))
                    if pur_order:
                        po_line_vals = {
                            'product_id' : line.product_id.id,
                            'product_qty': line.qty,
                            'name' : line.description,
                            'price_unit' : line.product_id.list_price,
                            'date_planned' : datetime.now(),
                            'product_uom' : line.uom_id.id,
                            'order_id' : pur_order.id,
                        }
                        purchase_order_line = purchase_order_line_obj.create(po_line_vals)
                        # print("purchase_order_line create")
                    else:
                        # print("not pur_order")
                        vals = {
                            'partner_id' : vendor.id,
                            'date_order' : datetime.now(),
                            'requisition_po_id' : self.id,
                            'state' : 'draft',
                            'picking_type_id':picking_type_ids[0].id,
                        }
                        purchase_order = purchase_order_obj.create(vals)
                        # print("purchase_order create")
                        po_line_vals = {
                            'product_id' : line.product_id.id,
                            'product_qty': line.qty,
                            'name' : line.description,
                            'price_unit' : line.product_id.list_price,
                            'date_planned' : datetime.now(),
                            'product_uom' : line.uom_id.id,
                            'order_id' : purchase_order.id,
                        }
                        purchase_order_line = purchase_order_line_obj.create(po_line_vals)
                        print ("purchase_order_line create")
            else:
                # for vendor in line.vendor_id:
                stock_picking_obj = self.env['stock.picking']
                stock_move_obj = self.env['stock.move']

                # picking_type_ids = stock_picking_type_obj.search([('code', '=', 'internal')])
                # employee_id = self.env['hr.employee'].search('id','=',self.env.user.name)
                stock_picking_ids = stock_picking_obj.search(
                    [('requisition_picking_id', '=', self.id)],limit=1)
                if stock_picking_ids:
                    # pic_line_val = {
                    #     'name': line.product_id.name,
                    #     'product_id': line.product_id.product_variant_id.id,
                    #     'product_uom_qty': line.qty,
                    #     'product_uom': line.uom_id.id,
                    #     'picking_id': self.internal_picking_id.id,
                    #     'product_uom': line.uom_id.id,
                    #     'location_id': self.source_location_id.id,
                    #     'location_dest_id': self.destination_location_id.id,
                    # }
                    pic_line_val = {
                        # 'partner_id': vendor.id,
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.qty,
                        'product_uom': line.uom_id.id,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                        'picking_id': stock_picking.id,
                        'picking_type_id': stock_picking.picking_type_id.id,
                    }
                    stock_move = stock_move_obj.create(pic_line_val)
                    print("stock_move create : " + str(stock_move))
                else:
                    print("not stock_picking_ids")
                    val = {
                        # 'partner_id': vendor.id,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                        'picking_type_id': self.internal_picking_id.id,
                        'company_id': self.env.user.company_id.id,
                        'requisition_picking_id': self.id,
                        'origin': self.sequence,
                        'note': self.reason_for_requisition,
                        'ticket_number': self.ticket_number,
                        'delivery_location': self.delivery_location,
                        'internal_transfer_type': self.internal_transfer_type.id,
                        'employee_id': self.employee_id.id,
                        'department_id': self.department_id.id,
                        'number_of_day': self.number_of_day,
                        # 'material_requisition_id': self.job_order_id and self.job_order_id.id,
                        # 'job_order_user_id': self.job_order_user_id and self.job_order_user_id.id,
                        # 'construction_project_id': self.construction_project_id and self.construction_project_id.id,
                        # 'analytic_account_id': self.account_analytic_id and self.account_analytic_id.id,
                        # ---------------------------------------------------------
                        'owner_id': self.requisition_responsible_id.partner_id.id,
                        'new_note': self.new_note,
                    }
                    stock_picking = stock_picking_obj.create(val)
                    # print("stock_picking create : " + str(stock_picking))
                    pic_line_val = {
                        # 'partner_id': vendor.id,
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.qty,
                        'product_uom': line.uom_id.id,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                        'picking_id': stock_picking.id,
                        'picking_type_id': stock_picking.picking_type_id.id,
                    }
                    stock_move = stock_move_obj.create(pic_line_val)
                    print("stock_move create : " + str(stock_move))
                    stock_picking.action_confirm()
                    stock_picking.action_assign()

        res = self.write({
            'state':'po_created',
        })
        return res

    @api.multi
    def _get_internal_picking_count(self):
        for picking in self:
            picking_ids = self.env['stock.picking'].search([('requisition_picking_id','=',picking.id)])
            picking.internal_picking_count = len(picking_ids)

    @api.multi
    def internal_picking_button(self):
        self.ensure_one()
        return {
            'name': 'Internal Picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_picking_id', '=', self.id)],
        }

    @api.multi
    def _get_purchase_order_count(self):
        for po in self:
            po_ids = self.env['purchase.order'].search([('requisition_po_id','=',po.id)])
            po.purchase_order_count = len(po_ids)

    @api.multi
    def purchase_order_button(self):
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_po_id', '=', self.id)],
        }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    @api.model
    def _default_picking_internal_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.destination_location_id = self.employee_id.destination_location_id
        self.department_id = self.employee_id.department_id

    # @api.multi
    # def _get_emp_destination(self):
    #     print ('_get_emp_destination')
    #     print (self.employee_id.destination_location_id)
    #     if not self.employee_id.destination_location_id:
    #         return
    #
    #     print ('update')
    #     self.destination_location_id =  self.employee_id.destination_location_id

    sequence = fields.Char(string='Sequence', readonly=True,copy =False)
    employee_id = fields.Many2one('hr.employee',string="Employee",required=True)
    department_id = fields.Many2one('hr.department',string="Department",required=True)
    requisition_responsible_id  = fields.Many2one('res.users',string="Requisition Responsible")
    requisition_date = fields.Date(string="Requisition Date",required=True,default=fields.Datetime.now)
    received_date = fields.Date(string="Received Date",readonly=True)
    requisition_deadline_date = fields.Date(string="Requisition Deadline")
    state = fields.Selection([('new','New'),
                              ('department_approval','Waiting Department Approval'),
                              ('ir_approve','Waiting IR Approved'),
                              ('approved','Approved'),
                              ('po_created','Purchase Order Created'),
                              ('received','Received'),
                              ('cancel','Cancel')],string='Stage',default="new",track_visibility='onchange')
    requisition_line_ids = fields.One2many('requisition.line','requisition_id',string="Requisition Line ID")
    confirmed_by_id = fields.Many2one('res.users',string="Confirmed By", readonly=True)
    department_manager_id = fields.Many2one('res.users',string="Department Manager", readonly=True)
    approved_by_id = fields.Many2one('res.users',string="Approved By", readonly=True)
    rejected_by = fields.Many2one('res.users',string="Rejected By", readonly=True)
    confirmed_date = fields.Date(string="Confirmed Date",readonly=True)
    department_approval_date = fields.Date(string="Department Approval Date",readonly=True)
    approved_date = fields.Date(string="Approved Date",readonly=True)
    rejected_date = fields.Date(string="Rejected Date",readonly=True)
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    internal_picking_id = fields.Many2one('stock.picking.type', string="Internal Picking",
                                          default=_default_picking_internal_type)
    source_location_id = fields.Many2one('stock.location',string="Source Location", related="internal_picking_id.default_location_src_id")
    destination_location_id = fields.Many2one('stock.location',string="Destination Location")

    internal_picking_count = fields.Integer('Internal Picking', compute='_get_internal_picking_count')
    purchase_order_count = fields.Integer('Purchase Order', compute='_get_purchase_order_count')
    company_id = fields.Many2one('res.company',string="Company")

    ##########Not use for TR
    picking_type_id = fields.Many2one('stock.picking.type',string='Picking Type')
    warranty_type = fields.Selection([('in','In-Warranty'),('out','Out-Warranty')],string='Warranty Type')
    ticket_number = fields.Char(string='Ticket Number')
    number_of_day = fields.Integer(string='Number of Borrow Day')
    delivery_location = fields.Text(string='Delivery Location')
    internal_transfer_type = fields.Many2one('internal.transfer.type', string='Internal Transfer Type')
    new_note = fields.Text(string="Notes")

class RequisitionLine(models.Model):
    _name = "requisition.line"

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name

    product_id = fields.Many2one('product.product',string="Product")
    description = fields.Text(string="Description")
    qty = fields.Float(string="Quantity",default=1.0)
    uom_id = fields.Many2one('product.uom',string="Unit Of Measure")
    requisition_id = fields.Many2one('material.purchase.requisition',string="Requisition Line")
    requisition_action = fields.Selection([('purchase_order','Purchase Order'),('internal_picking','Internal Picking')],default='internal_picking',string="Requisition Action")
    vendor_id = fields.Many2many('res.partner',string="Vendors")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    requisition_picking_id = fields.Many2one('material.purchase.requisition',string="Purchase Requisition")
    ticket_number = fields.Char(string='Ticket Number')
    delivery_location = fields.Text(strng='Delivery Location')
    internal_transfer_type = fields.Many2one('internal.transfer.type',string='Internal Transfer Type')
    number_of_day = fields.Integer(string='Number of Borrow Day')
    # employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', string="Department")

class Internal_Transfer_type(models.Model):
    _name = 'internal.transfer.type'

    name = fields.Char(string='Type')
    code = fields.Char(string='Code')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    requisition_po_id = fields.Many2one('material.purchase.requisition',string="Purchase Requisition")

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    destination_location_id = fields.Many2one('stock.location',string="Destination Location")

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    destination_location_id = fields.Many2one('stock.location',string="Destination Location")    


    
