# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import fields, models


class ImageGallery(models.Model):
    _name = "image.gallery"
    _description = "Adding an Image field"

    name = fields.Char(string='Name', required=True)
    tag_id = fields.Many2one('gallery.tags', string='Album', required=True)
    gallery_type = fields.Selection(related='tag_id.type')
    image_wizard = fields.Binary(string='Image')
    video_url = fields.Char(string='Video URL', help="Please provide embed url \
                                            with width 100% and height 250")


class GalleryTags(models.Model):
    _name = "gallery.tags"
    _description = "Adding an Image field"

    name = fields.Char(string='Name', required=True)
    image = fields.Binary(string='Cover Image')
    type = fields.Selection([('image', 'Image'), ('video', 'Video')], string='Type', required=True, default='image')
