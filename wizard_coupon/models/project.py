# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
import json

import requests

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class Task(models.Model):
    _inherit = "project.task"

    coupon_id = fields.Many2one('wizard.coupon', string='Coupon', readonly=True)
    plate_number_id = fields.Many2one('car.details', string='Plate Number', readonly=True)
    amount = fields.Float("Amount", digits=dp.get_precision('Amount'))
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    public_price = fields.Float("Public Price", digits=dp.get_precision('Amount'))
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done'), ('cancel', 'Cancelled')],
        string='Status', default='draft', readonly=True)
    distance = fields.Float(string='เลขไมล์')
    car_detail = fields.Text(string='หมายเหตุ')
    car_remark_ids = fields.Many2many('car.remark', string='Remark')
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True, copy=False)
    car_clean = fields.Char('Car Clean')
    barcode = fields.Char('Barcode')

    @api.multi
    def cancel_service_app(self):
        if self.state != 'draft':
            raise UserError(_('Cannot cancel in this state'))
        else:
            self.button_cancel()
            return True

    @api.multi
    def button_deadline(self):
        print('button_deadline')
        print('xxxxx', self.coupon_id.redeem_date)
        coupon_ids = self.env['project.task'].search([('date_deadline', '=', False)])
        print('coupon_ids', coupon_ids)
        for coupon_id in coupon_ids:
            coupon_id.date_deadline = self.coupon_id.redeem_date

    @api.multi
    def button_start(self):
        for task in self:
            if not int(task.distance) or not (task.car_remark_ids):
                raise UserError(_('ไส่เลขไมล์ และ รายละเอียดของรถให้เรียบร้อยก่อนยืนยันรับรถ'))
            # self.env['wizard.notification'].create({
            #     'name': 'Car number: ' + task.plate_number_id.name + ' has been started',
            #     'message': 'Coupon number:' + task.coupon_id.name + ' for service:' +
            #         task.description + ' redeemed at ' + task.project_id.name + ' for plate number: ' +
            #                task.plate_number_id.name + ' Distance before service: ' + str(
            #         task.distance) + ' Your car note: ' + task.car_detail + ' on ' + task.coupon_id.redeem_date,
            #     'read_message': False,
            #     'partner_id': task.partner_id.id,
            #     'message_at': fields.Datetime.now(),
            # })
            car_detail = ''
            if self.car_remark_ids:
                for remark in self.car_remark_ids:
                    car_detail += str(remark.name) + ','

            # print (car_detail)
            if task.plate_number_id and task.coupon_id:
                notification = self.env['wizard.notification'].create({
                    'name': 'Car number: ' + task.plate_number_id.name + ' has been started',
                    'message': 'Coupon number:' + task.coupon_id.name + ' for service:' + self.env[
                        "ir.fields.converter"].text_from_html(
                        task.description) + ' redeemed at ' + task.project_id.name + ' for plate number: ' +
                               task.plate_number_id.name + ' Distance before service: ' + str(
                        task.distance) + ' Your car note: ' + car_detail + ' on ' + task.coupon_id.redeem_date,
                    'read_message': False,
                    'partner_id': task.partner_id.id,
                    'message_at': fields.Datetime.now(),
                })
                if task.partner_id.device_token:
                    serverToken = self.env['car.settings'].sudo().search([]).server_token
                    deviceToken = task.partner_id.device_token
                    notifications = self.env['wizard.notification'].search([('partner_id', '=', task.partner_id.id),
                                                                            ('read_message', '=', False)])

                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': 'key=' + serverToken,
                    }

                    body = {
                        'notification': {'title': 'Car number: ' + task.plate_number_id.name + ' has been started',
                                         'body': 'Coupon number:' + task.coupon_id.name + ' for service:' + self.env[
                                             "ir.fields.converter"].text_from_html(
                                             task.description) + ' redeemed at ' + task.project_id.name + ' for plate number: ' +
                                                 task.plate_number_id.name + ' Distance before service: ' + str(
                                             task.distance) + ' Your car note: ' + car_detail + ' on ' + task.coupon_id.redeem_date,
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
            task.state = 'in_progress'
            if task.child_ids:
                for task_child in task.child_ids:
                    task_child.state = 'in_progress'
                    # if done_state:
                    #     task.stage_id = done_state.id

    @api.multi
    def button_stop(self):
        for task in self:
            car_detail = ''
            if task.car_remark_ids:
                for remark in task.car_remark_ids:
                    car_detail += str(remark.name) + ','
            if task.plate_number_id and task.coupon_id:
                notification = self.env['wizard.notification'].create({
                    'name': 'Car number: ' + task.plate_number_id.name + ' has been finished',
                    'message': 'Coupon number:' + task.coupon_id.name + ' for service:' + self.env[
                        "ir.fields.converter"].text_from_html(
                        task.description) + ' redeemed at ' + task.project_id.name + ' for plate number: ' +
                               task.plate_number_id.name + ' Distance before service: ' + str(
                        task.distance) + ' Your car note: ' + car_detail + ' on ' + task.coupon_id.redeem_date,
                    'read_message': False,
                    'partner_id': task.partner_id.id,
                    'message_at': fields.Datetime.now(),
                })
                if task.partner_id.device_token:
                    serverToken = self.env['car.settings'].sudo().search([]).server_token
                    deviceToken = task.partner_id.device_token
                    notifications = self.env['wizard.notification'].search([('partner_id', '=', task.partner_id.id),
                                                                            ('read_message', '=', False)])

                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': 'key=' + serverToken,
                    }

                    body = {
                        'notification': {'title': 'Car number: ' + task.plate_number_id.name + ' has been finished',
                                         'body': 'Coupon number:' + task.coupon_id.name + ' for service:' + self.env[
                                             "ir.fields.converter"].text_from_html(
                                             task.description) + ' redeemed at ' + task.project_id.name + ' for plate number: ' +
                                                 task.plate_number_id.name + ' Distance before service: ' + str(
                                             task.distance) + ' Your car note: ' + car_detail + ' on ' + task.coupon_id.redeem_date,
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

            task.state = 'done'
            done_state = self.env['project.task.type'].search([('name', 'in', ('done', 'Done'))], limit=1)
            if done_state:
                task.stage_id = done_state.id
            if task.child_ids:
                for task_child in task.child_ids:
                    task_child.state = 'done'
                    if done_state:
                        task.stage_id = done_state.id

    @api.multi
    def button_cancel(self):
        for task in self:
            if task.coupon_id:
                journal = self.env['account.move'].search([('ref', '=', task.coupon_id.name)], limit=1)
                if journal:
                    if not journal.journal_id.update_posted:
                        raise UserError(_('Please allow cancelling entries in journal settings'))
                    else:
                        journal.button_cancel()
                        journal.unlink()
                        task.coupon_id.redeem_date = False
                        task.coupon_id.branch_id = False
                        task.coupon_id.plate_number_id = False
                        task.coupon_id.state = 'draft'
                task.state = 'cancel'
                cancel_state = self.env['project.task.type'].search([('name', 'in', ('cancel', 'Cancel'))], limit=1)
                if cancel_state:
                    task.stage_id = cancel_state.id


class car_remark(models.Model):
    _name = 'car.remark'

    name = fields.Char(string='รายการ')
