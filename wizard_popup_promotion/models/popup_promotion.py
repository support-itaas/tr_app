# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import api, fields, models, _


class PopupPromotions(models.Model):
    _name = "popup.promotion"
    _description = "Popup Promotion"

    name = fields.Char(string='Name')
    image = fields.Binary(string='Image')
    title = fields.Text(string='Title')
    news_and_promotion_id = fields.Many2one('news.promotions', string='News and Promotion')
    link = fields.Char(string='Link')
    gallery_id = fields.Many2one('image.gallery', string='Gallery')
    type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('gallery', 'Gallery'),], default='internal')
    optout_user_ids = fields.One2many('optout.user', 'popup_id')

    def get_popup_promotion(self, PARTNER_ID):
        # for app

        popup_promotions_list = []
        promotions = self.search([])
        for promo in promotions:
            optout = promo.optout_user_ids.mapped('partner_id').ids
            if PARTNER_ID not in optout:
                data = {
                    'popup_promotion_id': promo.id,
                    'name': promo.name,
                    'image': promo.image,
                    'news': promo.title,
                    'type': promo.type,
                    'news_and_promotion_id': promo.news_and_promotion_id.id if promo.type == 'internal' else False,
                    'news_and_promotion_name': promo.news_and_promotion_id.name if promo.type == 'internal' else False,
                    'news_and_promotion_type': promo.news_and_promotion_id.type if promo.type == 'internal' else False,
                    'news_and_promotion_description': promo.news_and_promotion_id.description if promo.type == 'internal' else False,
                    'news_and_promotion_image': promo.news_and_promotion_id.image if promo.type == 'internal' else False,
                    'link': promo.link if promo.type == 'external' else False,
                    'gallery_id': promo.gallery_id.id if promo.type == 'gallery' else False,
                    'gallery_name': promo.gallery_id.name if promo.type == 'gallery' else False,
                    'gallery_album_id': promo.gallery_id.tag_id.id if promo.type == 'gallery' else False,
                    'gallery_album_type': promo.gallery_id.tag_id.type if promo.type == 'gallery' else False,
                    'gallery_album_name': promo.gallery_id.tag_id.name if promo.type == 'gallery' else False,
                    'gallery_album_cover_image': promo.gallery_id.tag_id.image if promo.type == 'gallery' else False,
                    'gallery_image': promo.gallery_id.image_wizard  if promo.type == 'gallery' and not promo.gallery_id.tag_id.type == 'video' else False,
                    'gallery_video': promo.gallery_id.video_url if promo.type == 'gallery' and not promo.gallery_id.tag_id.type == 'image' else False,
                    'PARTNER_ID': PARTNER_ID,
                }
                popup_promotions_list.append(data)
        return popup_promotions_list



    def popup_restrict(self, PARTNER_ID, POPUP_PROMOTION_ID):
        # for app

        popup_promotion = self.env['optout.user'].create({
            'popup_id': POPUP_PROMOTION_ID,
            'partner_id': PARTNER_ID,
        })

        return [{
            'message': 'success',
            'popup_promotion_id': popup_promotion.id,
            'PARTNER_ID': PARTNER_ID
        }]


class OptoutUser(models.Model):
    _name = 'optout.user'
    _description = 'OptOut User'

    popup_id = fields.Many2one('popup.promotion')
    partner_id = fields.Many2one('res.partner', string='Partner')
