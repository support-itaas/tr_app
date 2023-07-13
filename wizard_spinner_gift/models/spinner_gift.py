# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import api, fields, models


class SpinnerWheelGift(models.Model):
    _name = "spinner.wheel.gift"
    _description = 'Spinner Wheel Gift'

    sequence = fields.Integer(required=True, default=1)
    name = fields.Char(string='Name', required=True, size=10)
    is_coupon = fields.Boolean(string='Is Coupon', default=False)
    winners_ids = fields.One2many('gift.winners.list', 'gift_id', string='Winners')
    number_of_gift = fields.Integer(string='Number of Gift')
    won_gift_count = fields.Integer(string='Won Gift Count')
    remaining_count = fields.Integer(string='Remaining Gift Count')
    box = fields.Selection([('box1', 'Box 1'), ('box2', 'Box 2')], string='Box')
    span = fields.Selection(
        [('span1', 'Span 1'), ('span2', 'Span 2'), ('span3', 'Span 3'), ('span4', 'Span 4'), ('span5', 'Span 5'),
         ('span6', 'Span 6'), ('span7', 'Span 7'), ('span8', 'Span 8'), ('span9', 'Span 9'), ('span10', 'Span 10'),
         ('span11', 'Span 11'), ('span12', 'Span 12'), ('span13', 'Span 13'), ('span14', 'Span 14'),
         ('span15', 'Span 15'),
         ('span16', 'Span 16'), ('span17', 'Span 17'), ('span18', 'Span 18'), ('span19', 'Span 19')],
        string='Span')
    spinner_degree = fields.Char(string='Degree')
    product_id = fields.Many2one('product.product', string="Product")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    spinner_wheel_id = fields.Many2one('spinner.wheel.gift', string='Spinner Wheel')
    allotted_attempts = fields.Integer(string='Allotted Attempts')
    used_attempts = fields.Integer(string='Used Attempts')
    access_token = fields.Char(string='Access token')


class GiftWinnersList(models.Model):
    _name = "gift.winners.list"
    _description = "List of users won gifts"

    partner_id = fields.Many2one('res.partner', string="Winner")
    gift_id = fields.Many2one('spinner.wheel.gift', string="Gift")
    won_date = fields.Datetime(string='Won Date')
