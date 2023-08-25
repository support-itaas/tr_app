# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
import json
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
# import datetime
import requests

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from pytz import timezone, utc
import pytz
import threading



class WizardCoupon(models.Model):
    _name = 'wizard.coupon'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Coupon'
    _order = 'expiry_date asc,id asc'

    name = fields.Text(readonly=True, required=True, copy=False, default=lambda x: _('New'))
    package_id = fields.Many2one('product.product', string="Package")
    product_id = fields.Many2one('product.product', required=True, string="Coupon")
    product_package_id_line_id = fields.Many2one('')
    branch_id = fields.Many2one('project.project', string="Redeemed Branch")
    date_order = fields.Date(string="Order Date")
    order_branch_id = fields.Many2one('project.project', required=False, string="Purchase At",track_visibility='onchange')
    purchase_date = fields.Date(required=True, default=datetime.datetime.today())
    expiry_date = fields.Date(string="Expiry Date", readonly=True, compute="compute_expiry_date", store="True",track_visibility='onchange')
    # state = fields.Selection([('draft', 'Available'), ('redeem_request', 'Redeem Requested'),
    #                           ('redeem', 'Redeemed'), ('expire', 'Expired')], string='state',
    #                          default='draft')
    state = fields.Selection([('draft', 'Available'), ('redeem', 'Redeemed'), ('expire', 'Expired')], string='state',
                             track_visibility='onchange',default='draft')
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
    active = fields.Boolean(default=True,track_visibility='onchange')
    order_id = fields.Many2one('pos.order', string="Order_Id")
    session_id = fields.Many2one('pos.session',string='Session ID',related='order_id.session_id',store=True)
    coupon_code = fields.Char(related='product_id.default_code', string='Coupon Code')
    is_promotional_pkg = fields.Boolean(related='package_id.is_promotional_pkg', string='Is Promotional Package', default=False)
    #--------------------------------------------
    source_operating_unit_id = fields.Many2one('operating.unit',related='order_branch_id.operating_branch_id', string="Source Operating Unit")
    source_branch_amount = fields.Float("Source Branch Amount", digits=dp.get_precision('Amount'))
    destination_operating_unit_id = fields.Many2one('operating.unit',related='branch_id.operating_branch_id', string="Destination Operating Unit")
    destination_branch_amount = fields.Float("Destination Branch Amount", digits=dp.get_precision('Amount'))
    #########################################
    # session_id = fields.Many2one('pos.session', string='Session')
    coupon_running = fields.Char(readonly=True, required=True, copy=False, default=lambda x: _('New'))
    # redeem_request_date = fields.Date(string='Redeem Requested Date')
    revenue_to_branch = fields.Boolean(string='รายได้เข้าสาขาอย่างเดียว', default=False)
    is_cross_claim = fields.Boolean(string='เคลมระหว่างสาขา',compute='get_cross_claim',store=True)
    move_id = fields.Many2one('account.move',string='Accounting Record')
    # branch_amount = fields.Float(string="Branch Amount", compute='_compute_branch_amount')
    branch_amount = fields.Float(string="Branch Amount",)
    branch_amount2 = fields.Float(string="Branch Amount",)
    picking_id = fields.Many2one('stock.picking',string='Picking')
    task_id = fields.Many2one('project.task',string='Task')
    # branch_amount_total = fields.Float(string="Branch Amount Total",)

    available_branch = fields.Many2many('operating.unit', string='Available Branch')

    @api.depends('destination_branch_amount','source_branch_amount', 'branch_id', 'session_id')
    def _compute_branch_amount(self):
        print("testtttttttt")
        for obj in self:
            print("session_id;",obj.sudo().session_id.config_id.branch_id.name)
            print("order_branch_id;",obj.sudo().order_branch_id.name)
            print("branch_id;",obj.sudo().branch_id.name)

            # if obj.sudo().order_branch_id.name != obj.sudo().session_id.config_id.branch_id.name and obj.sudo().branch_id.name == obj.sudo().session_id.config_id.branch_id.name:
            #     print("aaaaaa")
            #     obj.branch_amount = obj.destination_branch_amount
            # if obj.sudo().order_branch_id.name == obj.sudo().session_id.config_id.branch_id.name and obj.sudo().branch_id.name != obj.sudo().session_id.config_id.branch_id.name:
            #     print("bbbbbb")
            #     obj.branch_amount = obj.source_branch_amount * -1
            # else:
            #     obj.branch_amount = obj.destination_branch_amount
            # print("branch_amount:",obj.branch_amount)

    @api.depends('branch_id','order_branch_id','state')
    def get_cross_claim(self):
        for coupon in self:
            if coupon.branch_id and coupon.order_branch_id and coupon.state == 'redeem' and coupon.branch_id != coupon.order_branch_id:
                coupon.is_cross_claim = True
            else:
                coupon.is_cross_claim = False

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
            'description': res.product_id.description_sale,
            'available_branch': [(6, 0, [b.id for b in res.package_id.sudo().available_branch])],
        })


        return res

    # def write(self, vals):
    #     for coupon in self:
    #         lock_date = max(self.env.user.company_id.period_lock_date, self.env.user.company_id.fiscalyear_lock_date)
    #         if lock_date and ('order_branch_id' in vals or 'active' in vals or 'purchase_date' in vals) and coupon.purchase_date <= lock_date:
    #             message = _("ไม่สามารถเปลี่ยนแปลงรายการของคูปองที่ขายก่อนวันที่ %s") %(lock_date)
    #             raise UserError(message)
    #     return super(WizardCoupon,self).write(vals)




    @api.multi
    def copy(self, default=None):
        context = self._context
        # print (context.get('allow_copy'))
        if not context.get('allow_copy'):
            raise UserError(_('Duplicating coupon is not allowed.'))
        else:
            # print ("GO HERE")
            return super(WizardCoupon, self).copy(default=default)



    @api.multi
    def unlink(self):
        for coupon in self:
            if coupon.state in ['redeem', 'expire']:
                raise UserError(_('You cannot delete this coupon'))
        return super(WizardCoupon, self).unlink()

    @api.multi
    def button_cancel(self):
        for coupon_id in self:
            coupon_id.redeem_date = False
            coupon_id.branch_id = False
            coupon_id.plate_number_id = False
            coupon_id.state = 'draft'

            journal = self.env['account.move'].search([('ref', '=', coupon_id.name)], limit=1)
            task_id = self.env['project.task'].sudo().search([('coupon_id', '=', coupon_id.id),('state', '!=', 'cancel')], limit=1)
            if journal:
                if not journal.journal_id.update_posted:
                    raise UserError(_('Please allow cancelling entries in journal settings'))
                else:
                    journal.button_cancel()
                    journal.unlink()

            if task_id:
                cancel_state_id = self.env['project.task.type'].sudo().search([('name', 'in', ('Cancel', 'cancel'))], limit=1)
                task_id.write({'state': 'cancel'})
                task_id.write({'stage_id': cancel_state_id.id})
                if task_id.picking_id and task_id.picking_id.state != 'done':
                    task_id.picking_id.action_cancel()
                elif task_id.picking_id and task_id.picking_id.state == 'done':
                    raise UserError(_('ระบบได้ตัดสต๊๊อกน้ำยาสำหรับบริการไปแล้ว ให้ทำการยลิก Task และ Return การตัด Stock ด้วยตนเอง'))

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
                if coupon.package_id.is_limit_branch and coupon.package_id.available_branch:
                    allow_branch_text = ''
                    count = 0
                    for branch_id in coupon.package_id.available_branch:
                        count +=1
                        if count == len(coupon.package_id.available_branch):
                            allow_branch_text += branch_id.name
                        else:
                            allow_branch_text += branch_id.name + ','
                    coupon_name = coupon.name + ' [ เฉพาะสาขา ' + allow_branch_text + ' ] '
                else:
                    coupon_name = coupon.name

                coupon_vals = {'id': coupon.id,
                               'name': coupon_name,
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

            # if rec.available_branch:
            #
            #
            date_redeem = rec.redeem_date or order_date
            if (plate_id is not None) and (not isinstance(plate_id, dict)):
                rec.plate_number_id = plate_id
            elif not rec.plate_number_id:
                raise UserError(_('Please choose the Plate Number'))
            if branch_id is not None and (not isinstance(branch_id, dict)):
                rec.branch_id = branch_id
            elif not rec.branch_id and branch_id is None:
                raise UserError(_('Please select the branch'))

            if rec.available_branch.sudo() and rec.branch_id.operating_branch_id.id not in rec.available_branch.ids:
                raise UserError(_('Coupon is not allowed to redeem this branch'))

            # elif self.product_id.is_limit_branch == True:
            #     if self.branch_id.operating_branch_id.id not in self.product_id.available_branch.ids:
            #         raise UserError(_('Redeem ผิดสาขากรุณาตรวจสอบอีกครั้ง'))

            # if (order_date is not None) and (not isinstance(order_date, dict)):
            #     rec.order_date = order_date
            # elif not rec.order_date:
            #     raise UserError(_('Please choose the Order Date'))
            ##############Add this condition for create or not create a task for each coupon#######
            # still create task but change state to 'Done' auto
            if rec.plate_number_id:
                existing_task_id = self.env['project.task'].sudo().search([('coupon_id','=',rec.id),('state','!=','cancel')],limit=1)
                if existing_task_id:
                    task = existing_task_id
                else:
                    task = self.env['project.task'].with_context(tracking_disable=True).create({
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

                rec.task_id = task.id

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

                    # send message if quick move to done due to no start, stop, otherwsie no message.

                    tz = pytz.timezone(self.env.user.tz)
                    # 'message': 'Coupon number ' + rec.name + ' redeemed at ' + rec.branch_id.name + ' for plate number ' +
                    # rec.plate_number_id.name + ' on ' + str(
                    #     fields.datetime.today().astimezone(tz).strftime('%Y-%m-%d %H:%M')),
                    #
                    operate_time = fields.datetime.today() + relativedelta(hours=7)
                    operate_time = operate_time.strftime('%Y-%m-%d %H:%M')
                    notification = self.env['wizard.notification'].create({
                        'name': 'Coupon number ' + rec.name + ' has been used',
                        'message': 'Coupon number ' + rec.name + ' redeemed at ' + rec.branch_id.name + ' for plate number ' +
                                   rec.plate_number_id.name + ' on ' + str(operate_time),
                        'read_message': False,
                        'partner_id': rec.partner_id.id,
                        'message_at': fields.Datetime.now(),
                    })

                    if rec.partner_id.device_token:
                        serverToken = self.env['car.settings'].sudo().search([]).server_token
                        deviceToken = rec.partner_id.device_token
                        notifications = self.env['wizard.notification'].search([('partner_id', '=', rec.partner_id.id),
                                                                                ('read_message', '=', False)])
                        if serverToken:
                            headers = {
                                'Content-Type': 'application/json',
                                'Authorization': 'key=' + serverToken,
                            }

                            body = {
                                'notification': {'title': 'Your order is created',
                                                 'body': 'Coupon number ' + rec.name + ' redeemed at ' + rec.branch_id.name + ' for plate number ' +
                                                         rec.plate_number_id.name + ' on ' + str(date.today()),
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

            ########This may make cross branch use coupon issue
            #remove redeem process and set schedule instead 05/09/2021
            # rec.create_actual_revenue()

            if not rec.redeem_date and order_date:
                print('==================')
                rec.redeem_date = order_date
            elif not rec.redeem_date and not order_date:
                print('xxxxxxxxxxxxxxxxxxxxxx')
                rec.redeem_date = date.today()

            ########This may make cross branch use coupon issue
            # remove redeem process and set schedule instead 05/09/2021
            # rec.create_picking()
            ########

            rec.state = 'redeem'

            if not rec.revenue_to_branch:
                source_branch_ratio = self.env['car.settings'].sudo().search([]).source_branch_ratio
                source_branch_amount = round(rec.amount * (source_branch_ratio / 100), 2)
                destination_branch_amount = round(rec.amount - source_branch_amount, 2)
            else:
                source_branch_amount = 0
                destination_branch_amount = rec.amount

            rec.update({'source_branch_amount': source_branch_amount,
                          'note': 'redeem-amount',
                         'destination_branch_amount': destination_branch_amount, })


            # print('rec.redeem_date : ',rec.redeem_date)
            # print('order_date : ',order_date)

            # if not rec.redeem_date and order_date:
            #     print('==================')
            #     rec.redeem_date = order_date
            # elif not rec.redeem_date and not order_date:
            #     print('xxxxxxxxxxxxxxxxxxxxxx')
            #     rec.redeem_date = date.today()

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
            usererror_message = ''
            # picking_id = Picking.sudo().search([('coupon_id', '=', coupon.id)], limit=1)
            # print('Coupon Picking exits : ',picking_id)
            # if picking_id:
            #     continue
            #################################
            # 1) change ---> company by redeem branch
            # 2) chnage ---> location ---> stock remove
            # 3) change ---> customer location
            company_id = coupon.branch_id.sudo().company_id.id
            pos_config = self.env['pos.config'].sudo().search([('branch_id', '=', coupon.branch_id.id)], limit=1, order='id desc')
            if not pos_config:
                continue
                # usererror_message += 'There is not POS for redeeming Branch. Please configure one. \n'
                # raise UserError(_('There is not POS for redeeming Branch. Please configure one.: %s') % (self.name))
            else:
                location_id = pos_config.stock_location_id.id
            #################################
            product = coupon.product_id.related_service_id
            # print ('coupon product_id :', coupon.product_id)
            # print ('related_service_id :', product)

            if not product:
                continue
                # usererror_message += 'Please configure related service to coupon product. \n'
                # raise UserError(_('Please configure related service to coupon product.: %s') % (self.name))

            # if coupon.order_id:
            #     pos_order = self.env['pos.order'].search([('id', '=', coupon.order_id.id)])
            # else:
            #     pos_order = False

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
            # print('address delivery :', address)
            picking_type = pos_config.picking_type_id
            # print('picking_type :',picking_type)
            order_picking = Picking
            return_picking = Picking
            moves = Move

            if coupon.partner_id:
                destination_id = coupon.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id
            # print('destination location :', destination_id)

            if picking_type:
                message = _("This transfer has been created from coupons: <a href=# data-oe-model=wizard.coupon data-oe-id=%d>%s</a>") % (coupon.id, coupon.name)
                picking_vals = {
                    'coupon_id':coupon.id,
                    'origin': coupon.name,
                    'partner_id': address.get('delivery', False),
                    'date_done': coupon.redeem_date,
                    'picking_type_id': picking_type.id,
                    'company_id': company_id,
                    'move_type': 'direct',
                    'note': coupon.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                    'force_date':coupon.redeem_date,
                    'scheduled_date': coupon.redeem_date,
                }

                # print('company_id : ', coupon.partner_id.company_id.name)
                # print('picking_vals : ', picking_vals)
                if product.type in ['product', 'consu']:
                    order_picking = Picking.sudo().create(picking_vals.copy())
                    order_picking.message_post(body=message)
            # print('order_picking : ', order_picking)

            qty = 1
            if product.type in ['product', 'consu'] and not float_is_zero(qty, precision_rounding=product.uom_id.rounding):
                move_val = {
                    'name': coupon.name,
                    'product_uom': product.uom_id.id,
                    'picking_id': order_picking.id,
                    'picking_type_id': picking_type.id,
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'quantity_done': qty,
                    'company_id': company_id,
                    'state': 'draft',
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                    'date': coupon.redeem_date,
                }
                # print('move_val :', move_val)
                moves |= Move.sudo().create(move_val)
            # print('create moves :', moves)

            coupon.write({'picking_id': order_picking.id})
            #Udpate picking to task#remove ส่วนนี้ชั่วคราวเนื่องจากตอนนี้ที่ coupon มี picking แล้ว ก็อาจจะไม่จำเป็นต้องมี picking ที่ task อีก
            if coupon.task_id:
                task_id.write({'picking_id': order_picking.id})
            else:
                task_id = self.env['project.task'].sudo().search([('coupon_id', '=', coupon.id),
                                                                  ('state', '!=', 'cancel')], limit=1)
                if task_id and order_picking:
                    task_id.write({'picking_id': order_picking.id})
                # print('task_id :',task_id)
            # Udpate picking to task

            order_picking.sudo().action_confirm()
            order_picking.sudo().action_assign()
            # print('order_picking move_line_ids :', order_picking.sudo().move_line_ids)
            # print('order_picking state :', order_picking.sudo().state)
            # print('order_picking name :', order_picking.sudo().name)

            #ไม่จำเป็นต้องรอ task done ก็จัดการสร้างได้เลย, เนื่องจากเป้นการทำย้อนหลังอยู่แล้ว เลยไม่ต้องเช็ค task
            # if order_picking.sudo().state == 'assigned' and task_id and task_id.state == 'done' and order_picking.sudo().move_line_ids:

            if order_picking.sudo().state == 'assigned' and order_picking.sudo().move_line_ids:
                order_picking.sudo().force_assign()
                if order_picking.sudo().move_line_ids and order_picking.sudo().state == 'assigned':
                    # for move_line in order_picking.sudo().move_line_ids:
                        # print('product ',move_line.product_id)
                        # print('product_uom_qty ',move_line.product_uom_qty)
                        # print('qty_done ',move_line.qty_done)
                        # print('lot ',move_line.lot_id)
                    order_picking.sudo().button_validate()
                    # order_picking.picking_immediate_process()
                    coupon.picking_immediate_process(order_picking)

            # if usererror_message:
            #     coupon.message_post(body=usererror_message)

        return True

    def picking_immediate_process(self, picking_id):
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        for picking in picking_id:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            if picking._check_backorder():
                pick_to_backorder |= picking
                continue
            pick_to_do |= picking
        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
        if pick_to_do:
            pick_to_do.action_done()
        if pick_to_backorder:
            return pick_to_backorder.action_generate_backorder_wizard()
        return False

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
            coupon.branch_id = coupon.order_branch_id.id
            coupon.redeem_date = coupon.expiry_date
            coupon.create_actual_revenue()

            # if not coupon.branch_id:
            #     coupon.branch_id = coupon.order_branch_id.id
            #     coupon.redeem_date = coupon.expiry_date
            # if coupon.branch_id:
            #     # print ('ST-1-2')
            #     coupon.create_actual_revenue()
            # elif coupon.order_branch_id:
            #     # print ('ST-1-3')
            #     coupon.create_actual_revenue()

            # print ('ST-2')
            # remove coupon expire function
            # coupon.create_reverse_wallet_entry()
            # print ('-revese to wallet')
            coupon.state = 'expire'

    @api.multi
    def redeem_coupon_scheduler(self, max_coupon=0, previous_day=0,com_id=0):
        if previous_day:
            previous_date = date.today() - relativedelta(days=previous_day)
        else:
            previous_date = '2021-01-01'

        if com_id:
            domain = [('redeem_date', '<=', date.today()),
                      ('redeem_date', '>=', previous_date),
                      ('amount', '!=', 0.0),
                      ('order_id', '!=', False),
                      ('state', '=', 'redeem'),
                      ('order_branch_id.company_id', '=', 1),
                      ('move_id', '=', False)]
        else:
            domain = [('redeem_date', '<=', date.today()),
                      ('redeem_date', '>=', previous_date),
                      ('amount', '!=', 0.0),
                      ('order_id', '!=', False),
                      ('state', '=', 'redeem'),
                      ('move_id', '=', False)]
        # print('redeem_coupon_scheduler domain', domain)

        if max_coupon:
            coupons = self.search(domain, limit=max_coupon, order='redeem_date')
        else:
            coupons = self.search(domain, order='redeem_date')

        txt = ''

        txt += 'All Coupon:' + str(len(coupons)) + '\r\n'
        start = str(fields.Datetime.now())
        for coupon in coupons:

            print ('COUPON:')
            print (coupon.name)
            if not coupon.branch_id.sudo():
                coupon.branch_id = coupon.order_branch_id.sudo().id

            # coupon.sudo().create_actual_revenue()

            try:
                coupon.sudo().create_actual_revenue()
                txt += 'Coupon:' + coupon.name + ':Done' + '\r\n'
            #     # Move to Create Picking Coupon Scheduler ----
            #     # if coupon.state == 'redeem':
            #     #     coupon.sudo().create_picking()
            #     # --------------------------------------------
            #     # threaded_redeem = threading.Thread(target=coupon.sudo().actual_revenue(), args=())
            #     # threaded_redeem.start()
            #     # coupon.sudo().actual_revenue()
            except:
                # print ('EXCEPT:')
                # print (coupon.name)
                txt += 'Coupon:' + coupon.name + ':Error' + '\r\n'
                continue
        val = {
            'start': 'redeem_coupon_scheduler',
            'ava_time': start,
            'expire_time': str(fields.Datetime.now()),
            'total_time':txt,
        }
        self.env['wizard.log'].create(val)

    # threaded_calculation = threading.Thread(target=self._procure_calculation_orderpoint, args=())
    # threaded_calculation.start()
    # return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def expire_coupon_scheduler(self, max_coupon=0):
        # print ('MAX--')
        # print (max_coupon)
        # print (self.env.user.company_id.name)
        if max_coupon:
            coupons = self.search([('expiry_date', '<', date.today()),
                                   ('expiry_date', '>=', '2021-01-01'),
                                   ('state', 'not in', ('expire','redeem'))],limit=max_coupon)
        else:
            coupons = self.search([('expiry_date', '<', date.today()),
                                   ('expiry_date', '>=', '2021-01-01'),
                                   ('state', 'not in', ('expire','redeem'))])

        txt = ''
        txt += 'All Coupon:' + str(len(coupons)) + '\r\n'
        for coupon in coupons.sudo():
            # print ('COUPON:')
            # print (coupon.name)
            if not coupon.branch_id.sudo():
                coupon.branch_id = coupon.order_branch_id.sudo().id
            try:

                coupon.state = 'expire'
                txt += 'Coupon:' + coupon.name + ':Done' + '\r\n'
                # coupon.sudo().expire_coupon()
            except:
                # print ('EXCEPT:')
                # print (coupon.name)
                txt += 'Coupon:' + coupon.name + ':Error' + '\r\n'
                continue

        val = {
            'start': 'expire_coupon_scheduler',
            'total_time': txt,
        }
        self.env['wizard.log'].create(val)

    @api.multi
    def action_view_tasks(self):
        self.ensure_one()
        action = self.env.ref('project.action_view_task').read()[0]
        ###########Since change name from coupon number to coupon name, so change search from name to coupon_id
        action['domain'] = [('coupon_id', '=', self.id)]
        return action

    @api.multi
    def action_view_journal_entries(self):
        journals = self.env['account.move'].search([('id', '=', self.move_id.id)])
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
        usererror_message = ''
        self.ensure_one()


        print ('ACTUAL REVENUE ', self, self.name)
        if self.move_id.sudo():
            if not self.move_id.sudo().journal_id.update_posted:
                self.move_id.sudo().journal_id.update_posted= True
            self.move_id.sudo().button_cancel()
            self.move_id.sudo().unlink()

        if not self.amount or not self.order_id.sudo() or self.redeem_date < '2021-01-01':
            return False

        print ('STEP-1 : Find Pos config')
        if not self.env['pos.config'].sudo().search([('branch_id', '=', self.branch_id.id)]):
            usererror_message += 'Please configure the branch in POS settings. \n'
            raise UserError(_('Please configure the branch in POS settings. : %s') % (self.name))

        journal_id = self.env['pos.config'].sudo().search([('branch_id', '=', self.branch_id.id)], limit=1, order='id desc').journal_id.id
        print('STEP-2 : Find Pos config for journal', journal_id)
        journal_original_id = self.env['pos.config'].sudo().search([('branch_id', '=', self.order_branch_id.id)], limit=1, order='id desc').journal_id.id
        print ('STEP-3 : Find car settings')
        if not self.env['car.settings'].search([]):
            usererror_message += 'Please configure the actual revenue account in settings. \n'
            raise UserError(_('Please configure the actual revenue account in settings.: %s') % (self.name))

        actual_revenue_id = self.env['car.settings'].search([]).actual_revenue_id
        print ('STEP-4 : Find car settings for actual_revenue_id', actual_revenue_id)

        ########if real actual account set by product, otherwise will use global wide
        print('order_branch_id company ', self.order_branch_id.sudo().company_id, self.order_branch_id.sudo().company_id.name)
        print('actual_revenue_id company ', actual_revenue_id.sudo().company_id)
        if self.order_branch_id.sudo().company_id.id != actual_revenue_id.sudo().company_id.id:
            print('self.order_branch_id.company_id.id ',self.order_branch_id.sudo().company_id.id)
            actual_revenue_id = self.product_id.product_tmpl_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).actual_income_account_id
        print ('STEP-5 : Find Actual Income Account ', actual_revenue_id)
        print ('STEP-5 : Find Actual Income Account company ', actual_revenue_id.sudo().company_id)
        # raise UserError('test')
        if self.order_branch_id.sudo().company_id.id != actual_revenue_id.sudo().company_id.id:
            return False
            # raise UserError(_('Please, check Actual Income Account (%s) company (%s) in product (%s) : %s') % (actual_revenue_id.name, self.order_branch_id.sudo().company_id.name, self.product_id.display_name, self.name))
        actual_revenue_id = actual_revenue_id.id

        if self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().property_account_income_id:
            product_journal = self.product_id.product_tmpl_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().property_account_income_id
        elif not self.product_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().property_account_income_id and self.product_id.categ_id:
            product_journal = self.product_id.product_tmpl_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).categ_id.property_account_income_categ_id
        else:
            product_journal = self.product_id.product_tmpl_id.with_context(force_company=self.order_branch_id.sudo().company_id.id).categ_id.parent_id.property_account_income_categ_id

        if self.order_branch_id.sudo().company_id.id != product_journal.company_id.id:
            raise UserError(_('Please, check Category of Income Account (%s) company (%s) in product (%s) : %s') % (product_journal.name, self.order_branch_id.sudo().company_id.name, self.product_id.display_name, self.name))

        print ('STEP-6 : Find Category of Income Account ', product_journal)
        #############change operating unit from branch_id or order_branch_id
        product_journal = product_journal.id
        account_move_line = [(0, 0, {
            'account_id': product_journal,
            'partner_id': self.partner_id.id,
            'name': 'Product Income',
            'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
            'debit': self.amount,
            'company_id': self.order_branch_id.sudo().company_id.id,
            'credit': 0.0,
        })]

        print ('STEP-7')
        if self.branch_id.sudo() == self.order_branch_id.sudo():
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
            # print (product_journal)
            # print (self.branch_id.sudo().operating_branch_id.company_id.id)
            # print (account_move_line)
            # add update amount bybook
            self.update({'source_branch_amount': self.amount, })

        print ('STEP-8')
        if not self.revenue_to_branch:
            print("STEP-8 not self.revenue_to_branch")
            source_branch_ratio = self.env['car.settings'].sudo().search([]).source_branch_ratio
            print("source_branch_ratio:",source_branch_ratio)
            source_branch_amount = round(self.amount * (source_branch_ratio / 100),2)
            print("source_branch_amount:", source_branch_amount)
            destination_branch_ratio = self.env['car.settings'].sudo().search([]).destination_branch_ratio
            destination_branch_amount = round(self.amount - source_branch_amount,2)
        else:
            print("STEP-8 else")
            source_branch_amount = 0
            destination_branch_amount = self.amount

        print ('STEP-9 : DIFF BRANCH and SAME COMPANY')
        if self.branch_id.sudo() != self.order_branch_id.sudo() and self.branch_id.sudo().company_id == self.order_branch_id.sudo().company_id:
            print ('*STEP-9 : DIFF BRANCH and SAME COMPANY')
            if source_branch_amount:
                account_move_line.append((0, 0, {
                    'account_id': actual_revenue_id,
                    'partner_id': self.partner_id.id,
                    'name': 'Actual Income',
                    'analytic_account_id': self.order_branch_id.sudo().analytic_account_id.id,
                    'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
                    'company_id': self.order_branch_id.sudo().company_id.id,
                    'debit': 0.0,
                    'credit': round(source_branch_amount,2),
                }))
            if destination_branch_amount:
                account_move_line.append((0, 0, {
                    'account_id': actual_revenue_id,
                    'partner_id': self.partner_id.id,
                    'name': 'Actual Income',
                    'analytic_account_id': self.branch_id.sudo().analytic_account_id.id,
                    'operating_unit_id': self.branch_id.sudo().operating_branch_id.id,
                    'company_id': self.branch_id.sudo().company_id.id,
                    'debit': 0.0,
                    'credit': round(destination_branch_amount,2),
                }))
            # add update amount bybook
            print("dddddddddddddd",destination_branch_amount)
            print("ssssssssssssss",source_branch_amount)
            self.update({'source_branch_amount': source_branch_amount,
                         'destination_branch_amount': destination_branch_amount, })
        print ('STEP-10 : DIFF BRANCH and DIFF COMPANY')
        if self.branch_id.sudo() != self.order_branch_id.sudo() and self.branch_id.sudo().company_id != self.order_branch_id.sudo().company_id:
            print('*STEP-10 : DIFF BRANCH and DIFF COMPANY')
            ########## At source company
            ######## NEED TO DO SOMETHING MORE
            journal_id = journal_original_id
            account_move_line.append((0, 0, {
                'account_id': actual_revenue_id,
                'partner_id': self.partner_id.id,
                'name': 'Actual Income',
                'analytic_account_id': self.order_branch_id.sudo().analytic_account_id.id,
                'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
                'company_id': self.order_branch_id.sudo().company_id.id,
                'debit': 0.0,
                'credit': round(source_branch_amount,2),
            }))
            # print ('HERE00')

            account_id = self.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().branch_id.partner_id.property_claim_account_payable_id
            if not account_id:
                account_id = self.with_context(force_company=self.order_branch_id.sudo().company_id.id).sudo().order_branch_id.sudo().company_id.partner_id.property_account_payable_id
            account_move_line.append((0, 0, {
                'account_id': account_id.id,
                'partner_id': self.branch_id.sudo().partner_id.id,
                'name': self.branch_id.sudo().name,
                'analytic_account_id': self.order_branch_id.sudo().analytic_account_id.id,
                'operating_unit_id': self.order_branch_id.sudo().operating_branch_id.id,
                'company_id': self.order_branch_id.sudo().company_id.id,
                'debit': 0.0,
                'credit': round(destination_branch_amount,2),
            }))
            ########## At destination company
            # add update amount bybook
            self.update({'source_branch_amount': source_branch_amount,
                         'destination_branch_amount': destination_branch_amount, })

        move_val = {'ref': self.name,
                    'journal_id': journal_id,
                    'date': self.redeem_date or datetime.datetime.today(),
                    'company_id': self.order_branch_id.sudo().company_id.id,
                    'line_ids': account_move_line,
                    }
        print ('CREATE MOVE', move_val)
        account_move = self.env['account.move'].sudo().create(move_val)
        print ('account_move: ', account_move)
        self.move_id = account_move.sudo()
        # raise UserError(_('Test'))
        return account_move.sudo().post()

    @api.multi
    def create_reverse_wallet_entry(self):
        journal_id = self.env['account.journal'].search([('code', '=', 'WRJ'),('company_id', '=', self.order_branch_id.company_id.id)],limit=1).id
        # print ('create_reverse_wallet_entry')
        # print (self.order_branch_id.company_id)
        # print (self.env['car.settings'].with_context(force_company=self.order_branch_id.company_id.id).sudo().search([]).wallet_expense_account_id.company_id)
        wallet_expense_account = self.env['car.settings'].with_context(force_company=self.order_branch_id.company_id.id).sudo().search([]).wallet_expense_account_id.id

        if not wallet_expense_account:
            raise UserError(_('Please configure the wallet expense account in settings'))
        if self.partner_id.property_account_receivable_id.id:
            # print ('-XXX')
            # print (self.partner_id.with_context(force_company=self.order_branch_id.company_id.id).property_account_receivable_id.company_id)
            partner_journal = self.partner_id.with_context(force_company=self.order_branch_id.company_id.id).property_account_receivable_id.id
            # print (x)
        else:
            # print ('-YYY')
            # print (self.partner_id.parent_id.property_account_receivable_id.company_id)
            partner_journal = self.partner_id.with_context(force_company=self.order_branch_id.company_id.id).parent_id.property_account_receivable_id.id
        ratio = self.env['car.settings'].search([]).wallet_ratio
        amount = self.amount * (ratio / 100)
        # print ('------CREATE REVERSE--')
        # print (self.name)
        # print (journal_id)
        # print (partner_journal)
        # print (partner_journal)
        # print (wallet_expense_account)
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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    coupon_id = fields.Many2one('wizard.coupon', string='Coupon')