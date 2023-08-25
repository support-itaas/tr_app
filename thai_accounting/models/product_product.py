# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from bahttext import bahttext
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta,date
import locale

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

# class product_product(models.Model):
#     _inherit = 'product.product'
#
#     @api.model
#     def create(self, vals):
#         if vals.get('default_code'):
#             code = vals.get('default_code')
#             name = vals.get('name')
#
#             is_duplicated = self.env['product.product'].search(['|', ('default_code', '=', code), ('name', '=', name)])
#             if is_duplicated and self.env.user.company_id.product_unique:
#                 raise UserError(_('This product require unique name and code.111'))
#
#         elif self.env.user.company_id.product_unique:
#             raise UserError(_('This product require product code (internal ref111).'))
#
#         print "product create done1"
#         product = super(product_product, self).create(vals)
#
#
#         print "product create done2"
#         return product

class product_template(models.Model):
    # _name = 'stock.move'
    _inherit = 'product.template'

    _sql_constraints = [
        ('unique_default_code', "CHECK( 1=1 )", "Internal Reference can't Duplicate"),
    ]


    type = fields.Selection([('consu', 'Consumable'), ('service', 'Service'), ('product', 'Stockable Product')],
                            string='Product Type', default='product',required=True,
                            help="A consumable is a product for which you don't manage stock, a service is a non-material product provided by a company or an individual.")


    @api.model
    def create(self, vals):

        if vals.get('default_code') or self.default_code:
            code = vals.get('default_code')
            name = vals.get('name')

            is_duplicated = self.env['product.product'].search(['|', ('default_code', '=', code), ('name', '=', name)])
            if is_duplicated and self.env.user.company_id.product_unique:
                raise UserError(_('This product require unique name and code.'))

        elif self.env.user.company_id.product_unique:
            raise UserError(_('This product require product code (internal ref).'))

        product = super(product_template, self).create(vals)
        return product

    @api.multi
    def get_stock_move(self):

        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        for product in self:
            move_line_s = {}
            move_in = False
            move_out = False
            balance = 0
            remark = ""
            i = 0
            product_id = self.env['product.product'].search([('name','=',product.name)],limit=1)
            move_ids = self.env['stock.move'].search([('product_id','=',product_id.id),('state','=','done')])

            # print move_ids
            if move_ids:
                for move in move_ids:

                    remark = ""
                    #define reference number
                    if move.picking_id:
                        reference = move.picking_id.name
                        if move.picking_id.note:
                            remark = move.picking_id.note
                    elif move.origin:
                        reference = move.origin
                    else:
                        reference = move.name


                    #define date
                    if move.create_date:
                        date = strToDate(move.create_date).strftime("%d/%m/%Y")
                    else:
                        date = False

                    #define qty
                    if move.product_uom_qty:
                        if product.uom_id.id == move.product_uom.id:
                            qty = move.product_uom_qty
                        else:
                            if move.product_uom.uom_type == 'reference':
                                #print "CASE1"
                                if product.uom_id.uom_type == 'bigger':
                                    #print "CASE1-1"
                                    qty = move.product_uom_qty / product.uom_id.factor_inv
                                else:
                                    #print "CASE1-2"
                                    qty = move.product_uom_qty * product.uom_id.factor

                            elif move.product_uom.uom_type == 'bigger':
                                #print "CASE2"
                                if product.uom_id.uom_type == 'reference':
                                    #print "CASE2-1"
                                    qty = move.product_uom_qty * move.product_uom.factor_inv
                                else:
                                    #print "CASE2-2"
                                    qty = move.product_uom_qty * move.product_uom.factor_inv * product.uom_id.factor
                            else:
                                #print "CASE3"
                                if product.uom_id.uom_type == 'reference':
                                    #print "CASE3-1"
                                    qty = move.product_uom_qty * move.product_uom.factor_inv
                                else:
                                    #print "CASE3-2"
                                    qty = move.product_uom_qty / move.product_uom.factor_inv / product.uom_id.factor

                    else:
                        qty = 0


                    #define move_in and move_out
                    if move.picking_type_id:
                        if move.picking_type_id.code == 'incoming':
                            move_in = True
                            move_out = False
                        elif move.picking_type_id.code == 'outgoing':
                            move_in = False
                            move_out = True
                        #it is internal move
                        else:
                            if move.location_id and move.location_dest_id:
                                if move.location_id.usage == 'internal':
                                    if move.location_dest_id.usage == 'inventory' or move.location_dest_id.usage == 'production' or move.location_dest_id.usage == 'supplier' or move.location_dest_id.usage == 'customer':
                                        move_in = False
                                        move_out = True
                                    else:
                                        move_in = False
                                        move_out = False
                                elif move.location_id.usage == 'inventory':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                    else:
                                        move_in = False
                                        move_out = False
                                elif move.location_id.usage == 'production':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                    # production to scrapt
                                    elif move.location_dest_id.usage == 'inventory':
                                        move_in = False
                                        move_out = True
                                    else:
                                        move_in = False
                                        move_out = False
                                elif move.location_id.usage == 'supplier':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                    else:
                                        move_in = False
                                        move_out = False

                                # case claim and return
                                elif move.location_id.usage == 'customer':
                                    if move.location_dest_id.usage == 'internal':
                                        move_in = True
                                        move_out = False
                                    else:
                                        move_in = False
                                        move_out = False
                                else:
                                    move_in = False
                                    move_out = False
                            else:
                                move_in = False
                                move_out = False

                    #if no picking type
                    else:
                        if move.location_id and move.location_dest_id:
                            if move.location_id.usage == 'internal':
                                if move.location_dest_id.usage == 'inventory' or move.location_dest_id.usage == 'production' or move.location_dest_id.usage == 'supplier' or move.location_dest_id.usage == 'customer':
                                    move_in = False
                                    move_out = True
                                else:
                                    move_in = False
                                    move_out = False
                            elif move.location_id.usage == 'inventory':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                else:
                                    move_in = False
                                    move_out = False
                            elif move.location_id.usage == 'production':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                #production to scrapt
                                elif move.location_dest_id.usage == 'inventory':
                                    move_in = False
                                    move_out = True
                                else:
                                    move_in = False
                                    move_out = False
                            elif move.location_id.usage == 'supplier':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                else:
                                    move_in = False
                                    move_out = False

                            #case claim and return
                            elif move.location_id.usage == 'customer':
                                if move.location_dest_id.usage == 'internal':
                                    move_in = True
                                    move_out = False
                                else:
                                    move_in = False
                                    move_out = False
                            else:
                                move_in = False
                                move_out = False

                    #only move_in or move_out action will be considered
                    if move_in or move_out:

                        if move_in:
                            balance += qty
                        else:
                            balance -= qty
                        i +=1



                        move_line_s[i] = {
                            'reference' : reference,
                            'date' : date,
                            'qty' : locale.format("%.2f",qty, grouping=True),
                            'move_in': move_in,
                            'move_out' : move_out,
                            'balance' : locale.format("%.2f",balance, grouping=True),
                            'remark' : remark
                        }
            move_line_s = [value for key, value in move_line_s.items()]

            return move_line_s

class stock_move(models.Model):
    _inherit = 'stock.move'
    _order = 'create_date asc'

class ResCompany(models.Model):
    _inherit = 'res.company'

    product_unique = fields.Boolean(string='Product Name and Code Unique',default=True)


class product_category(models.Model):
    _inherit = "product.category"

    category_code = fields.Char(string='Category Code')
