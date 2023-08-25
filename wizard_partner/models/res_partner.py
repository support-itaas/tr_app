# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from datetime import datetime
from datetime import timedelta
from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
import math
import random
import http.client, urllib.parse
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

from datetime import datetime, date

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class CarDetails(models.Model):
    _name = "car.details"
    _description = 'Adding Car Plate Number'

    name = fields.Char(string="Plate Number", required=True)
    partner_id = fields.Many2one('res.partner')
    is_primary = fields.Boolean(string="Primary", default=False)
    state_id = fields.Many2one('res.country.state', string='State')

    active = fields.Boolean('Active', default=True)

    @api.onchange('is_primary')
    def _is_primary_onchange(self):
        flag = 0
        for car in self.partner_id.car_ids:
            if car.is_primary:
                flag = flag + 1
                if flag > 1:
                    raise UserError(_('You have already selected a car as primary'))


class StarLevel(models.Model):
    _name = "star.level"
    _description = 'Star Level'

    name = fields.Char("Name", required=True)
    from_point = fields.Float(string='From', required=True)
    to_point = fields.Float(string='To', required=True)
    number = fields.Integer(string='Number')


class SmsSignupMobile(models.Model):
    _name = "sms.signup.mobile"
    _description = "Stores signup details for verification."

    mobile = fields.Char(string="Mobile")
    otp = fields.Char(string="OTP")
    otp_sent_time = fields.Datetime(string="OTP Sent Time")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_country_id(self):
        country_id = self.env['res.country'].search([('code', '=', 'TH')])
        return country_id

    last_name = fields.Char(string="Last Name")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", default='male')
    birth_date = fields.Date(string="Birth Date")
    line_id = fields.Char(string="Line ID")
    member = fields.Char(string="Member ID")
    member_number = fields.Char(string="Member Number")
    member_date = fields.Date(string="Member Date",default=fields.Date.today)
    base_branch_id = fields.Many2one('project.project', string="Base Branch")
    is_a_member = fields.Boolean(string="Is A Member", default=False)
    car_ids = fields.One2many('car.details', 'partner_id', string='Plate Number')
    membership_type_id = fields.Many2one('membership.type', string='Membership Type',
                                         compute='_compute_membership_type_id')
    # membership_type_id = fields.Many2one('membership.type', string='Membership Type',
    #                                      compute='_compute_membership_type_id')
    # membership_type_color = fields.Char(string="Color", related='membership_type_id.color', readonly=True,store=True)
    membership_type_color = fields.Char(string="Color", related='membership_type_id.color')
    plate_id = fields.Many2one('car.details', string="Plate No", compute='_compute_plate_id')
    password = fields.Char("Password")
    user_credential = fields.Char("User Credential")
    signup = fields.Selection([
        ('not_signup', 'Not Signup'),
        ('mobile', 'Mobile'),
        ('gmail', 'Gmail'),
        ('facebook', 'Facebook'),
        ('apple', 'Apple'),
    ], default='not_signup')
    last_service = fields.Date("Last Service", compute='_compute_last_service')
    total_order_amount = fields.Monetary(compute='_compute_total_order_amount', string="Amount")
    # points = fields.Float(string='Points', compute='_compute_total_points',store=True)
    points = fields.Float(string='Points', compute='_compute_total_points')
    stars = fields.Integer('Star Level', compute='_compute_star_level')
    country_id = fields.Many2one('res.country', string='Country', default=_default_country_id)
    otp = fields.Char(string="OTP")
    otp_sent_time = fields.Datetime(string="OTP Sent Time")
    partner_latitude = fields.Float(string='Geo Latitude', digits=dp.get_precision('Geo'))
    partner_longitude = fields.Float(string='Geo Longitude', digits=dp.get_precision('Geo'))

    next_level_diff = fields.Float(string='Next Level Difference', compute='_compute_next_level_difference')
    next_level_name = fields.Char(string='Next Level Name')
    ###new member compute#
    pos_order_ids = fields.One2many('pos.order','partner_id',domain=[('state', 'in', ('paid','done','invoiced'))],string='POS Order')
    # membership_level = fields.Many2one('membership.type', string='Membership Level',
    #                                      compute='get_member_status',store=True)
    # membership_valid_start_date = fields.Date(string='Validate Start Date')
    # membership_valid_end_date = fields.Date(string='Validate End Date',compute='compute_end_date',store=True)
    # membership_level_color = fields.Char(string="Color", related='membership_level.color')
    # membership_level_sequence = fields.Integer(string="Sequence", related='membership_level.sequence',store=True)
    # last_order_date = fields.Datetime(string='Last Order Date',compute='get_member_status',store=True)

    membership_level = fields.Many2one('membership.type', string='Membership Level')
    membership_valid_start_date = fields.Date(string='Validate Start Date')
    membership_valid_end_date = fields.Date(string='Validate End Date')
    membership_level_color = fields.Char(string="Color", related='membership_level.color')
    membership_level_sequence = fields.Integer(string="Sequence", related='membership_level.sequence')
    last_order_date = fields.Datetime(string='Last Order Date')

    @api.depends('membership_valid_start_date')
    def compute_end_date(self):
        for partner in self:
            if partner.membership_valid_start_date:
                partner.membership_valid_end_date = strToDate(partner.membership_valid_start_date) + relativedelta(days=365)

    @api.model
    def create_from_app_new(self, vals):
        # app
        vals.update({'is_available_in_pos': True})
        if vals.get('signup'):
            if vals.get('mobile') and vals['signup'] == 'mobile':
                partner = self.search([('mobile', '=', vals['mobile'])])
                if partner:
                    if partner.is_a_member:
                        return {'status': 'false',
                                'message': 'ALREADY_REG'}
                    else:
                        partner.write({'is_a_member': True, 'password': vals['password']})
                        return partner.id
                else:
                    if not vals['otp']:
                        return {'status': 'false',
                                'message': 'INVALID_OTP'}
                    signup = self.env['sms.signup.mobile'].search([('mobile', '=', vals['mobile'])])
                    if signup:
                        if signup[len(signup) - 1].otp != vals['otp']:
                            return {'status': 'false',
                                    'message': 'INVALID_OTP'}
                        time = datetime.now()
                        if time > datetime.strptime(signup[len(signup) - 1].otp_sent_time, '%Y-%m-%d %H:%M:%S'):
                            return {'status': 'false',
                                    'message': 'OTP_EXPIRED'}
                        else:
                            vals['member_number'] = self.env['ir.sequence'].sudo().next_by_code('app.wizard.member')
                            return {'status': 'true',
                                    'message': '',
                                    'PartnerId': self.create(vals).id}

            if vals['signup'] == 'facebook':
                partner = self.search([('user_credential', '=', vals['user_credential']), ('signup', '=', 'facebook')])
                if partner:
                    raise UserError(_('There is an account already existing. Please signup with another number'))
                else:
                    vals['member_number'] = self.env['ir.sequence'].sudo().next_by_code('app.wizard.member')
                    return {'status': 'true',
                            'message': '',
                            'PartnerId': self.create(vals).id}
            if vals['signup'] == 'gmail':
                partner = self.search([('user_credential', '=', vals['user_credential']), ('signup', '=', 'gmail')])
                if partner:
                    raise UserError(_('There is an account already existing. Please signup with another number'))
                else:
                    vals['member_number'] = self.env['ir.sequence'].sudo().next_by_code('app.wizard.member')
                    return {'status': 'true',
                            'message': '',
                            'PartnerId': self.create(vals).id}
            if vals['signup'] == 'apple':
                partner = self.search([('user_credential', '=', vals['user_credential']), ('signup', '=', 'apple')])
                if partner:
                    raise UserError(_('There is an account already existing. Please signup with another number'))
                else:
                    vals['member_number'] = self.env['ir.sequence'].sudo().next_by_code('app.wizard.member')
                    return {'status': 'true',
                            'message': '',
                            'PartnerId': self.create(vals).id}
        else:
            return {'status': 'true',
                    'message': '',
                    'PartnerId': self.create(vals).id}

    @api.model
    def create_from_app(self, vals):
        #app
        vals.update({'is_available_in_pos': True})
        if vals.get('signup'):
            if vals.get('mobile') and vals['signup']=='mobile':
                partner = self.search([('mobile','=',vals['mobile'])])
                if partner:
                    if partner.is_a_member:
                        raise UserError(_('There is an account already existing. Please signup with another number'))
                    else:
                        partner.write({'is_a_member': True, 'password': vals['password']})
                        return partner.id
                else:
                    vals['member_number'] = self.env['ir.sequence'].sudo().next_by_code('app.wizard.member')
                    return self.create(vals).id
            if vals['signup']=='facebook':
                partner = self.search([('user_credential','=',vals['user_credential']),('signup','=','facebook')])
                if partner:
                    raise UserError(_('There is an account already existing. Please signup with another number'))
                else:
                    vals['member_number'] = self.env['ir.sequence'].sudo().next_by_code('app.wizard.member')
                    return self.create(vals).id
            if vals['signup']=='gmail':
                partner = self.search([('user_credential','=',vals['user_credential']),('signup','=','gmail')])
                if partner:
                    raise UserError(_('There is an account already existing. Please signup with another number'))
                else:
                    vals['member_number'] = self.env['ir.sequence'].sudo().next_by_code('app.wizard.member')
                    return self.create(vals).id
        else:
            return self.create(vals).id

    @api.multi
    def write(self, vals):
        # check if it is calling from app
        if vals.get('plate_id') and vals.get('update_from_app', True):
            for plate in self.car_ids:
                if plate.id == vals.get('plate_id'):
                    plate.is_primary = True
                else:
                    plate.is_primary = False
        return super(ResPartner, self).write(vals)

    @api.multi
    def _check_user_credential(self):
        for rec in self:
            ############JA-14-12-2019
            ############ add condition to check only member existing list
            partner = self.env['res.partner'].search([('id', '!=', rec.id),('is_a_member', '=', True)])
            if rec.signup == 'mobile':
                for val in partner:
                    if val.mobile and rec.mobile:
                        phones = val.mobile
                        phn = phones.replace(' ', '').replace('-', '')
                        mobiles = rec.mobile
                        mob = mobiles.replace(' ', '').replace('-', '')
                        if phn == mob:
                            return False
            elif rec.signup == 'gmail' or rec.signup == 'facebook':
                for val in partner:
                    if val.user_credential == rec.user_credential:
                        return False
        return True

    # _constraints = [
    #     (_check_user_credential, 'User credential must be unique ', []),
    # ]

    @api.multi
    @api.depends('last_service')
    def _compute_last_service(self):
        for rec in self:
            task = self.env['project.task'].search([('partner_id', '=', rec.id)], order='date_deadline desc', limit=1)
            rec.last_service = task.date_deadline

    @api.multi
    @api.depends('car_ids')
    def _compute_plate_id(self):
        for partner in self:
            for car in partner.car_ids:
                if car.is_primary:
                    partner.plate_id = car.id

    @api.multi
    def _compute_total_points(self):
        for partner in self:
            from_date = date.today() + relativedelta(days=-365)
            print ('FROM date', from_date)
            orders = self.env['pos.order'].search(
                [('partner_id', '=', partner.id), ('date_order', '>=', str(from_date))])

            # orders = self.env['pos.order'].search([('partner_id', '=', partner.id)])
            # car_settings = self.env['car.settings'].search([])

            point_equal_amount = 100
            for order in orders:
                if point_equal_amount != 0 and order.state != 'draft':
                    new_point = (order.amount_total / point_equal_amount)
                else:
                    new_point = 0.00
                partner.points = partner.points + new_point
                partner._compute_membership_type_id()

    @api.multi
    def _compute_star_level(self):
        for partner in self:
            star_levels = self.env['star.level'].search([])
            for star_level in star_levels:
                if star_level.from_point <= partner.points <= star_level.to_point:
                    partner.stars = star_level.number

    @api.depends('points')
    def _compute_next_level_difference(self):
        for partner in self:
            next_level = self.env['star.level'].search([('number', '>', partner.stars)], limit=1)
            partner.next_level_diff = next_level.from_point - partner.points
            partner.next_level_name = next_level.name


    @api.multi
    @api.depends('membership_type_id','points')
    def _compute_membership_type_id(self):
        for partner in self:
            membership_types = self.env['membership.type'].search([])
            for membership_type in membership_types:
                if (membership_type.point_from <= partner.points) and (membership_type.point_to >= partner.points) or (
                        (membership_type.amount_from <= partner.total_order_amount) and (
                        membership_type.amount_to >= partner.total_order_amount)):

                    print ('partner.total_order_amount',partner.total_order_amount)
                    print ('partner.points', partner.points)
                    print('membership_type', membership_type.name)
                    print ('membership_type',membership_type.color)
                    # partner.update({'membership_type_id': membership_type.id})
                    partner.membership_type_id = membership_type.id

    @api.multi
    @api.depends('pos_order_ids', 'pos_order_ids.state')
    def get_member_status(self):
        for partner in self:
            # print ('CURRENT LEVEL:',partner.membership_level.name)
            point_equal_amount = 100
            if partner.membership_valid_start_date:
                from_date = partner.membership_valid_start_date
            else:
                from_date = date.today() + relativedelta(days=-365)

            print('FROM date', from_date)
            if partner.last_order_date:
                orders = self.env['pos.order'].search(
                    [('partner_id', '=', partner.id),('state', 'in', ('paid','done','invoiced')),('date_order', '>', partner.last_order_date)])
                new_point = 0
                for order in orders:
                    if point_equal_amount != 0 and order.state != 'draft':
                        new_point += (order.amount_total / point_equal_amount)
                    else:
                        new_point = 0.00

                partner.points += new_point
            else:
                orders = self.env['pos.order'].search(
                    [('partner_id', '=', partner.id), ('state', 'in', ('paid', 'done', 'invoiced')),
                     ('date_order', '>=', str(from_date))])

                new_point = 0
                for order in orders:
                    if point_equal_amount != 0 and order.state != 'draft':
                        new_point += (order.amount_total / point_equal_amount)
                    else:
                        new_point = 0.00

                partner.points = new_point

            if partner.pos_order_ids:
                partner.last_order_date = partner.pos_order_ids.sorted(key=lambda r: r.id)[-1].date_order
            else:
                partner.last_order_date = False

            membership_types = self.env['membership.type'].search([('point_from','<=',new_point),('point_to','>=',new_point)],limit=1)
            # partner.membership_level = membership_types.id
            # partner.membership_valid_start_date = date.today()
            # partner.membership_valid_end_date = date.today() + relativedelta(days=365)

            if membership_types.sequence > partner.membership_level_sequence:
                print ('membership_type.sequence',membership_types.sequence)
                print('partner.membership_level.sequence', partner.membership_level.sequence)
                print('partner.membership_level.new', membership_types.point_to)
                print('partner.membership_level.current name', partner.membership_level.name)

            else:
                print ("Reduce level, ignore")



    def reset_member_status(self):
        # partner_ids = self.env['res.partner'].search([('membership_valid_end_date','!=',False),('membership_valid_end_date','<',str(date.today()))])
        # partner_ids = self.env['res.partner'].search(
        #     [('membership_level', '=', False), ('is_a_member', '=', True), ('pos_order_ids', '!=', False)], limit=2000)

        partner_ids = self.env['res.partner']
        for partner_id in self:
            if partner_id not in partner_ids:
                partner_ids += partner_id

        for partner in partner_ids:
            if partner.membership_valid_start_date:
                from_date = partner.membership_valid_start_date
            else:
                from_date = date.today() + relativedelta(days=-365)

            # print('FROM date', from_date)
            #more that from date
            orders = self.env['pos.order'].search(
                [('partner_id', '=', partner.id), ('state', 'in', ('paid', 'done', 'invoiced')),
                 ('date_order', '>', str(from_date))])


            if partner.pos_order_ids:
                partner.last_order_date = partner.pos_order_ids.sorted(key=lambda r: r.id)[-1].date_order
            else:
                partner.last_order_date = False

            point_equal_amount = 100
            new_point = 0
            for order in orders:
                if point_equal_amount != 0 and order.state != 'draft':
                    new_point += (order.amount_total / point_equal_amount)
                else:
                    new_point = 0.00

            partner.points = new_point
            print ('NEW POINT',new_point)
            membership_types = self.env['membership.type'].search([])
            for membership_type in membership_types:
                if (membership_type.point_from <= partner.points) and (membership_type.point_to >= partner.points):

                    print ('membership_type',membership_type.name)
                    partner.membership_level = membership_type.id
                    if partner.last_order_date:
                        partner.membership_valid_start_date = strToDate(partner.last_order_date)
                        partner.membership_valid_end_date = strToDate(partner.last_order_date) + relativedelta(days=365)

    @api.multi
    @api.depends('total_order_amount')
    def _compute_total_order_amount(self):
        total_order_amount = 0
        for partner in self:
            # current = date.today()
            from_date = date.today() + relativedelta(days=-365)
            print ('FROM date',from_date)
            orders = self.env['pos.order'].search([('partner_id', '=', partner.id),('date_order', '>=', str(from_date))])
            for order in orders:
                total_order_amount = total_order_amount + order.amount_total
            partner.total_order_amount = total_order_amount
            partner._compute_membership_type_id()

    @api.multi
    def name_get(self):
        result = []
        for partners in self:
            # if partners.last_name:
            #     name = partners.name + ' ' + partners.last_name
            # else:
            #     name = partners.name

            name = partners.name

            result.append((partners.id, name))
        return result

    @api.multi
    def change_password(self, partner_id=None, old_password=None, new_password=None):
        # app
        partner = self.env['res.partner'].search([('id', '=', partner_id), ('password', '=', old_password)])
        if partner:
            partner.write({
                'password': new_password,
            })
            return True
        else:
            return False

    @api.multi
    def forget_password(self, mobile=None, new_password=None, otp=None):
        # app
        partner = self.env['res.partner'].search([('mobile', '=', mobile)])
        if partner and len(partner) == 1:
            time = datetime.now()
            if time > datetime.strptime(partner.otp_sent_time, '%Y-%m-%d %H:%M:%S'):
                return {'status': 'OTP Expired'}
            else:
                if partner.otp != otp:
                    return {'status': 'Incorrect OTP'}
                else:
                    partner.write({
                        'password': new_password,
                    })
                    return {'status': 'Success'}
        else:
            return {'status': 'Incorrect Mobile Number'}

    @api.multi
    def generate_otp_new(self, mobile, source):
        partner = self.env['res.partner'].search([('mobile', '=', mobile)])
        if not partner and source == 'Forget':
            return {'status': 'INVALID_NUMBER'}
        if partner and source == 'Signup':
            return {'status': 'ALREADY_REG'}

        # Declare a digits variable which stores all digits
        digits = "0123456789"
        OTP = ""
        # length of password can be changed by changing value in range
        for i in range(4):
            OTP += digits[math.floor(random.random() * 10)]
        Username = self.env['ir.config_parameter'].sudo().get_param(
            'wizard_partner.smsmkt_username')
        Password = self.env['ir.config_parameter'].sudo().get_param(
            'wizard_partner.smsmkt_password')
        Sender = self.env['ir.config_parameter'].sudo().get_param('wizard_partner.smsmkt_sender')
        expiry = self.env['ir.config_parameter'].sudo().get_param('wizard_partner.otp_expiry')
        if not Username or not Password or not Sender:
            return {'status': 'Credentials Not Configured'}
        Parameter = urllib.parse.urlencode({
            "User": Username,
            "Password": Password,
            "Msnlist": mobile,
            "Msg": "Your OTP to reset password is " + OTP,
            "Sender": Sender
        })
        Headers = {
            "Content-type": "application/x-www-form-urlencoded"
        }
        Url = "member.smsmkt.com"
        Path = "/SMSLink/SendMsg/index.php"
        Connect = http.client.HTTPSConnection(Url)
        Connect.request("POST", Path, Parameter, Headers)
        Response = Connect.getresponse().read().decode('utf-8')
        if Response:
            resp = Response.split(',')[0].split('=')[1]

            if resp == '0':
                if source == 'Forget':
                    if partner and len(partner) == 1:
                        partner.write({
                            'otp': OTP,
                            'otp_sent_time': datetime.now() + timedelta(minutes=float(expiry))
                        })
                    else:
                        return {'status': 'INVALID_NUMBER'}
                if source == 'Signup':
                    self.env['sms.signup.mobile'].create({
                        'mobile': mobile,
                        'otp': OTP,
                        'otp_sent_time': datetime.now() + timedelta(minutes=float(expiry))
                    })
                return {'status': 'Success'}
            elif resp == '-101':
                return {'status': 'Parameter not complete.'}
            elif resp == '-102':
                return {'status': 'Database is not ready.'}
            elif resp == '-103':
                return {'status': 'Invalid User / Invalid Password.'}
            elif resp == '-104':
                return {'status': 'Invalid Mobile format.'}
            elif resp == '-105':
                return {'status': 'MsnList length limit exceed.'}
            elif resp == '-106':
                return {'status': 'Invalid your Sendername.'}
            elif resp == '-107':
                return {'status': 'Your account is expired.'}
            elif resp == '-108':
                return {'status': 'Quota Limit exceed.'}
            elif resp == '-109':
                return {'status': 'System is not ready. Please try to post again later.'}
            elif resp == '-110':
                return {'status': 'Your account has been Locked'}
            elif resp == '-111':
                return {'status': 'Message Input Error.'}
            elif resp == '-112':
                return {'status': 'Mobile number blacklisted.'}
        else:
            return {'status': 'Response Not Received'}

    @api.multi
    def generate_otp(self, mobile=None):
        partner = self.env['res.partner'].search([('mobile', '=', mobile)])
        if partner and len(partner) == 1:
            # Declare a digits variable which stores all digits
            digits = "0123456789"
            OTP = ""
            # length of password can be changed by changing value in range
            for i in range(4):
                OTP += digits[math.floor(random.random() * 10)]
            Username = self.env['ir.config_parameter'].sudo().get_param(
                'wizard_partner.smsmkt_username')
            Password = self.env['ir.config_parameter'].sudo().get_param(
                'wizard_partner.smsmkt_password')
            Sender = self.env['ir.config_parameter'].sudo().get_param('wizard_partner.smsmkt_sender')
            expiry = self.env['ir.config_parameter'].sudo().get_param('wizard_partner.otp_expiry')
            if not Username or not Password or not Sender:
                return {'status': 'Credentials Not Configured'}
            Parameter = urllib.parse.urlencode({
                "User": Username,
                "Password": Password,
                "Msnlist": mobile,
                "Msg": "Your OTP to reset password is " + OTP,
                "Sender": Sender
            })
            Headers = {
                "Content-type": "application/x-www-form-urlencoded"
            }

            Url = "member.smsmkt.com"
            Path = "/SMSLink/SendMsg/index.php"

            Connect = http.client.HTTPSConnection(Url)
            Connect.request("POST", Path, Parameter, Headers)
            Response = Connect.getresponse().read().decode('utf-8')
            if Response:
                resp = Response.split(',')[0].split('=')[1]
                if resp == '0':
                    partner.write({
                        'otp': OTP,
                        'otp_sent_time': datetime.now() + timedelta(minutes=float(expiry))
                    })
                    return {'status': 'Success'}
                elif resp == '-101':
                    return {'status': 'Parameter not complete.'}
                elif resp == '-102':
                    return {'status': 'Database is not ready.'}
                elif resp == '-103':
                    return {'status': 'Invalid User / Invalid Password.'}
                elif resp == '-104':
                    return {'status': 'Invalid Mobile format.'}
                elif resp == '-105':
                    return {'status': 'MsnList length limit exceed.'}
                elif resp == '-106':
                    return {'status': 'Invalid your Sendername.'}
                elif resp == '-107':
                    return {'status': 'Your account is expired.'}
                elif resp == '-108':
                    return {'status': 'Quota Limit exceed.'}
                elif resp == '-109':
                    return {'status': 'System is not ready. Please try to post again later.'}
                elif resp == '-110':
                    return {'status': 'Your account has been Locked'}
                elif resp == '-111':
                    return {'status': 'Message Input Error.'}
                elif resp == '-112':
                    return {'status': 'Mobile number blacklisted.'}
            else:
                return {'status': 'Response Not Received'}
        else:
            return {'status': 'Invalid Mobile Number'}

    def remove_plate_number(self, PARTNER_ID, PLATE_NUMBER):
        # for app

        # partner = self.env['res.partner'].search([('id', '=', PARTNER_ID)])
        partner = self.browse(PARTNER_ID)
        cars = partner.car_ids.search([('name', '=', PLATE_NUMBER)])
        if cars:
            for car in cars:
                toggle = car.toggle_active()

            return [{
                'message': 'Success'
            }]
        else:
            return [{
                'message': 'Plate Number not registered for the Partner'
            }]

    def change_number(self, NEW_MOBILE, PARTNER_ID, OTP):
        # for app

        new_mob = self.search([('mobile', '=', NEW_MOBILE)])

        if not OTP:
            return {'status': 'Please enter OTP'}
        if not NEW_MOBILE:
            return {'status': 'Please enter NEW MOBILE NUMBER'}
        if new_mob:
            return {'status': 'Mobile Number Already Registered With Another User'}
        signup = self.env['sms.signup.mobile'].search([('mobile', '=', NEW_MOBILE)])
        if signup:
            if signup[len(signup) - 1].otp != OTP:
                return {'status': 'false',
                        'message': 'INVALID_OTP'}
            time = datetime.now()
            if time > datetime.strptime(signup[len(signup) - 1].otp_sent_time, '%Y-%m-%d %H:%M:%S'):
                return {'status': 'false',
                        'message': 'OTP_EXPIRED'}
            else:
                partner = self.env['res.partner'].search([('id', '=', PARTNER_ID)])
                partner.mobile = NEW_MOBILE
                return [{
                    'status': 'success',
                }]

    def get_partner_profile(self, partner_id):
        partner = self.env['res.partner'].sudo().search([('id', '=', partner_id),
                                                         ('customer', '=', True),
                                                         ('is_a_member', '=', True)])
        if partner:
            country_phone_code = partner.country_id.phone_code

            mobile = False
            if partner.mobile:
                mobile = partner.mobile
                if mobile.startswith(str(country_phone_code)):
                    mobile = mobile[len(str(country_phone_code)):]

            curr_date = datetime.now()
            if strToDate(partner.member_date).month > curr_date.month:
                to_date = datetime(curr_date.year, strToDate(partner.member_date).month,
                                   strToDate(partner.member_date).day).date() or False
            else:
                to_date = datetime(curr_date.year + 1, strToDate(partner.member_date).month,
                                   strToDate(partner.member_date).day).date() or False
            next_level_id = self.env['membership.type'].search(
                [('sequence', '=', partner.membership_type_id.sequence + 1)], limit=1)

            msg_text = 'ขณะนี้คุณมีสถานะเป็น ' + str(partner.membership_type_id.name) + ' จนถึงวันที่ ' + str(to_date.strftime('%d/%m/%Y'))
            last_service_date = 'สะสมอีก ' + str(partner.next_level_diff) + ' แต้มเพื่อเป็นระดับ ' + str(next_level_id.name)

            data = [{
                'name': partner.name,
                'last_name': partner.last_name,
                'company_type': partner.company_type,
                'title': [partner.title.id, partner.title.name],
                # 'title_abbreviation': partner.title.shortcut,
                'gender': partner.gender,
                'birth_date': partner.birth_date,
                'mobile': mobile,
                'line_id': partner.line_id,
                'email': partner.email,
                'street': partner.street,
                'street2': partner.street2,
                'city': partner.city,
                'state_id': [partner.state_id.id, partner.state_id.name],
                # 'state_name': partner.state_id.name,
                'country_id': [partner.country_id.id, partner.country_id.name],
                # 'country_name': partner.country_id.name,
                'zip': partner.zip,
                'member': partner.member,
                'member_number': partner.member_number,
                'member_date': partner.member_date,
                'membership_type_id': [partner.membership_type_id.id, partner.membership_type_id.name],
                # 'membership_type_name': partner.membership_type_id.name,
                'membership_type_color': partner.membership_type_color,
                'base_branch_id': [partner.base_branch_id.id, partner.base_branch_id.name],
                # 'base_branch_name': partner.base_branch_id.name,
                'plate_id': [partner.plate_id.id, partner.plate_id.name],
                # 'plate_number': partner.plate_id.name,
                'points': partner.points,
                'credit': partner.credit,
                'stars': partner.stars,
                'next_level_diff_and_name': msg_text,
                'last_service': last_service_date,
                'image': partner.image,
                'vat': partner.vat,
            }]
            return data
        else:
            return {
                'message': 'failed'
            }








    # @api.multi
    # def generate_otp_new(self, mobile, source):
    #     partner = self.env['res.partner'].search([('mobile', '=', mobile)])
    #     if not partner and source == 'Forget':
    #         return {'status': 'INVALID_NUMBER'}
    #     if partner and source == 'Signup':
    #         return {'status': 'ALREADY_REG'}
    #
    #     # Declare a digits variable which stores all digits
    #     digits = "0123456789"
    #     OTP = ""
    #     # length of password can be changed by changing value in range
    #     for i in range(4):
    #         OTP += digits[math.floor(random.random() * 10)]
    #     Username = self.env['ir.config_parameter'].sudo().get_param(
    #         'wizard_partner.smsmkt_username')
    #     Password = self.env['ir.config_parameter'].sudo().get_param(
    #         'wizard_partner.smsmkt_password')
    #     Sender = self.env['ir.config_parameter'].sudo().get_param('wizard_partner.smsmkt_sender')
    #     expiry = self.env['ir.config_parameter'].sudo().get_param('wizard_partner.otp_expiry')
    #     if not Username or not Password or not Sender:
    #         return {'status': 'Credentials Not Configured'}
    #     Parameter = urllib.parse.urlencode({
    #         "User": Username,
    #         "Password": Password,
    #         "Msnlist": mobile,
    #         "Msg": "Your OTP to reset password is " + OTP,
    #         "Sender": Sender
    #     })
    #     Headers = {
    #         "Content-type": "application/x-www-form-urlencoded"
    #     }
    #     Url = "member.smsmkt.com"
    #     Path = "/SMSLink/SendMsg/index.php"
    #     Connect = http.client.HTTPSConnection(Url)
    #     Connect.request("POST", Path, Parameter, Headers)
    #     Response = Connect.getresponse().read().decode('utf-8')
    #     if Response:
    #         resp = Response.split(',')[0].split('=')[1]
    #
    #         if resp == '0':
    #             if source == 'Forget':
    #                 if partner and len(partner) == 1:
    #                     partner.write({
    #                         'otp': OTP,
    #                         'otp_sent_time': datetime.now() + timedelta(minutes=float(expiry))
    #                     })
    #                 else:
    #                     return {'status': 'INVALID_NUMBER'}
    #             if source == 'Signup':
    #                 self.env['sms.signup.mobile'].create({
    #                     'mobile': mobile,
    #                     'otp': OTP,
    #                     'otp_sent_time': datetime.now() + timedelta(minutes=float(expiry))
    #                 })
    #             return {'status': 'Success'}
    #         elif resp == '-101':
    #             return {'status': 'Parameter not complete.'}
    #         elif resp == '-102':
    #             return {'status': 'Database is not ready.'}
    #         elif resp == '-103':
    #             return {'status': 'Invalid User / Invalid Password.'}
    #         elif resp == '-104':
    #             return {'status': 'Invalid Mobile format.'}
    #         elif resp == '-105':
    #             return {'status': 'MsnList length limit exceed.'}
    #         elif resp == '-106':
    #             return {'status': 'Invalid your Sendername.'}
    #         elif resp == '-107':
    #             return {'status': 'Your account is expired.'}
    #         elif resp == '-108':
    #             return {'status': 'Quota Limit exceed.'}
    #         elif resp == '-109':
    #             return {'status': 'System is not ready. Please try to post again later.'}
    #         elif resp == '-110':
    #             return {'status': 'Your account has been Locked'}
    #         elif resp == '-111':
    #             return {'status': 'Message Input Error.'}
    #         elif resp == '-112':
    #             return {'status': 'Mobile number blacklisted.'}
    #     else:
    #         return {'status': 'Response Not Received'}
