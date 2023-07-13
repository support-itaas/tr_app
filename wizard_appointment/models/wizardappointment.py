# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
import json
from datetime import datetime

import pytz
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Appointment(models.Model):
    _name = "appointment.appointment"
    _description = 'Class Appointment'

    name = fields.Char(string="Name")
    branch_id = fields.Many2one('project.project', string='Branch', required=True)
    appointment_date = fields.Date(string='Appointment Date', required=True)
    type = fields.Selection([('coupon', 'Coupon'),
                             ('service', 'Service')
                             ], string='Type', default='coupon', required=True)
    coupon_no_id = fields.Many2one('wizard.coupon', string='Coupon Number')
    product_id = fields.Many2one('product.product', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('approve', 'Approve'),
                              ('reject', 'Reject'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')
                              ], string='Status', default="draft")
    slot_id = fields.Many2one('appointment.slot', string='Slot', required=True)
    from_date = fields.Datetime(string='From Date', compute='_compute_date', index=True, store=True)
    to_date = fields.Datetime(string='To Date', compute='_compute_date', store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('wizard.appointment.sequence') or _('New')
        branch = self.env['project.project'].browse(vals.get('branch_id'))
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        notification = self.env['wizard.notification'].create({
            'name': 'Appointment' + ' ' + 'created',
            'message': 'Dear Sir/Madam,' + '\n' + 'Your appointment' + ' (' + vals.get(
                'name') + ')' + ' is created on' + ' ' + vals.get(
                'appointment_date') + ' ' + 'at' + ' ' + branch.name + ' ' + 'for' + ' ' + vals.get('type'),
            'read_message': False,
            'partner_id': partner.id,
            'message_at': fields.Datetime.now(),
        })
        if partner.device_token:
            serverToken = self.env['car.settings'].sudo().search([]).server_token
            # serverToken = self.env['car.settings'].sudo().get_param('server_token') or False
            deviceToken = partner.device_token
            notifications = self.env['wizard.notification'].search([('partner_id', '=', partner.id),
                                                                    ('read_message', '=', False)])
            if serverToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Appointment Created',
                                     'body': 'Dear Sir/Madam,' + '\n' + 'Your appointment' + ' (' + vals.get(
                    'name') + ')' + ' is created on' + ' ' + vals.get(
                    'appointment_date') + ' ' + 'at' + ' ' + branch.name + ' ' + 'for' + ' ' + vals.get('type'),
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))

        return super(Appointment, self).create(vals)

    @api.multi
    @api.depends('appointment_date', 'slot_id')
    def _compute_date(self):
        tz_name = self._context.get('tz') or self.env.user.tz
        local = pytz.timezone(tz_name)
        if self.appointment_date and self.slot_id:
            from_time = self.slot_id.from_time
            from_time_converted = '{0:02.0f}:{1:02.0f}'.format(*divmod(from_time * 60, 60))
            appointment_date_str = str(self.appointment_date)
            date_time_str = (appointment_date_str + ' ' + from_time_converted)
            date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
            local_dt = local.localize(date_time_obj, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            self.from_date = utc_dt

            to_time = self.slot_id.to_time
            to_time_converted = '{0:02.0f}:{1:02.0f}'.format(*divmod(to_time * 60, 60))
            date_to_time_str = (appointment_date_str + ' ' + to_time_converted)
            date_to_time_obj = datetime.strptime(date_to_time_str, '%Y-%m-%d %H:%M')
            local_to_dt = local.localize(date_to_time_obj, is_dst=None)
            utc_to_dt = local_to_dt.astimezone(pytz.utc)
            self.to_date = utc_to_dt

    @api.multi
    def action_confirm(self):
        self.state = 'confirm'
        notification = self.env['wizard.notification'].create({
            'name': 'Appointment' + ' ' + 'confirmed',
            'message': 'Dear Sir/Madam,' + '\n' + 'Your appointment' + ' (' + self.name + ')' + ' is confirmed' + ' ' + 'at' + ' ' + self.branch_id.name + ' ' + 'for' + ' ' + self.type,
            'read_message': False,
            'partner_id': self.partner_id.id,
            'message_at': fields.Datetime.now(),
        })
        if self.partner_id.device_token:
            serverToken = self.env['car.settings'].sudo().search([]).server_token
            # serverToken = self.env['car.settings'].sudo().get_param('server_token') or False
            deviceToken = self.partner_id.device_token
            notifications = self.env['wizard.notification'].search([('partner_id', '=', self.partner_id.id),
                                                                    ('read_message', '=', False)])
            if serverToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Appointment confirmed',
                                     'body': 'Dear Sir/Madam,' + '\n' + 'Your appointment' + ' (' + self.name + ')' + ' is confirmed' + ' ' + 'at' + ' ' + self.branch_id.name + ' ' + 'for' + ' ' + self.type,
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications)},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))

    @api.multi
    def action_approve(self):
        appointments = self.env['appointment.appointment'].search(
            [('partner_id', '!=', self.partner_id.id)])
        for appointment in appointments:
            if appointment.slot_id == self.slot_id:
                raise UserError(_('You cannot use this slot'))
        self.state = 'approve'

    @api.multi
    def action_reject(self):
        self.state = 'reject'
        notification = self.env['wizard.notification'].create({
            'name': 'Appointment' + ' ' + 'Reject',
            'message': 'Dear Sir/Madam,' + '\n' + 'เนื่องจากบริการที่ท่านนัดหมาย ได้ถูกจองเต็มแล้ว ทางร้านของแจ้งให้ท่านทราบว่า' 
                       '\n' + 'Your appointment' + ' (' + self.name + ')' + ' is reject' + ' ' + 'at' + ' ' + self.branch_id.name + ' ' + 'for' + ' ' + self.type,
            'read_message': False,
            'partner_id': self.partner_id.id,
            'message_at': fields.Datetime.now(),
        })
        if self.partner_id.device_token:
            serverToken = self.env['car.settings'].sudo().search([]).server_token
            deviceToken = self.partner_id.device_token
            notifications = self.env['wizard.notification'].search([('partner_id', '=', self.partner_id.id),
                                                                    ('read_message', '=', False)])
            if serverToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Appointment Rejected',
                                     'body': 'Dear Sir/Madam,' + '\n' + 'เนื่องจากบริการที่ท่านนัดหมาย ได้ถูกจองเต็มแล้ว ทางร้านของแจ้งให้ท่านทราบว่า' 
                           '\n' + 'Your appointment' + ' (' + self.name + ')' + ' is reject' + ' ' + 'at' + ' ' + self.branch_id.name + ' ' + 'for' + ' ' + self.type,
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'
        notification = self.env['wizard.notification'].create({
            'name': 'Appointment' + ' ' + 'Cancel',
            'message': 'Dear Sir/Madam,' + '\n' + 'เนื่องจากบริการที่ท่านนัดหมาย ได้ถูกจองเต็มแล้ว ทางร้านของแจ้งให้ท่านทราบว่า'
                                                  '\n' + 'Your appointment' + ' (' + self.name + ')' + ' is cancel' + ' ' + 'at' + ' ' + self.branch_id.name + ' ' + 'for' + ' ' + self.type,
            'read_message': False,
            'partner_id': self.partner_id.id,
            'message_at': fields.Datetime.now(),
        })
        if self.partner_id.device_token:
            serverToken = self.env['car.settings'].sudo().search([]).server_token
            deviceToken = self.partner_id.device_token
            notifications = self.env['wizard.notification'].search([('partner_id', '=', self.partner_id.id),
                                                                    ('read_message', '=', False)])
            if serverToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

                body = {
                    'notification': {'title': 'Appointment Canceled',
                                     'body': 'Dear Sir/Madam,' + '\n' + 'เนื่องจากบริการที่ท่านนัดหมาย ได้ถูกจองเต็มแล้ว ทางร้านของแจ้งให้ท่านทราบว่า'
                                                      '\n' + 'Your appointment' + ' (' + self.name + ')' + ' is cancel' + ' ' + 'at' + ' ' + self.branch_id.name + ' ' + 'for' + ' ' + self.type,
                                     'badge': len(notifications),
                                     "click_action": "FCM_PLUGIN_ACTIVITY"
                                     },
                    'to':
                        deviceToken,
                    'priority': 'high',
                    'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))

    @api.onchange('type', 'branch_id')
    def onchange_slot_id(self):
        slot_list = []
        slots = self.env['appointment.slot']
        if self.type == 'coupon':
            slots = self.env['appointment.slot'].search(
                [('active', '=', True),('type', '=', 'coupon'), ('branch_id', '=', self.branch_id.id)])
        elif self.type == 'service':
            slots = self.env['appointment.slot'].search(
                [('active', '=', True),('type', '=', 'service'), ('branch_id', '=', self.branch_id.id)])
        if slots:
            for slot in slots:
                slot_list.append(slot.id)
        res = {'domain': {'slot_id': [('id', 'in', slot_list)]}}
        return res

    @api.onchange('type')
    def onchange_product_id(self):
        product_list = []
        products = self.env['product.product']
        if self.type == 'coupon':
            products = self.env['product.product'].search([('is_coupon', '=', True)])
        elif self.type == 'service':
            products = self.env['product.product'].search([('is_service', '=', True)])
        if products:
            product_list.extend(products.ids)
        res = {'domain': {'product_id': [('id', 'in', product_list)]}}
        return res

    def check_appointment_slot(self, type, product_id, request_date, branch_id):
        # app
        result = []
        slots = self.env['appointment.slot'].search(
            [('type', '=', type), ('product_id', '=', product_id), ('branch_id', '=', branch_id)])
        if slots:
            for slot in slots:
                alter_branch = []
                new_alter = []
                alternative = self.env['appointment.slot'].search(
                    [('from_time', '=', slot.from_time), ('to_time', '=', slot.to_time),
                     ('branch_id', '!=', slot.branch_id.id), ('type', '=', slot.type),
                     ('product_id', '=', slot.product_id.id)])
                if alternative:
                    alter_branch = alternative.mapped('branch_id')
                appts = self.search(
                    [('appointment_date', '=', request_date), ('slot_id', '=', slot.id), ('type', '=', slot.type),
                     ('product_id', '=', slot.product_id.id), ('state', '=', 'approve')])
                if appts:
                    for appt in appts:
                        if appt.branch_id in alter_branch:
                            alter_branch.remove(appt.branch_id)
                        if alter_branch:
                            for val in alter_branch:
                                new_alter.append({
                                    'branchId': val.id,
                                    'branchName': val.name
                                })
                        if appt.branch_id == slot.branch_id:
                            result.append(
                                {"id": slot.id, "from_time": slot.from_time, "to_time": slot.to_time,
                                 "branch": slot.branch_id.id, "status": "Not Available",
                                 "alternative_branches": new_alter})

                        elif appt.branch_id != slot.branch_id:
                            result.append(
                                    {"id": slot.id, "from_time": slot.from_time, "to_time": slot.to_time,
                                     "branch": slot.branch_id.id, "status": "Available",
                                     "alternative_branches": new_alter})
                else:
                    if alter_branch:
                        for val in alter_branch:
                            new_alter.append({
                                'branchId': val.id,
                                'branchName': val.name
                            })
                    result.append(
                            {"id": slot.id, "from_time": slot.from_time, "to_time": slot.to_time,
                             "branch": slot.branch_id.id,
                             "status": "Available", "alternative_branches": new_alter})
            return result

        else:
            return {"status": "No slots allotted"}


class AppointmentSlot(models.Model):
    _name = "appointment.slot"
    _description = 'Class Appointment Slot'

    name = fields.Char(string="Slot Name")
    branch_id = fields.Many2one('project.project', string='Branch', required=True)
    from_time = fields.Float(string='From Time', required=True)
    to_time = fields.Float(string='To Time', required=True)
    type = fields.Selection([('service', 'Service'), ('coupon', 'Coupon')], 'Type', default='service', required=True)
    product_id = fields.Many2one('product.product', required=True)
    active = fields.Boolean(string='Active',default=True)

    @api.multi
    def name_get(self):
        result = []
        for move in self:
            from_time = move.from_time
            converted_from_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(from_time * 60, 60))
            to_time = move.to_time
            converted_to_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(to_time * 60, 60))
            slot_name = (converted_from_time + '-' + converted_to_time)
            result.append((move.id, slot_name))
        return result

    @api.onchange('type')
    def onchange_product_id(self):
        product_list = []
        products = self.env['product.product']
        if self.type == 'coupon':
            products = self.env['product.product'].search([('is_coupon', '=', True)])
        elif self.type == 'service':
            products = self.env['product.product'].search([('is_service', '=', True)])
        if products:
            product_list.extend(products.ids)
        res = {'domain': {'product_id': [('id', 'in', product_list)]}}
        return res
