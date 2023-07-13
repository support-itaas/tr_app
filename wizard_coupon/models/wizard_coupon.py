# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
import json
from datetime import date, timedelta
# import datetime
import requests

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class WizardCoupon(models.Model):
    _name = 'wizard.coupon'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Coupon'

    name = fields.Text(readonly=True, required=True, copy=False, default=lambda x: _('New'))
    package_id = fields.Many2one('product.product', string="Package")
    product_id = fields.Many2one('product.product', required=True, string="Coupon")
    product_package_id_line_id = fields.Many2one('')
    branch_id = fields.Many2one('project.project', string="Redeemed Branch")
    date_order = fields.Date(string="Order Date")
    order_branch_id = fields.Many2one('project.project', required=False, string="Purchase At")
    purchase_date = fields.Date(required=True, default=datetime.datetime.today())
    expiry_date = fields.Date(string="Expiry Date", readonly=True, compute="compute_expiry_date", store="True")
    # state = fields.Selection([('draft', 'Available'), ('redeem_request', 'Redeem Requested'),
    #                           ('redeem', 'Redeemed'), ('expire', 'Expired')], string='state',
    #                          default='draft')
    state = fields.Selection([('draft', 'Available'), ('redeem', 'Redeemed'), ('expire', 'Expired')], string='state',
                             default='draft')
    redeem_date = fields.Date(readonly=True, string="Redeem Date", )
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', track_sequence=2,
                                 required=True)
    plate_number_id = fields.Many2one('car.details', string='Plate Number')
    note = fields.Text(string="Notes")
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    amount = fields.Float("Amount", digits=dp.get_precision('Amount'))
    image = fields.Binary(string='Image', readonly=True)
    description = fields.Text(string='Description', readonly=True)
    active = fields.Boolean(default=True)
    order_id = fields.Many2one('pos.order', string="Order_Id")
    coupon_code = fields.Char(related='product_id.default_code', string='Coupon Code')
    is_promotional_pkg = fields.Boolean(related='package_id.is_promotional_pkg', string='Is Promotional Package', default=False)
    #--------------------------------------------
    source_operating_unit_id = fields.Many2one('operating.unit',related='order_branch_id.operating_branch_id', string="Source Operating Unit")
    source_branch_amount = fields.Float("Source Branch Amount", digits=dp.get_precision('Amount'))
    destination_operating_unit_id = fields.Many2one('operating.unit',related='branch_id.operating_branch_id', string="Destination Operating Unit")
    destination_branch_amount = fields.Float("Destination Branch Amount", digits=dp.get_precision('Amount'))
    #########################################
    session_id = fields.Many2one('pos.session', string='Session')
    coupon_running = fields.Char(readonly=True, required=True, copy=False, default=lambda x: _('New'))
    # redeem_request_date = fields.Date(string='Redeem Requested Date')

    @api.onchange('package_id')
    def _package_onchange(self):
        products = []
        for pdt in self.package_id.product_pack_id:
            products.append(pdt.product_id.id)
        res = {'domain': {'product_id': [('id', 'in', products)]}}
        return res

    @api.onchange('partner_id')
    def _partner_onchange(self):
        cars = []
        if self.partner_id.car_ids:
            cars.extend(self.partner_id.car_ids.ids)
        res = {'domain': {'plate_number_id': [('id', 'in', cars)]}}
        return res

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('wizard.coupon') or _('New')
        res = super(WizardCoupon, self).create(vals)
        res.write({
            'image': res.product_id.image_medium,
            'description': res.product_id.description_sale
        })
        return res

    @api.multi
    def copy(self, default=None):
        raise UserError(_('Duplicating coupon is not allowed.'))

    @api.multi
    def unlink(self):
        for coupon in self:
            if coupon.state in ['redeem', 'expire']:
                raise UserError(_('You cannot delete this coupon'))
        return super(WizardCoupon, self).unlink()

    @api.multi
    def button_cancel(self):
        for coupon_id in self:
            journal = self.env['account.move'].search([('ref', '=', coupon_id.name)], limit=1)
            if journal:
                if not journal.journal_id.update_posted:
                    raise UserError(_('Please allow cancelling entries in journal settings'))
                else:
                    journal.button_cancel()
                    journal.unlink()
                    coupon_id.redeem_date = False
                    coupon_id.branch_id = False
                    coupon_id.plate_number_id = False
                    coupon_id.state = 'draft'

    @api.multi
    @api.depends('product_id', 'package_id')
    def compute_expiry_date(self):
        for record in self:
            if record.package_id:
                for x in record.package_id.product_pack_id:
                    if record.product_id == x.product_id:
                        if x.coupon_validity > 0:
                            expirdate = date.today() + timedelta(days=x.coupon_validity)
                            record.expiry_date = datetime.datetime.strptime((expirdate.strftime("%d-%m-%Y")),
                                                                            '%d-%m-%Y')
                        else:
                            expirdate = date.today() + timedelta(days=x.product_id.coupon_validity)
                            record.expiry_date = datetime.datetime.strptime((expirdate.strftime("%d-%m-%Y")),
                                                                            '%d-%m-%Y')
            else:
                if record.product_id:
                    expirdate = date.today() + timedelta(days=record.product_id.coupon_validity)
                    record.expiry_date = datetime.datetime.strptime((expirdate.strftime("%d-%m-%Y")), '%d-%m-%Y')
                    print("record.expiry_date", record.expiry_date)
                else:
                    record.expiry_date = None


    @api.multi
    def transfer_customer(self):
        wizard_form_id = self.env.ref('wizard_coupon.view_wizard_customer_transfer').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'wizard.customer.transfer',
                'view_mode': 'form',
                'views': [(wizard_form_id, 'form')],
                'target': 'new'}

    @api.multi
    def transfer_coupon_app(self, coupon_ids, current_partner_id, note, mobile):
        # app
        if current_partner_id:
            current_partner = self.env['res.partner'].browse(current_partner_id)
        #     if current_partner.mobile == mobile:
        #         return False
        if coupon_ids:
            coupons = self.env['wizard.coupon'].browse(coupon_ids)
            if mobile:
                partner = self.env['res.partner'].search([('mobile', '=', mobile)])
                if partner:
                    coupons.write({'partner_id': partner.id, 'note': note})
                    receiving_partner = partner
                else:

                    notification = self.env['wizard.notification'].create({
                        'name': 'รายชื่อผู้รับไม่ถูกต้อง',
                        'message': 'การโอนย้าย Coupon ไม่สมบูรณ์ กรุณาตรวจสอบรายชื่อก่อนโอนย้ายอีกครั้ง',
                        'read_message': False,
                        'partner_id': current_partner.id,
                        'message_at': fields.Datetime.now(),
                    })
                    if current_partner.device_token:
                        serverToken = self.env['car.settings'].sudo().search([]).server_token
                        deviceToken = current_partner.device_token
                        notifications = self.env['wizard.notification'].search([('partner_id', '=', current_partner.id),
                                                                                ('read_message', '=', False)])

                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': 'key=' + serverToken,
                        }

                        body = {
                            'notification': {'title': 'รายชื่อผู้รับไม่ถูกต้อง',
                                             'body': 'การโอนย้าย Coupon ไม่สมบูรณ์ กรุณาตรวจสอบรายชื่อก่อนโอนย้ายอีกครั้ง',
                                             'badge': len(notifications),
                                             "click_action": "FCM_PLUGIN_ACTIVITY"
                                             },
                            'to':
                                deviceToken,
                            'priority': 'high',
                            'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                        }
                        response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers,
                                                 data=json.dumps(body))
                    return False
                    ##################if no partner then not allow to send out ##############
                    ################## 16/06/2020 ###########################################
                    # new_partner_id = self.env['res.partner'].create({'name': mobile,
                    #                                                  'mobile': mobile})
                    # coupons.write({'partner_id': new_partner_id.id, 'note': note})
                    # receiving_partner = new_partner_id
            # coupon transfer notification
            var = ""

            for coupon in coupons:
                var += coupon.name + ', '
            result = var[:-2]

            notification = self.env['wizard.notification'].create({
                'name': 'Coupon ' + result + ' is transferred',
                'message': 'Your coupon ' + result + ' is successfully transferred to ' + receiving_partner.name + ' (' + str(
                    receiving_partner.mobile) + '). ',
                'read_message': False,
                'partner_id': current_partner.id,
                'message_at': fields.Datetime.now(),
            })
            if current_partner.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                deviceToken = current_partner.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', current_partner.id),
                                                                        ('read_message', '=', False)])

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Coupon ' + result + ' is transferred',
                                     'body': 'Your coupon ' + result + ' is successfully transferred to ' + receiving_partner.name + ' (' + str(
                    receiving_partner.mobile) + '). ',
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers,
                                         data=json.dumps(body))

            notification = self.env['wizard.notification'].create({
                'name': 'Coupon ' + result + ' is received',
                'message': 'You are successfully received Coupon with Coupon number ' + result + ' from ' + current_partner.name + ' (' + str(
                    current_partner.mobile) + ') ' + '.',
                'read_message': False,
                'partner_id': receiving_partner.id,
                'message_at': fields.Datetime.now(),
            })
            if receiving_partner.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                deviceToken = receiving_partner.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', receiving_partner.id),
                                                                        ('read_message', '=', False)])

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Coupon ' + result + ' is received',
                                     'body': 'You are successfully received Coupon with Coupon number ' + result + ' from ' + current_partner.name + ' (' + str(
                    current_partner.mobile) + ') ' + '.',
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers,
                                         data=json.dumps(body))
            # errrrrror
        else:
            return False

    @api.multi
    def use_coupon_app(self, partner_id):
        # app
        if partner_id:
            group_coupons = {}
            coupons = self.search([('state', '=', 'draft'), ('partner_id', '=', partner_id),
                                   ('type', '=', 'e-coupon')])
            for coupon in coupons:
                coupon_vals = {'id': coupon.id,
                               'name': coupon.name,
                               'partner_id': coupon.partner_id.id,
                               'partner': coupon.partner_id.name,
                               'order_branch_id': coupon.order_branch_id.id,
                               'order_branch': coupon.order_branch_id.name,
                               'package_id': coupon.package_id.id,
                               'package': coupon.package_id.name,
                               'product_id': coupon.product_id.id,
                               'coupon': coupon.product_id.name,
                               'purchase_date': coupon.purchase_date,
                               'expiry_date': coupon.expiry_date,
                               'currency_id': coupon.currency_id.id,
                               'currency': coupon.currency_id.name
                               }
                if coupon.product_id.id not in group_coupons:
                    product_group = {'name': coupon.product_id.name,
                                     'image': coupon.product_id.image,
                                     'currency_id': coupon.product_id.currency_id.id,
                                     'currency': coupon.product_id.currency_id.name,
                                     'product_id': coupon.product_id.id,
                                     'is_pack': coupon.product_id.is_pack,
                                     'is_coupon': coupon.product_id.is_coupon,
                                     'is_service': coupon.product_id.is_service,
                                     'description': coupon.product_id.description,
                                     'description_sale': coupon.product_id.description_sale,
                                     'list_price': coupon.product_id.list_price,
                                     'coupon_validity': coupon.product_id.coupon_validity,
                                     'coupons': [coupon_vals],
                                     'count': 1}
                    group_coupons[coupon.product_id.id] = product_group
                else:
                    group_coupons[coupon.product_id.id]['count'] += 1
                    group_coupons[coupon.product_id.id]['coupons'].append(coupon_vals)
            return list(group_coupons.values())
        else:
            return False

    @api.multi
    def button_redeem(self, plate_id=None, branch_id=None, order_date=None, car_clean=None, barcode=None):
        # print('def button_redeem : ', plate_id, branch_id, order_date, car_clean, barcode)
        max_amount = 0
        parent_task_id = ""
        description = ""
        tasks = []

        for rec in self:
            date_redeem = rec.redeem_date or order_date
            if (plate_id is not None) and (not isinstance(plate_id, dict)):
                rec.plate_number_id = plate_id
            elif not rec.plate_number_id:
                raise UserError(_('Please choose the Plate Number'))
            if not rec.branch_id and (branch_id is not None and (not isinstance(branch_id, dict))):
                rec.branch_id = branch_id
            elif not rec.branch_id and branch_id is None:
                raise UserError(_('Please select the branch'))
            # if (order_date is not None) and (not isinstance(order_date, dict)):
            #     rec.order_date = order_date
            # elif not rec.order_date:
            #     raise UserError(_('Please choose the Order Date'))
            ##############Add this condition for create or not create a task for each coupon#######
            # still create task but change state to 'Done' auto
            if rec.plate_number_id:
                task = self.env['project.task'].create({
                    'name': rec.product_id.name,
                    'project_id': rec.branch_id.id if rec.branch_id else None,
                    'user_id': rec.branch_id.user_id.id,
                    'date_assign': rec.redeem_date,
                    'date_deadline': order_date or rec.redeem_date or date.today(),
                    'partner_id': rec.partner_id.id,
                    'coupon_id': rec.id,
                    'plate_number_id': rec.plate_number_id.id,
                    'amount': rec.amount,
                    'company_id': rec.branch_id.company_id.id,
                    'public_price': rec.product_id.lst_price,
                    'car_clean': car_clean,
                    'barcode': barcode
                })

                if rec.amount > max_amount:
                    max_amount = rec.amount
                    parent_task_id = task.id

                ######### if first task is not the highest one then it will be ignore, so append all task here.
                tasks.append(task)
                description += task.name + ","
                # still create task but change state to 'Done' auto, if flag create task is not tick
                if not rec.product_id.is_create_task:
                    task.state = 'done'
                    task.date_assign = date.today()
                    task.date_deadline = date_redeem or date.today()

                    done_state = self.env['project.task.type'].search([('name', 'in', ('done', 'Done'))], limit=1)
                    if done_state:
                        task.stage_id = done_state.id

            ########This may make cross branch use coupon issue
            # print ('11111')
            rec.create_actual_revenue()
            # print('2222')
            rec.create_picking()
            # print('3333')
            ########

            rec.state = 'redeem'


            # print('rec.redeem_date : ',rec.redeem_date)
            # print('order_date : ',order_date)

            if not rec.redeem_date and order_date:
                print('==================')
                rec.redeem_date = order_date
            elif not rec.redeem_date and not order_date:
                print('xxxxxxxxxxxxxxxxxxxxxx')
                rec.redeem_date = date.today()

            # if order_date:
            #     rec.redeem_date = order_date

            ########REMOVE FIRST as it will send again on start the task
            # self.env['wizard.notification'].create({
            #     'name': 'Coupon number ' + rec.name + ' has been used',
            #     'message': 'Coupon number ' + rec.name + ' redeemed at ' + rec.branch_id.name + ' for plate number ' +
            #                rec.plate_number_id.name + ' on ' + rec.redeem_date,
            #     'read_message': False,
            #     'partner_id': rec.partner_id.id,
            #     'message_at': fields.Datetime.now(),
            # })

        ######### update task end of the process
        ###### if it is child task then update parent task
        ###### if it is parent task then update description

        if tasks:
            for task in tasks:
                if task.id != parent_task_id:
                    task.write({'parent_id': parent_task_id})
                else:
                    task.write({'description': description})

        qr_url = 'http://erp.wizardgroup.com/web?#id=' + str(parent_task_id) + '&view_type=form&model=project.task'
        # print('.........', qr_url)
        return qr_url


    def create_picking(self):
        print ('def create_picking')
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        pos_order_obj = self.env['pos.order']

        for coupon in self:
            #################################
            # 1) change ---> company by redeem branch
            # 2) chnage ---> location ---> stock remove
            # 3) change ---> customer location
            company_id = coupon.branch_id.company_id.id
            pos_config = self.env['pos.config'].search([('branch_id', '=', coupon.branch_id.id)])[-1]
            if not pos_config:
                raise UserError(_('There is not POS for redeeming Branch. Please configure one'))
            else:
                location_id = pos_config.stock_location_id.id
            #################################
            product = coupon.product_id.related_service_id
            print('1------2')
            if not product:
                raise UserError(_('Please configure related service to coupon product.'))

            if coupon.order_id:
                pos_order = self.env['pos.order'].search([('id', '=', coupon.order_id.id)])
            else:
                pos_order = False

            #####################Remove this condition
            # pos_order = self.env['pos.order'].search([('id', '=', coupon.order_id.id)])
            # if not pos_order:
            #     raise UserError(_('There is no related POS order available. Please contact the Manager'))
            # if len(pos_order.ids) > 1:
            #     pos_order[0]
            ###########################################
            if not product.filtered(lambda l: l.type in ['product', 'consu']):
                continue
            address = coupon.partner_id.address_get(['delivery']) or {}
            print('1------2')
            picking_type = pos_config.picking_type_id
            print('1------3')
            order_picking = Picking
            return_picking = Picking
            moves = Move


            print('1------4')
            if coupon.partner_id:
                destination_id = coupon.partner_id.property_stock_customer.id
                print('1------5')
            else:
                print('1------6')
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                    print('1------7')
                else:
                    destination_id = picking_type.default_location_dest_id.id
                    print('1------8')

            if picking_type:
                print('1------81')
                message = _(
                    "This transfer has been created from coupons: <a href=# data-oe-model=wizard.coupon data-oe-id=%d>%s</a>") % (
                              coupon.id, coupon.name)
                picking_vals = {
                    'origin': coupon.name,
                    'partner_id': address.get('delivery', False),
                    'date_done': coupon.redeem_date,
                    'picking_type_id': picking_type.id,
                    'company_id': company_id,
                    'move_type': 'direct',
                    'note': coupon.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                }

                print (coupon.partner_id.company_id.name)
                print (picking_vals)
                print('1------82')
                if product.type in ['product', 'consu']:
                    print('1------83')
                    order_picking = Picking.sudo().create(picking_vals.copy())

                    print('1------84')
                    order_picking.message_post(body=message)
                    print('1------85')
            qty = 1
            print('1------9')
            if product.type in ['product', 'consu'] and not float_is_zero(qty,
                                                                          precision_rounding=product.uom_id.rounding):
                moves |= Move.create({
                    'name': coupon.name,
                    'product_uom': product.uom_id.id,
                    'picking_id': order_picking.id,
                    'picking_type_id': picking_type.id,
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'state': 'draft',
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                })

            # prefer associating the regular order picking, not the return
            print('1------10')
            if pos_order:
                # edit by book
                task_ids = self.env['project.task'].sudo().search([('coupon_id','=',coupon.id)])
                for task in task_ids:
                    task.write({'picking_id': order_picking.id or return_picking.id})
                # pos_order.write({'picking_id': order_picking.id or return_picking.id})
                print('1------11')
            else:
                order_picking.action_assign()
                order_picking.force_assign()
                wrong_lots = coupon.set_pack_operation_lot(order_picking)
                if not wrong_lots:
                    try:
                        print ('no wrong_lots')
                        order_picking.button_validate()
                    except:
                        print ('ERRRRRRRRRRRR')
                        continue



            if return_picking and pos_order:
                print('1------12')
                pos_order._force_picking_done(return_picking)
                print('1------13')
            if order_picking and pos_order:
                print('1------14')
                pos_order._force_picking_done(order_picking)
                print('1------15')



            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                print('1------16')
                moves._action_assign()
                print('1------17')
                moves.filtered(lambda m: m.state in ['confirmed', 'waiting'])._force_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()
                print('1------18')


        print('1------22')
        return True

    def set_pack_operation_lot(self, picking=None):
        """Set Serial/Lot number in pack operations to mark the pack operation done."""

        has_wrong_lots = False
        for move in picking.move_lines:
            for move_line in move.move_line_ids:
                move_line.qty_done = move_line.product_uom_qty

        # print (has_wrong_lots)
        return has_wrong_lots


    @api.multi
    def expire_coupon(self):
        for coupon in self:
            if not coupon.branch_id:
                coupon.branch_id = coupon.order_branch_id.id
            if self.branch_id:
                coupon.create_actual_revenue()
            elif self.order_branch_id:
                coupon.create_actual_revenue()
            coupon.create_reverse_wallet_entry()
            print ('-revese to wallet')
            coupon.state = 'expire'

    @api.multi
    def expire_coupon_scheduler(self):
        coupons = self.search([('expiry_date', '<=', date.today()), ('state', '=', 'draft')])
        for coupon in coupons:
            if not coupon.branch_id:
                coupon.branch_id = coupon.order_branch_id.id
            coupon.expire_coupon()

    @api.multi
    def action_view_tasks(self):
        self.ensure_one()
        action = self.env.ref('project.action_view_task').read()[0]
        ###########Since change name from coupon number to coupon name, so change search from name to coupon_id
        action['domain'] = [('coupon_id', '=', self.id)]
        return action

    @api.multi
    def action_view_journal_entries(self):
        journals = self.env['account.move'].search([('ref', '=', self.name)])
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if len(journals) > 1:
            action['domain'] = [('id', 'in', journals.ids)]
            action['context'] = {}
        elif journals:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = journals.ids[0]
        return action

    @api.multi
    def action_view_pos_orders(self):
        orders = self.env['pos.order'].search([('id', '=', self.order_id.id)])
        action = self.env.ref('point_of_sale.action_pos_pos_form').read()[0]
        if len(orders) > 1:
            action['domain'] = [('id', 'in', orders.ids)]
        elif orders:
            action['views'] = [(self.env.ref('point_of_sale.view_pos_pos_form').id, 'form')]
            action['res_id'] = orders.ids[0]
        return action

    @api.multi
    def create_actual_revenue(self):
        # print ('--------create_actual_revenue')
        if not self.env['pos.config'].search([('branch_id', '=', self.branch_id.id)]):
            raise UserError(_('Please configure the branch in POS settings'))
        journal_id = self.env['pos.config'].sudo().search([('branch_id', '=', self.branch_id.id)],limit=1)[-1].journal_id.id
        print("orderbranch",self.order_branch_id)
        journal_original_id = self.env['pos.config'].sudo().search([('branch_id', '=', self.order_branch_id.id)],limit=1)[-1].journal_id.id

        if not self.env['car.settings'].search([]):
            raise UserError(_('Please configure the actual revenue account in settings'))
        actual_revenue_id = self.env['car.settings'].search([]).actual_revenue_id.id

        ########if real actual account set by product, otherwise will use global wide
        if self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().actual_income_account_id:
            actual_revenue_id = self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().actual_income_account_id.id

        # print (self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().actual_income_account_id)
        # print (self.product_id.sudo().property_account_income_id)
        if self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().property_account_income_id:
            product_journal = self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().property_account_income_id.id
        elif not self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().property_account_income_id and self.product_id.categ_id:
            product_journal = self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).categ_id.property_account_income_categ_id.id
        else:
            product_journal = self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).categ_id.parent_id.property_account_income_categ_id.id


        # print (actual_revenue_id)
        # print (product_journal)
        #############change operating unit from branch_id or order_branch_id

        account_move_line = [(0, 0, {
            'account_id': product_journal,
            'partner_id': self.partner_id.id,
            'name': 'Product Income',
            'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
            'debit': self.amount,
            'company_id': self.order_branch_id.sudo().company_id.id,
            'credit': 0.0,
        })]

        if self.branch_id == self.order_branch_id:
            print ('------SAME BRANCH')
            account_move_line.append((0, 0, {
                'account_id': actual_revenue_id,
                'partner_id': self.partner_id.id,
                'name': 'Actual Income',
                'analytic_account_id': self.branch_id.sudo().analytic_account_id.id,
                'operating_unit_id': self.branch_id.sudo().operating_branch_id.id,
                'company_id': self.branch_id.sudo().company_id.id,
                'debit': 0.0,
                'credit': self.amount,
            }))
            # add update amount bybook
            self.update({'source_branch_amount': self.amount, })
        # print (account_move_line)
        # print ('---frst move---')
        source_branch_ratio = self.env['car.settings'].sudo().search([]).source_branch_ratio
        # print (source_branch_ratio)
        source_branch_amount = self.amount * (source_branch_ratio / 100)
        # print(source_branch_amount)
        destination_branch_ratio = self.env['car.settings'].sudo().search([]).destination_branch_ratio
        # print(destination_branch_ratio)
        destination_branch_amount = self.amount * (destination_branch_ratio / 100)
        # print (destination_branch_amount)

        if self.branch_id.sudo() != self.order_branch_id.sudo() and self.branch_id.sudo().company_id == self.order_branch_id.sudo().company_id:
            print ('-----DIFF BRANCH, SAME COMPANY')
            account_move_line.append((0, 0, {
                'account_id': actual_revenue_id,
                'partner_id': self.partner_id.id,
                'name': 'Actual Income',
                'analytic_account_id': self.order_branch_id.sudo().analytic_account_id.id,
                'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
                'company_id': self.order_branch_id.sudo().company_id.id,
                'debit': 0.0,
                'credit': source_branch_amount,
            }))
            account_move_line.append((0, 0, {
                'account_id': actual_revenue_id,
                'partner_id': self.partner_id.id,
                'name': 'Actual Income',
                'analytic_account_id': self.branch_id.sudo().analytic_account_id.id,
                'operating_unit_id': self.branch_id.sudo().operating_branch_id.id,
                'company_id': self.branch_id.sudo().company_id.id,
                'debit': 0.0,
                'credit': destination_branch_amount,
            }))
            # add update amount bybook
            self.update({'source_branch_amount': source_branch_amount,
                         'destination_branch_amount': destination_branch_amount, })

        if self.branch_id.sudo() != self.order_branch_id.sudo() and self.branch_id.sudo().company_id != self.order_branch_id.sudo().company_id:
            ########## At source company
            print ('-----DIFF BRANCH and DIFF COMPANY') ######## NEED TO DO SOMETHING MORE
            journal_id = journal_original_id
            account_move_line.append((0, 0, {
                'account_id': actual_revenue_id,
                'partner_id': self.partner_id.id,
                'name': 'Actual Income',
                'analytic_account_id': self.order_branch_id.sudo().analytic_account_id.id,
                'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
                'company_id': self.order_branch_id.sudo().company_id.id,
                'debit': 0.0,
                'credit': source_branch_amount,
            }))
            account_move_line.append((0, 0, {
                'account_id': self.with_context(force_company=self.order_branch_id.sudo().company_id.id).order_branch_id.sudo().company_id.partner_id.property_account_payable_id.id,
                'partner_id': self.branch_id.sudo().company_id.partner_id.id,
                'name': self.branch_id.sudo().name,
                'analytic_account_id': self.order_branch_id.sudo().analytic_account_id.id,
                'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
                'company_id': self.order_branch_id.sudo().company_id.id,
                'debit': 0.0,
                'credit': destination_branch_amount,
            }))
            ########## At destination company
            # add update amount bybook
            self.update({'source_branch_amount': source_branch_amount,
                         'destination_branch_amount': destination_branch_amount, })

        # print ('------MOVE LINE')
        # print (account_move_line)

        move_val = {'ref': self.name,
             'journal_id': journal_id,
             'date': datetime.datetime.today(),
             'company_id': self.order_branch_id.sudo().company_id.id,
             'line_ids': account_move_line,
             }
        # print (move_val)
        account_move = self.env['account.move'].sudo().create(move_val)
        # print ('---NUMBER---')
        # print (account_move.number)
        return account_move.post()

    @api.multi
    def create_reverse_wallet_entry(self):
        journal_id = self.env['account.journal'].search([('code', '=', 'WRJ'),('company_id', '=', self.branch_id.company_id.id)],limit=1).id
        wallet_expense_account = self.env['car.settings'].search([]).wallet_expense_account_id.id
        if not wallet_expense_account:
            raise UserError(_('Please configure the wallet expense account in settings'))
        if self.partner_id.property_account_receivable_id.id:
            partner_journal = self.partner_id.property_account_receivable_id.id
        else:
            partner_journal = self.partner_id.parent_id.property_account_receivable_id.id
        ratio = self.env['car.settings'].search([]).wallet_ratio
        amount = self.amount * (ratio / 100)
        print ('------CREATE REVERSE--')
        print (self.name)
        print (journal_id)
        print (partner_journal)
        if journal_id != False:
            account_move = self.env['account.move'].sudo().create(
                {'ref': self.name,
                 'journal_id': journal_id,
                 'date': datetime.datetime.today(),
                 'line_ids': [(0, 0, {
                     'account_id': partner_journal,
                     'partner_id': self.partner_id.id,
                     'name': 'Reverse Credit',
                     'debit': 0.0,
                     'credit': amount,
                 }), (0, 0, {
                     'account_id': wallet_expense_account,
                     'partner_id': self.partner_id.id,
                     'name': 'Reverse Credit',
                     'debit': amount,
                     'credit': 0.0,
                 })]
                 })
            return account_move.post()

    # def request_redeem_new(self, couponIds=None):
    #     # for app
    #
    #     for record in couponIds:
    #         rec = self.browse(record)
    #         rec.redeem_request_date = date.today()
    #         rec.state = 'redeem_request'
    #
    #     return [{
    #             'message': 'success'
    #             }]

    # def request_redeem(self):
    #     self.redeem_request_date = date.today()
    #     self.state = 'redeem_request'

    # def cancel_redeem(self, couponIds):
    #     # for app
    #
    #     for record in couponIds:
    #         rec = self.browse(record)
    #         rec.redeem_request_date = False
    #         rec.redeem_date = False
    #         rec.state = 'draft'
    #
    #     return [{
    #         'message': 'success'
    #     }]

