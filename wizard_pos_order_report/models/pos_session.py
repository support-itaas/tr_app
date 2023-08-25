# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime,timedelta,date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
import pytz

def strToDatetime(strdate):
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # print strdate
    return datetime.strptime(strdate, DATETIME_FORMAT)

class pos_order_line(models.Model):
    _inherit = 'pos.order.line'

    session_id = fields.Many2one('pos.session',string='Session',related='order_id.session_id')


# class pos_order_line_report(models.Model):
#     _name = 'pos.order.line.report'
#
#     product_id = fields.Many2one('product.product')
#     product_id = fields.Many2one('product.product')

class pos_session(models.Model):
    _inherit = 'pos.session'

    order_line_ids = fields.One2many('pos.order.line', 'session_id', string='Order line')
    task_ids = fields.One2many('project.task','session_id', string='Task')
    stock_bom_ids = fields.One2many('pos.session.bom', 'session_id', string='Stock')

    def update_task_date_deadline(self):
        task_ids = self.env['project.task'].sudo().search([('date_deadline','=',False)])
        for task in task_ids:
            task.write({'date_deadline': task.create_date})

    def convert_utc_to_usertz(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = tz.localize(date_time).astimezone(user_tz)
        # date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time

    def convert_usertz_to_utc(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = user_tz.localize(date_time).astimezone(tz)
        # date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time

    def get_order_by_product(self):
        order_summary = []
        date_order_ids = self.order_ids.mapped('date_order')
        str2dt = fields.Datetime.from_string
        date_ids = []
        # print('date_order_ids : ', date_order_ids)
        for date in date_order_ids:
            tz_date = self.convert_utc_to_usertz(str2dt(date)).date()
            if tz_date not in date_ids:
                date_ids.append(tz_date)

        # for date_ids
        # print('date_ids : ', date_ids)
        for date_group in date_ids:
            # print('date_group : ', date_group)
            # print('date_group date_group_from: ', datetime.combine(date_group, datetime.min.time()))
            date_group_from = self.convert_usertz_to_utc(datetime.combine(date_group, datetime.min.time()))
            date_group_from = date_group_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            date_group_to = self.convert_usertz_to_utc(datetime.combine(date_group, datetime.max.time()))
            date_group_to = date_group_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            order_line_ids = []
            order_line_by_product_ids = self.order_line_ids.filtered(lambda x: x.order_id.date_order >= date_group_from and x.order_id.date_order <= date_group_to)
            # print('order_line_by_product_ids : ', order_line_by_product_ids)
            product_ids = order_line_by_product_ids.mapped('product_id')
            print('product_ids : ',product_ids)
            if product_ids:
                for product in product_ids:
                    # print('product : ',product.display_name)
                    order_line = order_line_by_product_ids.filtered(lambda x: x.product_id.id == product.id)

                    total_qty = sum(order_line.mapped('qty'))
                    total_amount = sum(order_line.mapped('price_subtotal_incl'))
                    if total_amount != 0.0:
                        total_qty_t = total_qty if total_qty == 0 else 1
                        order_line_ids.append({
                            'product_name': product.name,
                            'total_qty': total_qty,
                            'price_unit': total_amount / total_qty_t,
                            'total_amount': total_amount,
                        })

                order_summary.append({'date_order': date_group,
                                      'order_line': order_line_ids,})

        return order_summary

    def get_task_by_product(self):
        # print('get_task_by_product : ')
        order_summary = []

        str2dt = fields.Datetime.from_string
        session_start_date = self.convert_utc_to_usertz(str2dt(self.start_at))
        if self.stop_at:
            session_stop_date = self.convert_utc_to_usertz(str2dt(self.stop_at))
        else:
            session_stop_date = self.convert_utc_to_usertz(str2dt(fields.Datetime.now()))
        task_ids = self.env['project.task'].search([('date_deadline', '>=', session_start_date),
                                                    ('date_deadline', '<=', session_stop_date),
                                                    ('project_id', '=', self.config_id.branch_id.id),])

        date_deadline_ids = task_ids.mapped('date_deadline')
        date_ids = []
        for date in date_deadline_ids:
            if date not in date_ids:
                date_ids.append(date)

        # for date_ids
        # print('date_ids : ', date_ids)
        for date_group in date_ids:
            print('date_group : ', date_group)
            task_group_ids = []
            task_group_date = task_ids.filtered(lambda x: x.date_deadline == date_group)

            # task_no_coupon = task_group_date.filtered(lambda x: not x.coupon_id)
            task_name = []
            for task_no in task_group_date:
                if task_no.name in task_name:
                    index = task_name.index(task_no.name)
                    print('task_group_ids[index]',task_group_ids[index])
                    task_group_ids[index]['total_qty'] = task_group_ids[index]['total_qty'] + 1
                else:
                    task_group_ids.append({
                        'product_name': task_no.name,
                        'total_qty': 1,
                    })
                    task_name.append(task_no.name)

            # product_ids = task_group_date.mapped('product_id')
            # for product in product_ids:
            #     task_line = task_group_date.filtered(lambda x: x.coupon_id.product_id.id == product.id)
            #     if task_line:
            #         total_qty = len(task_line)
            #         task_group_ids.append({
            #             'product_name': task_line[0].name,
            #             'total_qty': total_qty,
            #         })

            order_summary.append({'date_deadline': date_group,
                                  'task_ids': task_group_ids, })

        # print('get_task_by_product : ',order_summary)
        return order_summary

    # def get_task_by_product_old(self):
    #     # print('get_task_by_product : ')
    #     order_summary = []
    #     product_ids = []
    #
    #     for line in self.task_ids:
    #         if line.coupon_id and line.coupon_id.product_id and line.coupon_id.product_id.id not in product_ids:
    #             product_ids.append(line.coupon_id.product_id.id)
    #
    #     for product_id in product_ids:
    #         task_by_product_ids = self.task_ids.filtered(lambda x: x.coupon_id.product_id.id == product_id)
    #         total_qty = len(task_by_product_ids)
    #
    #         order_summary.append({
    #             'product_name':task_by_product_ids[0].coupon_id.product_id.name,
    #             'total_qty': total_qty,
    #         })
    #
    #     print('get_task_by_product : ',order_summary)
    #     return order_summary

    def check_product_by_meter(self):
        print('check_product_by_meter')
        # task_product_line_ids = self.order_line_ids.mapped('product_id')
        # all_meter_type = []
        # for task_product_line_id in task_product_line_ids:
        #     if task_product_line_id.meter_type not in all_meter_type:
        #         all_meter_type.append(task_product_line_id.meter_type)
        # meter_type_line_ids = self.order_line_ids.mapped('product_id').mapped('meter_type')
        all_task = []
        product_ids = self.env['product.product']

        task_coupon_product_line_ids = self.task_ids.filtered(lambda x: x.coupon_id).mapped('coupon_id').mapped('product_id').mapped('related_service_id')
        task_order_product_line_ids = self.task_ids.filtered(lambda x: x.order_id).mapped('order_id').mapped('lines').mapped('product_id')
        print("task_coupon_product_line_ids:", task_coupon_product_line_ids)
        print("task_order_product_line_ids:", task_order_product_line_ids)
        if task_coupon_product_line_ids:
            all_task.append(task_coupon_product_line_ids)
            product_ids |= task_coupon_product_line_ids
        if task_order_product_line_ids:
            all_task.append(task_order_product_line_ids)
            product_ids |= task_order_product_line_ids

        # task_product_line_ids = self.task_ids.mapped('coupon_id').mapped('product_id').mapped('related_service_id')
        # task_product_line_ids = task_coupon_ids.product_id.mapped('related_service_id')
        # task_product_line = self.task_ids.coupon_id.product_id.related_service_id.filtered(lambda x: x.meter_type)
        print("all_task:", all_task)
        print("product_ids:", product_ids)
        # task_product_line_ids = task_product_line.mapped('related_service_id')
        all_meter_type = []
        all_meter_type_last = []
        # for meter_type in meter_type_ids:
        for task_product_line_id in product_ids:
            print("task_product_line_id.meter_type:", task_product_line_id.meter_type)
            if task_product_line_id.meter_type not in all_meter_type:
                # all_meter_type.append(task_product_line_id.meter_type)
                for meter_type in task_product_line_id.meter_type:
                    print("meter_type:", meter_type)
                    all_meter_type.append(meter_type.name)

        meter_type_ids = []
        # meter_type = self.env['meter.type']
        meter_type = self.env['meter.type'].search([])
        meter_coupon_type_line_ids = self.task_ids.filtered(lambda x: x.coupon_id).mapped('coupon_id').mapped('product_id').mapped('related_service_id').mapped('meter_type')
        meter_order_type_line_ids = self.task_ids.filtered(lambda x: x.order_id).mapped('order_id').mapped('lines').mapped('product_id').mapped('meter_type')
        print("meter_coupon_type_line_ids:", meter_coupon_type_line_ids)
        print("meter_order_type_line_ids:", meter_order_type_line_ids)
        if meter_coupon_type_line_ids:
            meter_type_ids.append(meter_coupon_type_line_ids)
            meter_type |= meter_coupon_type_line_ids
        if meter_order_type_line_ids:
            meter_type_ids.append(meter_order_type_line_ids)
            meter_type |= meter_order_type_line_ids
        print("meter_type:", meter_type)
        for all_meter in meter_type:
            if all_meter not in all_meter_type_last:
                all_meter_type_last.append(all_meter.name)
        print('all_meter_type_last:',all_meter_type_last)
        data_temp = []
        for meter_types in all_meter_type_last:
            count = 0
            for task_id in self.task_ids.filtered(lambda x: not x.order_id and x.coupon_id):
                meter_type_obj = task_id.mapped('coupon_id').mapped('product_id').mapped('related_service_id').mapped('meter_type').filtered(lambda x: x.name == meter_types)
                if meter_type_obj:
                    count+=1

            # coupon_lines = self.task_ids.filtered(lambda x: not x.order_id and x.coupon_id).mapped('coupon_id').mapped('product_id').mapped('related_service_id').mapped('meter_type').filtered(lambda x: x.name == meter_types)
            # print('coupon_lines:', coupon_lines)
            # qty_total = coupon_lines
            vals={
                'meter_type':meter_types,
                'qty':count,
            }
            data_temp.append(vals)
        print('data_temp:',data_temp)
        return data_temp

    @api.multi
    def check_claim_coupon(self):
        ###### use this function to avoid new button, same use the same button for claim coupon
        super(pos_session , self).check_claim_coupon()
        # self.task_ids.sudo().unlink()
        # session_date = strToDatetime(self.start_at) + relativedelta(hours=7)
        str2dt = fields.Datetime.from_string
        session_start_date = self.convert_utc_to_usertz(str2dt(self.start_at))
        if self.stop_at:
            session_stop_date = self.convert_utc_to_usertz(str2dt(self.stop_at))
        else:
            session_stop_date = self.convert_utc_to_usertz(str2dt(fields.Datetime.now()))

        task_ids = self.env['project.task'].sudo().search([('date_deadline', '>=', session_start_date.date()),
                                                           ('date_deadline', '<=', session_stop_date.date()),
                                                           ('project_id', '=', self.config_id.branch_id.id),])
        # print('task_ids: ',task_ids)
        self.task_ids = [(6, 0, task_ids.ids)]
        print('self.task_ids: ', self.task_ids)

        self.stock_bom_ids.sudo().unlink()
        if task_ids.sudo():
            print('task_ids')
            bom_line_ids = []
            for task in task_ids:
                product_task = task.order_id.lines.product_id.filtered(lambda x: x.select_stock_bom)
                product_coupon = task.coupon_id.product_id.related_service_id.filtered(lambda x: x.select_stock_bom)
                if product_task.bom_ids:
                    print('task_product :', product_task)
                    bom_line_ids.append(product_task.bom_ids[0].bom_line_ids)
                    # print('task_bom_line_ids :', bom_line_ids)

                elif product_coupon and product_coupon.bom_ids:
                    print('product_coupon :', product_coupon)
                    bom_line_ids.append(product_coupon.bom_ids[0].bom_line_ids)
                    # print('coupon_bom_line_ids :', bom_line_ids)
                print('bom_line_ids_last :', bom_line_ids)

            if bom_line_ids:
                print('aaa')
                for bom in bom_line_ids:
                    if self.stock_bom_ids:
                        stock_bom_id = self.sudo().stock_bom_ids.filtered(lambda x: x.product_id == bom.product_id and x.product_uom_id == bom.product_uom_id)
                        print("stock_bom_id:",stock_bom_id)
                        if stock_bom_id:
                            stock_bom_id.update({
                                'product_qty': stock_bom_id.product_qty + bom.product_qty,
                            })
                        else:
                            value = {
                                'session_id': self.id,
                                'product_id': bom.product_id.id,
                                'product_qty': bom.product_qty,
                                'product_uom_id': bom.product_uom_id.id,
                            }
                            self.env['pos.session.bom'].sudo().create(value)
                    else:
                        print("else")
                        value = {
                            'session_id': self.id,
                            'product_id': bom.product_id.id,
                            'product_qty': bom.product_qty,
                            'product_uom_id': bom.product_uom_id.id,
                        }
                        self.env['pos.session.bom'].sudo().create(value)
            # else:
            #     for bom in bom_line_ids:
            #         print("else")
            #         value = {
            #             'session_id': self.id,
            #             'product_id': bom.product_id.id,
            #             'product_qty': bom.product_qty,
            #             'product_uom_id': bom.product_uom_id.id,
            #         }
            #         self.env['pos.session.bom'].sudo().create(value)