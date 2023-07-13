# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _
from datetime import date, datetime

from odoo.exceptions import UserError


class WizardCustomerApi(models.Model):
    _name = 'wizard.customer.api'

    def customer_payment_result(self, data):
        order = data.get('order')
        if not order:
            return {"success": "false", "message": "Please provide order id in parameter", "data": []}
        if order:
            order_id = self.env['pos.order'].search([('id', '=', order)])
            if order_id:
                statement_ids = order_id.statement_ids.ids
                if len(statement_ids) != 0 and order_id.state in ['paid', 'done', 'invoiced']:
                    return {"success": "true", "message": ("Payment done for %s" % order_id.name), "data": []}
                elif order_id.state == 'draft' and not order_id.is_payment_failed:
                    return {"success": "false", "message": ("Payment pending for order %s" % order_id.name),
                            "data": []}
                elif order_id.is_payment_failed:
                    return {"success": "false", "message": ("Payment failed for order %s" % order_id.name),
                            "data": []}
            else:
                return {"success": "false", "message": "Cant find order", "data": []}
        else:
            return {"success": "false", "message": "Please provide a valid order id", "data": []}

    def update_order(self, partner_id=None, branch_id=None, use_wallet=False, order_line_data=[], order=None):
        # print("orderlines", order_line_data)
        # order_line_list = []
        # order_id = self.env['pos.order'].search([('id', '=', 402)])
        # for line in order_line_data:
        #     order_line_list.append((0, 0, line))
        #     order_id.lines.unlink()
        #     order_id.write({'lines': order_line_list})

        # if branch_id == None:
        #     raise UserError(_('Please send the branch to place order'))
        # if partner_id == None:
        #     raise UserError(_('Please send the partner to place order'))
        # branch = self.env['project.project'].search([('id', '=', branch_id)], limit=1)
        # config = self.env['pos.config'].search([('branch_id', '=', branch.id)], limit=1)
        # if not config:
        #     raise UserError(_('There is no POS for selected branch'))
        # session = self.env['pos.session'].search(
        #     [('config_id', '=', config.id), ('state', '=', 'opened')], limit=1)
        # if not session:
        #     raise UserError(_('There is no active session running on selected branch. Try after sometime'))
        if order:
            order_line_list = []
            for line in order_line_data:
                order_line_list.append((0, 0, line))
            order_id = self.env['pos.order'].search([('id', '=', order)])
            if not order_id:
                return {"success": "false", "message": "order not found",
                        "data": []}
            date_obj = datetime.strptime(order_id.expire_on, '%Y-%m-%d %H:%M:%S')
            if datetime.now() < date_obj:
                order_id.lines.unlink()
                order_id.write({'lines': order_line_list})
                return {"success": "true", "message": ("Order Updated"),
                        "data": []}
            else:
                result = self.env['pos.order'].place_order(partner_id=partner_id, branch_id=branch_id,
                                                           use_wallet=use_wallet, order_line_data=order_line_data)
                return result
        else:
            result = self.env['pos.order'].place_order(partner_id=partner_id, branch_id=branch_id,
                                                       use_wallet=use_wallet, order_line_data=order_line_data)
            return result
            #     new_order_id = self.env['pos.order'].create({
            #     'session_id': session.id,
            #     'partner_id': partner_id,
            #     'lines': order_line_list,
            #     'branch_id': branch.id,
            #     'company_id': branch.company_id.id,
            #     'operating_branch_id': config.operating_branch_id.id,
            # })
        #
        # qty = data.get('quantity')
        # order_id = self.env['pos.order'].search([('id', '=', order)])
        # if not order_id:
        #     return {"success": "false", "message": ("Order not found"),
        #             "data": []}
        # if order_id.state == 'draft':
        #     date_obj = datetime.strptime(order_id.expire_on, '%Y-%m-%d %H:%M:%S')
        #     if datetime.now() < date_obj:
        #         order_id.lines.write({'qty': qty})
        #         return {"success": "true", "message": ("Order Updated"),
        #                 "data": []}
        #     else:
        #         order_id.state = 'cancel'
        #         new_order_id = order_id.copy()
        #         new_order_id.lines.write({'qty': qty})
        #         return {"success": "true", "message": ("Order Updated"),
        #                 "data": []}
        # else:
        #     return {"success": "false", "message": ("Order already paid"),
        #             "data": []}
