# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
import random
import uuid

import werkzeug
from dateutil.relativedelta import relativedelta

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
# from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError
from odoo.http import request, route

import datetime
import requests
from odoo import api, fields


# logger = logging.getLogger(__name_)


class AuthSignupHome(Home):

    def degree_spinner_random(self):
        list_of_lists = []
        gifts = request.env['spinner.wheel.gift'].sudo().search([("remaining_count", ">=", 0)])
        for gift in gifts:
            if gift.spinner_degree:
                new_array = gift.spinner_degree.replace(" ", "")
                arr = new_array.split(',')
                list_of_lists.extend([item for item in arr])
        if list_of_lists:
            selected_random = random.choice(list_of_lists)
            return selected_random

    @route(['/my/spinner_login'], type='http', auth='public', website=True)
    def spinner_login(self, redirect=None, **post):
        if post and request.httprequest.method == 'POST':
            username = post.get('username')
            password = post.get('password')
            mobile_input_length = len(username)
            users = request.env['res.partner'].sudo().search([])
            user = request.env['res.partner'].sudo()
            if mobile_input_length == 12:
                user = request.env['res.partner'].sudo().search(
                    [("mobile", "=", username), ("password", "=", password)])
            else:
                for us in users:
                    if us.mobile:
                        mobile_length = len(us.mobile)
                        if mobile_length == 12:
                            mobile_num = us.mobile[2:]
                            if mobile_num == username:
                                user = us
            if user:
                access = str(uuid.uuid4())
                user.access_token = access
                return request.redirect('/my/spinner?ak=%s' % access)
            else:
                return request.redirect('/my/spinner_login')
        return request.render("wizard_spinner_gift.my_spinner_login")

    @route(['/my/spinner_logout'], type='http', auth='public', website=True)
    def spinner_logout(self, redirect=None, **post):
        access = post.get('ak')
        if access:
            user = request.env['res.partner'].sudo().search([("access_token", "=", access)])
            if user:
                user.access_token = ''
                return request.redirect('/my/spinner_login')

    @route(['/my/spinner'], type='http', auth='public', website=True)
    def spinner(self, redirect=None, **post):
        gifts = request.env['spinner.wheel.gift'].sudo().search([])
        access = post.get('ak')
        if access:
            user = request.env['res.partner'].sudo().search([("access_token", "=", access)])
            if user:
                values = {
                    "gifts": gifts,
                    "user": user,
                }
                return request.render("wizard_spinner_gift.spinner_wheel", values)
            else:
                return request.redirect('/my/spinner_login')
        else:
            return request.redirect('/my/spinner_login')

    @http.route('/spinner_gifts', type='http', auth='public', website=True, sitemap=False)
    def spinner_gifts(self, **post):
        gifts = request.env['spinner.wheel.gift'].sudo().search([])
        random_degree_and_gift = ''
        random = self.degree_spinner_random()
        for gift in gifts:
            if random:
                if gift.spinner_degree:
                    new_array = gift.spinner_degree.replace(" ", "")
                    arr = new_array.split(',')
                    exists = str(random) in arr
                    if exists:
                        random_degree_and_gift = {
                            "gift_name": gift.name,
                            "random": random
                        }
        return json.dumps(random_degree_and_gift)

    @http.route('/update_spinner_gift_winner', type='http', auth='public', website=True, sitemap=False)
    def update_spinner_gift_winner(self, **post):
        degree = post.get('degree')
        partner = post.get('partner')
        partner_id = request.env['res.partner'].sudo().browse(int(partner))
        partner_id.update({
            "used_attempts": partner_id.used_attempts + 1
        })
        winner = request.env['gift.winners.list'].sudo().browse(int(partner_id.id))
        gift = request.env['spinner.wheel.gift'].sudo().search([("spinner_degree", "ilike", degree)])
        if winner and gift:
            gifts = request.env['gift.winners.list'].sudo().create({
                "partner_id": partner_id.id,
                "gift_id": gift.id,
                "won_date": datetime.datetime.today()
            })
            gift.update({
                "winners_ids": [(4, gifts.id)],
            })
            total_won_count = gift.won_gift_count
            won_count = total_won_count + 1
            remaining = gift.number_of_gift - won_count
            gift.update({
                "won_gift_count": won_count,
                "remaining_count": remaining,
            })
            if gift.is_coupon:
                coupon_id = request.env['wizard.coupon'].sudo().create({
                    'partner_id': partner_id.id,
                    'product_id': gift.product_id.id,
                    'type': 'e-coupon',
                    'note': '',
                    'purchase_date': datetime.date.today(),
                })
            else:
                spinner_notification = request.env['wizard.notification'].sudo().create({
                    'name': 'Congratulations',
                    'message': 'Congratulations Mr/Ms. ' + partner_id.name + '. You won a ' + gift.name + '. Please contact to our office.',
                    'read_message': False,
                    'partner_id': partner_id.id,
                    'message_at': fields.Datetime.now(),
                })
                if partner_id.device_token:
                    serverToken = request.env['car.settings'].sudo().search([]).server_token
                    deviceToken = request.partner_id.device_token
                    notifications = request.env['wizard.notification'].search(
                        [('partner_id', '=', partner_id.id),
                         ('read_message', '=', False)])
                    if serverToken:
                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': 'key=' + serverToken,
                        }
                        body = {
                            'notification': {'title': 'Congratulations',
                                             'body': 'Congratulations Mr/Ms ' + partner_id.name + '. You won a ' + gift.name + '. Please contact to our office.',
                                             'badge': len(notifications),
                                             "click_action": "FCM_PLUGIN_ACTIVITY"
                                             },
                            'to': deviceToken,
                            'priority': 'high',
                            'data': {"notification_count": len(notifications),
                                     'notification_id': spinner_notification.id}, }
                        response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers,
                                                 data=json.dumps(body))



