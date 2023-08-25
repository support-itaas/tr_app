# -*- coding: utf-8 -*-
import odoo
from odoo import api,fields,models
from odoo.tools.translate import _

Alignment = [
(0x02,'Centre'),
(0x01,'Left'),
(0x03, 'Right'),
(0x05,'Justified')
]


BG_Colors = [
('aqua','Aqua'),
('black','Black'),
('blue','Blue'),
('blue_gray','BlueGray'),
('bright_green','Brightgreen'),
('brown','Brown'),
('coral','Coral'),
('cyan_ega','Cyanega'),
('dark_blue','DarkBlue'),
('dark_blue_ega','Darkblueega'),
('dark_green','DarkGreen'),
('dark_green_ega','DarkGreenega'),
('dark_purple','DarkPurple'),
('dark_red','DarkRed'),
('dark_red_ega','DarkRedega'),
('dark_teal','DarkTeal'),
('dark_yellow','Darkyellow'),
('gold','Gold'),
('gray_ega','Grayega'),
('gray25','Gray25'),
('gray40','Gray40'),
('gray50','Gray50'),
('gray80','Gray80'),
('green','Green'),
('ice_blue','IceBlue'),
('indigo','Indigo'),
('ivory','Ivory'),
('lavender','Lavender'),
('light_blue','LightBlue'),
('light_green','LightGreen'),
('light_orange','LightOrange'),
('light_turquoise','LightTurquoise'),
('light_yellow','LightYellow'),
('lime','Lime'),
('magenta_ega','Magentaega'),
('ocean_blue','OceanBlue'),
('olive_ega','Oliveega'),
('olive_green','OliveGreen'),
('orange','Orange'),
('pale_blue','PaleBlue'),
('periwinkle','Periwinkle'),
('pink','Pink'),
('plum','Plum'),
('purple_ega','Purpleega'),
('red','Red'),
('rose','Rose'),
('sea_green','SeaGreen'),
('silver_ega','Silverega'),
('sky_blue','SkyBlue'),
('tan','Tan'),
('teal','Teal'),
('teal_ega','TealEga'),
('turquoise','Turquoise'),
('violet','Violet'),
('white','White'),
('yellow','Yellow')]

class color_xls_theme(models.Model):

    _name = "color.xls.theme"
    _description = 'Xls Report Color Customizations'
    

    name = fields.Char(string="Theme Name")
    
    bg_color = fields.Selection(BG_Colors,string="Background Color",default='black')
    font_size = fields.Char(string="Report Name Font Size",default=250)
    font_bold = fields.Boolean("Report Name Bold?")
    font_italic = fields.Boolean("Report Name Italic?")
    font_color = fields.Selection(BG_Colors,string="Header Font Color",default='white')
    header_alignment = fields.Selection(Alignment,string="Header Font Alignment",default=0x02)
    column_font_size = fields.Char(string="Column Headers Font Size",default=200)
    body_font_size = fields.Char(string="Body Font Size",default=200)
    column_bg_color = fields.Selection(BG_Colors,string="Column Background Color",default='red')
    column_header_alignment = fields.Selection(Alignment,string="Column Header Font Alignment",default=0x01)
    body_bg_color = fields.Selection(BG_Colors,string="Body Background Color",default='red')
    column_font_bold = fields.Boolean("Column Header Font Bold?")
    column_font_italic = fields.Boolean("Column Header Font Italic?")
    column_font_color = fields.Selection(BG_Colors,string="Column Header Font Color",default='white')
    body_font_bold = fields.Boolean("Body Font Bold?")
    body_font_italic = fields.Boolean("Body Font Italic?")
    body_font_color = fields.Selection(BG_Colors,string="Body Font Color",default='white')
    body_header_alignment = fields.Selection(Alignment,string="Body Font Alignment",default=0x01)
