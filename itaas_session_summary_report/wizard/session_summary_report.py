# -*- coding: utf-8 -*-
# Copyright (C) 2021-today ITAAS (Dev K.IT)
from operator import itemgetter

from odoo import api, models, fields, _
from datetime import datetime, timedelta, date, time
from odoo.exceptions import UserError
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class SessionSummaryReport(models.TransientModel):
    _name = 'session.summary.report'

    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('project.project',string='Branch')
    user_id = fields.Many2one('res.users', string='User')

    @api.model
    def default_get(self, fields):
        res = super(SessionSummaryReport, self).default_get(fields)
        curr_date = datetime.now()
        curr_month = curr_date.month
        from_date = datetime(curr_date.year, curr_month, 1).date() or False
        to_date = datetime(curr_date.year, curr_month, curr_date.day).date() or False
        res.update({'date_from': str(from_date),
                    'date_to': str(to_date),
                    'user_id': self.env.user.id,
                    })
        return res


    def _prepare_report_data(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_ids': self.company_ids or False,
        }
        data['form'].update(data)
        return data


    def print_report_pdf(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'branch_id', 'company_id','user_id'])[0]
        print("data['form']",data['form'])

        return self.env.ref('itaas_session_summary_report.action_session_summary_report_id').report_action(self, data=data, config=False)


    # def print_report_excel(self):
    #     [data] = self.read()
    #     datas = {'form': data}
    #
    #     str2d = fields.Date.from_string
    #     date_from = str2d(self.date_from)
    #     date_to = str2d(self.date_to)
    #     # backorder_summary = self.get_property_counting(date_from, date_to,)
    #     date_from_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
    #     date_to_obj = datetime.strptime(self.date_from, '%Y-%m-%d')
    #     report_file = "รายงานสรุปจ่ายคืนเงินให้กับ ร่วมทุน และ แฟรนไซส์" + str(date_from_obj.strftime("%d/%m/%Y")) + "-" + str(date_to_obj.strftime("%d/%m/%Y"))
    #     self.env.ref('itaas_session_summary_report.ssr_report_xls').report_file = report_file
    #     return self.env.ref('itaas_session_summary_report.ssr_report_xls').report_action(self, data=datas, config=False)

    # def get_so_and_do_line(self, date_from, date_to, partner=False):
    #     domain = [
    #         ('order_id.date_order', '>=', date_from),
    #         ('order_id.date_order', '<=', date_to),
    #         ('order_id.state', 'in', ['sale','done'])
    #     ]
    #     if partner:
    #         domain += [('order_id.partner_id', 'in', partner.ids)]
    #
    #     sale = self.env['sale.order.line'].search(domain)
    #     return sale.sorted(key=lambda a: a.order_id.date_order)

    def get_session_summary(self, branch_id=False):
        date_from = self.date_from
        date_to = strToDate(self.date_to) + relativedelta(days=1)
        if self.branch_id:
            branch_id = self.branch_id
        # datetime_from = self.convert_usertz_to_utc(datetime.combine(date_from, time.min))
        # datetime_to = self.convert_usertz_to_utc(datetime.combine(date_to, time.max))
        # datetime_from = datetime_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # datetime_to = datetime_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # session_start_date = self.convert_utc_to_usertz(str2dt(pos_session_id.start_at))

        domain = [
            ('state', '=', 'closed'),('stop_at', '>=', date_from),('stop_at', '<', str(date_to))
        ]
        if branch_id:
            domain += [('config_id.branch_id', 'in', branch_id.ids)]
        # if user_id:
        #     domain += [('config_id.branch_id.user_id', 'in', user_id.ids)]
        # if datetime_from:
        #     domain += ['|', ('start_at', '>=', datetime_from),('stop_at', '>=', datetime_from)]
        # if datetime_to:
        #     domain += ['|', ('start_at', '<=', datetime_to),('stop_at', '<=', datetime_to)]

        print('domain ',domain)
        pos_session = self.env['pos.session'].search(domain)
        print("pos_session:",pos_session)
        return pos_session
        # return self.get_order_by_product_summary(pos_session)


    def get_order_by_product_summary(self,branch_id=False):
        # print("get_order_by_product_summary:")
        order_summary = []
        check_product = []


        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        # print('docs:', docs)

        str2d = fields.Date.from_string
        str2dt = fields.Datetime.from_string
        date_from = str2d(docs.date_from)
        date_to = str2d(docs.date_to)
        # date_time_from = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_from), time.min))
        # date_time_to = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_to), time.max))
        # branch_id = docs.branch_id
        # user_id = docs.user_id
        pos_session_ids = docs.sudo().get_session_summary(branch_id)
        # print('pos_session:', pos_session_ids)
        product_idsss = self.env['product.product']
        product_ids_all = []
        all_order_line_ids = []
        if pos_session_ids.sudo():
            # print('===== START',pos_session)
            
            order_ids = pos_session_ids.filtered(lambda x: x.order_ids).mapped('order_ids')
            print ('ORDER IDS',order_ids)
            order_line_ids = order_ids.mapped('lines')
            product_idsss = order_ids.mapped('lines').mapped('product_id')
            # for order in order_ids:
            #     print("order:", order.name)
            # for order_line in order_line_ids:
            #     print("order_line:", order_line.name)


            # date_order_ids = order_ids.mapped('date_order')
            # str2dt = fields.Datetime.from_string
            # date_ids = []
            # for date in date_order_ids:
            #     tz_date = pos_session.convert_utc_to_usertz(str2dt(date)).date()
            #     if tz_date not in date_ids:
            #         date_ids.append(tz_date)

            # order_line_by_product_ids = self.env['pos.order.line']
            # for date_group in date_ids:
            #     date_group_from = pos_session.convert_usertz_to_utc(datetime.combine(date_group, datetime.min.time()))
            #     date_group_from = date_group_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            #     date_group_to = pos_session.convert_usertz_to_utc(datetime.combine(date_group, datetime.max.time()))
            #     date_group_to = date_group_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

                # order_line_by_product_ids |= order_line_ids.filtered(lambda x: x.order_id.date_order >= date_group_from and x.order_id.date_order <= date_group_to)
            # order_line_by_product_ids |= order_line_ids
            # product_ids = order_line_by_product_ids.mapped('product_id')
            # for product in product_ids:
            #     # qty, amount
            #     #
            #     if product and product not in product_ids_all:
            #         product_ids_all.append(product.id)
            #         product_idsss |= product
            # print('order_line_by_product_ids:',order_line_by_product_ids)
            # print('product_idsss:',product_idsss)
            if product_idsss:
                for product in product_idsss:
                    # print('product:',product)
                    order_line = order_line_ids.filtered(lambda x: x.product_id.id == product.id)
                    # print('order_lineeeeee : ', order_line)
                    # print('check_productL',check_product)
                    total_qty = sum(order_line.mapped('qty'))
                    total_amount = sum(order_line.mapped('price_subtotal_incl'))

                    if total_amount != 0.0:
                        all_order_line_ids.append({
                            'product_id':product.id ,
                            'product_name': product.name,
                            'total_qty': total_qty,
                            'price_unit': total_amount / total_qty,
                            'total_amount': total_amount,
                            'order_line': order_line,
                        })
                        # total_qty_t = total_qty if total_qty == 0 else 1
                        # if product.id not in check_product:
                        #     all_order_line_ids.append({
                        #         'product_id':product.id ,
                        #         'product_name': product.name,
                        #         'total_qty': total_qty,
                        #         'price_unit': total_amount / total_qty_t,
                        #         'total_amount': total_amount,
                        #         'order_line': order_line,
                        #     })
                        #     check_product.append(product.id)
                        # else:
                        #     for order_loop in order_summary:
                        #         filter_pos = list(filter(lambda x: x['product_id'] == product.id, order_loop['order_line']))
                        #         for filter_pos_a in filter_pos:
                        #             filter_pos_a['total_qty'] += total_qty
                        #             filter_pos_a['price_unit'] += total_amount
                        #         # print('filter_pos:',filter_pos)
                if all_order_line_ids:
                    order_summary.append({'order_line': all_order_line_ids,})
        # print("order_summary:", order_summary)
        return order_summary

    def get_task_by_product_summary(self,branch_id=False):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        # print('docs:', docs)
        order_summary = []

        str2d = fields.Date.from_string
        str2dt = fields.Datetime.from_string
        date_from = str2d(docs.date_from)
        date_to = str2d(docs.date_to)
        # date_time_from = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_from), time.min))
        # date_time_to = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_to), time.max))

        # branch_id = docs.branch_id
        # user_id = docs.user_id

        task_ids = self.env['project.task']
        pos_session_ids = docs.get_session_summary(branch_id)
        for pos_session_id in pos_session_ids:
            str2dt = fields.Datetime.from_string
            session_start_date = self.convert_utc_to_usertz(str2dt(pos_session_id.start_at))
            if pos_session_id.stop_at:
                session_stop_date = self.convert_utc_to_usertz(str2dt(pos_session_id.stop_at))
            else:
                session_stop_date = self.convert_utc_to_usertz(str2dt(fields.Datetime.now()))

            session_task_ids = self.env['project.task'].sudo().search([('date_deadline', '>=', session_start_date.date()),
                                                               ('date_deadline', '<=', session_stop_date.date()),
                                                               ('project_id', '=', branch_id.id), ])
            task_ids += session_task_ids


        # print('pos_session:', pos_session_ids)

        # session_start_date = self.convert_utc_to_usertz(str2dt(self.start_at))
        # print('session_start_date:', session_start_date)
        # if self.stop_at:
        #     session_stop_date = self.convert_utc_to_usertz(str2dt(self.stop_at))
        # else:
        #     session_stop_date = self.convert_utc_to_usertz(str2dt(fields.Datetime.now()))
        # task_ids = self.env['project.task'].search([('date_deadline', '>=', date_time_from),
        #                                             ('date_deadline', '<=', date_time_to),
        #                                             ('project_id', '=', branch_id.id),])

        # print('task_ids:', task_ids)
        # date_deadline_ids = task_ids.mapped('date_deadline')
        # date_ids = []
        # for date in date_deadline_ids:
        #     if date not in date_ids:
        #         date_ids.append(date)

        # for date_ids
        # print('date_ids : ', date_ids)
        # for date_group in date_ids:
        #     print('date_group : ', date_group)
        task_group_ids = []
        task_group_date = task_ids

        # test = task_ids.mapped('name')
        # print ('TEST',test)

        # coupon_ids = task_ids.mapped('coupon_id')
        # task_no_coupon = task_group_date.filtered(lambda x: not x.coupon_id)

        # task_group_date = task_ids

        task_name = []
        for task_no in task_group_date:
            if task_no.name in task_name:
                # print('IF------')
                index = task_name.index(task_no.name)
                # print ('task_group_ids before',task_group_ids)
                task_group_ids[index]['total_qty'] = task_group_ids[index]['total_qty'] + 1
                # print('task_group_ids after', task_group_ids)
            else:
                # print ('ELSE-------')
                task_group_ids.append({
                    'product_name': task_no.name,
                    'total_qty': 1,
                })
                task_name.append(task_no.name)
                # print ('task_group_ids',task_group_ids)

        # product_ids = task_group_date.mapped('product_id')
        # for product in product_ids:
        #     task_line = task_group_date.filtered(lambda x: x.coupon_id.product_id.id == product.id)
        #     if task_line:
        #         total_qty = len(task_line)
        #         task_group_ids.append({
        #             'product_name': task_line[0].name,
        #             'total_qty': total_qty,
        #         })


        order_summary.append({'task_ids': task_group_ids, })
        #
        # print('get_task_by_product : ',order_summary)
        return order_summary

    def check_product_by_meter_summary(self,branch_id=False):
        print('check_product_by_meter')
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        # branch_id = docs.branch_id
        # user_id = docs.user_id
        str2d = fields.Date.from_string
        str2dt = fields.Datetime.from_string
        date_from = str2d(docs.date_from)
        date_to = str2d(docs.date_to)
        # date_time_from = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_from), time.min))
        # date_time_to = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_to), time.max))

        pos_session_ids = docs.get_session_summary(branch_id)
        # print('pos_session:', pos_session_ids)
        # new_session = list(docs.get_session_summary(date_from, date_to, branch_id, user_id)[0])
        # print('new_session:', new_session)
        # old_session = list(docs.get_session_summary(date_from, date_to, branch_id, user_id)[-1])
        # print('old_session:', old_session)
        data_temp = []
        all_meter_11 = []

        for session_ids in pos_session_ids:
            task_ids = session_ids.filtered(lambda x: x.task_ids).mapped('task_ids')
            print('task_idssssssssss:', task_ids)
            all_task = []
            product_ids = self.env['product.product']

            task_coupon_product_line_ids = task_ids.filtered(lambda x: x.coupon_id).mapped('coupon_id').mapped('product_id').mapped('related_service_id')
            task_order_product_line_ids = task_ids.filtered(lambda x: x.order_id).mapped('order_id').mapped('lines').mapped('product_id')
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
            meter_coupon_type_line_ids = task_ids.filtered(lambda x: x.coupon_id).mapped('coupon_id').mapped('product_id').mapped('related_service_id').mapped('meter_type')
            meter_order_type_line_ids = task_ids.filtered(lambda x: x.order_id).mapped('order_id').mapped('lines').mapped('product_id').mapped('meter_type')
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
            for meter_types in all_meter_type_last:
                print('================== meter_types:',meter_types)
                count = 0
                for task_id in task_ids.filtered(lambda x: not x.order_id and x.coupon_id):
                    meter_type_obj = task_id.mapped('coupon_id').mapped('product_id').mapped('related_service_id').mapped('meter_type').filtered(lambda x: x.name == meter_types)
                    if meter_type_obj:
                        count+=1

                if meter_types not in all_meter_11:
                    print('iFFFFFFFFFFFFFFFFFFFFFFFF')
                    vals = {
                        'meter_type': meter_types,
                        'qty': count,
                    }
                    data_temp.append(vals)
                    all_meter_11.append(meter_types)
                else:
                    print('ELSEEEEEE')
                    filter_data_temp = list(filter(lambda x: x['meter_type'] == meter_types, data_temp))
                    for filter_data_loop in filter_data_temp:
                        filter_data_loop['qty'] += count

        print('data_temp:',data_temp)
        return data_temp

    def get_stock_bom_summary(self,branch_id=False):
        print("get_stock_bom_summary")
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        # branch_id = docs.branch_id
        # user_id = docs.user_id
        str2d = fields.Date.from_string
        str2dt = fields.Datetime.from_string
        date_from = str2d(docs.date_from)
        date_to = str2d(docs.date_to)
        # date_time_from = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_from), time.min))
        # date_time_to = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_to), time.max))
        pos_session_ids = docs.get_session_summary(branch_id)
        print('pos_sessionnnnnnn:', pos_session_ids)
        all_stock_bom_ids = []
        product_ids = self.env['product.product']
        data_temp =[]
        for session_ids in pos_session_ids:
            stock_bom_ids = session_ids.filtered(lambda x: x.stock_bom_ids).mapped('stock_bom_ids')
            print('stock_bom_ids:', stock_bom_ids)
            # bom_ids = self.env['pos.session.bom']
            # bom_ids |= stock_bom_ids
            # print("bommmmmmmm:", bom_ids)
            # product_id = bom_ids.mapped('product_id')
            for stock_bom_id in session_ids.stock_bom_ids:
                print('product:', stock_bom_id.product_id.name)
                if stock_bom_id.product_id and stock_bom_id.product_id not in all_stock_bom_ids:
                    all_stock_bom_ids.append(stock_bom_id.product_id)
                    vals={
                        'product_id': stock_bom_id.product_id,
                        'qty': stock_bom_id.product_qty,
                        'product_uom_id': stock_bom_id.product_uom_id,
                    }
                    data_temp.append(vals)
                else:
                    filter_data_temp = list(filter(lambda x: x['product_id'] == stock_bom_id.product_id, data_temp))
                    for filter_data in filter_data_temp:
                        filter_data['qty'] += stock_bom_id.product_qty
        print("data_temp:",data_temp)
        print("all_stock_bom_idssssss:",all_stock_bom_ids)

        return data_temp
            # print("product_idssss:", product_ids)

        # all_product_ids = []
        # for product in product_ids:
        #     print("productttttttttttt:", product)
        #     stock_bom_id = bom_ids.filtered(lambda x: x.product_id.id == product_id)
        #     print("sssssssssssssssss:", stock_bom_id)
        #     # total_qty = sum(stock_bom_id.mapped('qty'))
        #     # print("total_qty:", total_qty)



    def convert_usertz_to_utc(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = user_tz.localize(date_time).astimezone(tz)
        # date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time

    def convert_utc_to_usertz(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = tz.localize(date_time).astimezone(user_tz)
        # date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time

        # class SessionSummaryReportXls(models.AbstractModel):
        #     _name = 'report.itaas_session_summary_report.ssr_report_xls'
        #     _inherit = 'report.report_xlsx.abstract'
        #
        #     def generate_xlsx_report(self, workbook, data, lines):
        #         print('test generate_xlsx_report')
        #         for_left = workbook.add_format({'align': 'left'})
        #         for_left_border = workbook.add_format({'align': 'left', 'border': True})
        #         for_left_bold = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True})
        #         for_left_bold_border = workbook.add_format({'valign': 'top', 'align': 'left', 'bold': True, 'border': True})
        #
        #         for_right = workbook.add_format({'align': 'right'})
        #         for_right_border = workbook.add_format({'align': 'right', 'border': True})
        #         for_right_bold_border = workbook.add_format({'align': 'right', 'border': True, 'bold': True})
        #         for_right_border_num_format = workbook.add_format({'align': 'right', 'border': True, 'num_format': '#,##0.00'})
        #         for_right_bold_border_num_format = workbook.add_format(
        #             {'align': 'right', 'border': True, 'bold': True, 'num_format': '#,##0.00'})
        #
        #         for_center = workbook.add_format({'align': 'center'})
        #         for_center_bold = workbook.add_format({'align': 'center', 'bold': True})
        #         for_center_border = workbook.add_format({'align': 'center', 'border': True})
        #         for_center_bold_border = workbook.add_format({'valign': 'vcenter','align': 'center', 'bold': True, 'border': True})
        #         for_center_border_num_format = workbook.add_format({'align': 'center', 'border': True, 'num_format': '#,##0.00'})
        #
        #         for_center_date = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy'})
        #         for_center_date1 = workbook.add_format({'align': 'center', 'border': True, 'num_format': 'dd/mm/yyyy HH:MM'})
        #
        #         # def convert_utc_to_usertz(date_time):
        #         #     if not date_time:
        #         #         return ''
        #         #     user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        #         #     tz = pytz.timezone('UTC')
        #         #     date_time = tz.localize(fields.Datetime.from_string(date_time)).astimezone(user_tz)
        #         #     date_time = date_time.strftime('%d/%m/%Y %H:%M')
        #         #
        #         #     return date_time
        #
        #         company_id = self.env.user.company_id
        #         project_task_ids = lines.get_session_summary(lines.date_from, lines.date_to, branch_id=lines.branch_id)
        #         print('project_task_ids:',project_task_ids)
        #
        #         worksheet = workbook.add_worksheet('รายงานจำนวนรถเข้าใช้บริการ')
        #         # company_address = company_id.get_company_full_address_text()
        #
        #         i_row = 0
        #         i_col = 0
        #         i_row += 2
        #         worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'ว.ด.ปี', for_center_bold_border)
        #         i_col += 1
        #         worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'ลูกค้าชื่อ', for_center_bold_border)
        #         i_col += 1
        #         worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'Redeem สาขา', for_center_bold_border)
        #         i_col += 1
        #         worksheet.merge_range(i_row, i_col, i_row + 1, i_col, 'ทะเบียนรถ', for_center_bold_border)
        #
        #         product_coupon_ids = project_task_ids.mapped('coupon_id').mapped('product_id').filtered(lambda x: x.is_coupon and x.type == 'service')
        #         i_col = 3
        #         for product in product_coupon_ids:
        #             i_col += 1
        #             worksheet.write(i_row + 1, i_col, product.name or ' ', for_center_bold_border)
        #         i_col += 1
        #         worksheet.write(i_row + 1, i_col, 'ระดับสี', for_center_bold_border)
        #
        #         worksheet.merge_range(0, 0, 0, 4 + len(product_coupon_ids), 'รายงานรถเข้าใช้บริการ', for_center_bold_border)
        #         worksheet.merge_range(1, 0, 1, 4 + len(product_coupon_ids), strToDate(lines.date_from).strftime("%d/%m/%Y") + " - " + strToDate(lines.date_to).strftime("%d/%m/%Y"), for_center_bold_border)
        #
        #         if len(product_coupon_ids) == 1:
        #             worksheet.write(i_row, 4, 'งานบริการ', for_center_bold_border)
        #             i_col = 5
        #         else:
        #             worksheet.merge_range(i_row, 4, i_row, i_col, 'งานบริการ', for_center_bold_border)
        #             i_col += 1
        #
        #         worksheet.write(i_row, i_col, ' ', for_center_bold_border)

        # i_row += 1
        # project_ids = project_task_ids.mapped('project_id')
        # for project in project_ids:
        #     project_task_by_project = project_task_ids.filtered(lambda x: x.project_id == project)
        #     print('project_task_by_project ',project_task_by_project)
        #     partner_ids = project_task_by_project.mapped('partner_id')
        #     print('partner_ids ', partner_ids)
        #     for partner in partner_ids:
        #         project_task_by_project_partner = project_task_by_project.filtered(lambda x: x.partner_id == partner)
        #         plate_number_ids = project_task_by_project.mapped('plate_number_id')
        #         for plate_number in plate_number_ids:
        #             project_task_by_project_partner_plate_number = project_task_by_project_partner.filtered(lambda x: x.plate_number_id == plate_number)
        #             date_deadline_list = set(project_task_by_project_partner_plate_number.mapped('date_deadline'))
        #             print('date_deadline_list ',date_deadline_list)
        #             for date_deadline in date_deadline_list:
        #                 project_task_by_project_partner_plate_number_date_deadline = project_task_by_project_partner_plate_number.filtered(lambda x: x.date_deadline == date_deadline)
        #                 product_count = []
        #                 for product in product_coupon_ids:
        #                     project_task_product_coupon = project_task_by_project_partner_plate_number_date_deadline.filtered(lambda x: x.coupon_id.product_id == product)
        #                     product_count.append(len(project_task_product_coupon))
        #                 print('product_count:', product_count)
        #                 max_count = max(product_count)
        #                 print('max:', max_count)
        #
        #                 if lines.car_status:
        #                     if lines.car_status == '1' and max_count != 1:
        #                         continue
        #                     elif lines.car_status == '2' and max_count != 2:
        #                         continue
        #                     elif lines.car_status == '3' and max_count < 3:
        #                         continue
        #
        #                 i_row += 1
        #                 i_col = 0
        #                 worksheet.write(i_row, i_col, date_deadline or ' ', for_center_date)
        #                 i_col += 1
        #                 worksheet.write(i_row, i_col, partner.name or ' ', for_left_border)
        #                 i_col += 1
        #                 worksheet.write(i_row, i_col, project.name or ' ', for_left_border)
        #                 i_col += 1
        #                 worksheet.write(i_row, i_col, plate_number.name or ' ', for_left_border)
        #
        #                 for product in product_coupon_ids:
        #                     project_task_product_coupon = project_task_by_project_partner_plate_number_date_deadline.filtered(lambda x: x.coupon_id.product_id == product)
        #                     i_col += 1
        #                     worksheet.write(i_row, i_col, len(project_task_product_coupon), for_left_border)
        #
        #                 i_col += 1
        #                 if max_count > 2:
        #                     worksheet.write(i_row, i_col, 'สีแดง', for_left_border)
        #                 elif max_count > 1:
        #                     worksheet.write(i_row, i_col, 'สีเหลือง', for_left_border)
        #                 else:
        #                     worksheet.write(i_row, i_col, 'สีปกติ', for_left_border)

        workbook.close()



class SessionSummaryReportPDF(models.AbstractModel):
    _name = 'report.itaas_session_summary_report.session_summary_report_id'

    @api.model
    def get_report_values(self, docids, data=None):
        print('get_report_values:')
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        print('self.model:', self.model)
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        # docs = self.env['pos.session'].browse(self.env.context.get('active_ids', []))
        print('docs:', docs)

        str2d = fields.Date.from_string
        str2dt = fields.Datetime.from_string
        date_from = str2d(docs.date_from)
        date_to = str2d(docs.date_to)
        # date_time_from = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_from), time.min))
        # date_time_to = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_to), time.max))
        # print('date_time_from:', date_time_from)
        # print('date_time_to:', date_time_to)
        # location_ids = docs._get_location()
        # product_ids = docs._get_stock_move_product(location_ids)
        # product_ids = self.env['product.product'].browse(31125)
        # print('product_ids ', product_ids)
        # if docs.branch_id:
        #     branch_id = docs.branch_id
        # else:
        #     branch_id = docs.branch_id
        branch_id = docs.branch_id
        user_id = docs.user_id
        # session_summary = docs.get_session_summary(date_from, date_to, branch_id, user_id)
        # print('session_summary:', session_summary)
        # new_session = list(docs.get_session_summary(date_from, date_to, branch_id, user_id)[0])
        # for new_session_id in new_session:
        #     print('new_session_id.meter_1_end:', new_session_id.meter_1_end)
        # # new_session_id = self.env['pos.session'].search([('id', 'in', new_session)])
        # print('new_session:', new_session[0])
        # print('new_session_id:', new_session_id)
        # old_session = list(docs.get_session_summary(date_from, date_to, branch_id, user_id)[-1])
        # for old_session_id in old_session:
        #     print('old_session_id.meter_1_end:', old_session_id.meter_1_end)
        # # old_session_id = self.env['pos.session'].search([('id', 'in', old_session)])
        # print('old_session:', old_session[0])
        # print('old_session_id:', old_session_id)
        if docs.branch_id:
            branch_ids = docs.branch_id
        elif docs.user_id:
            branch_ids = self.env['project.project'].sudo().search([('user_id','=',docs.user_id.id)])
        else:
            branch_ids = False
        docargs = {
            'doc_ids': docids,
            'data': data['form'],
            'docs': docs,
            'date_from': str2dt(docs.date_from).strftime("%d/%m/%Y"),
            'date_to': str2dt(docs.date_to).strftime("%d/%m/%Y"),
            # 'date_time_to': date_time_to,
            # 'date_time_from': date_time_from,
            'branch_id': docs.branch_id,
            'branch_ids': branch_ids,
            'user_id': docs.user_id,
            # 'session_summary': session_summary,
            # 'new_session': new_session[0],
            # 'old_session': old_session[0],
        }
        print("docargs:",docargs)
        return docargs