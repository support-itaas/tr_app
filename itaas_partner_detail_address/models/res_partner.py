# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt.Ltd.(<http://www.technaureus.com/>).
from odoo import fields, api, models


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _order = 'ref asc'

    district_id = fields.Many2one('res.district', string='District')
    sub_district_id = fields.Many2one('res.sub.district', string='Sub District')

    @api.multi
    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self.country_id.address_format or \
                         "%(street)s\n%(street2)s\n%(sub_district_name)s %(district_name)s %(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'sub_district_code': self.sub_district_id.code or '',
            'sub_district_name': self.sub_district_id.name or '',
            'district_code': self.district_id.code or '',
            'district_name': self.district_id.name or '',
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
            'company_name': self.commercial_company_name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    def _display_address_depends(self):
        res = super(Partner, self)._display_address_depends()
        res = res + ['district_id', 'district_id.code', 'district_id.name', 'sub_district_id', 'sub_district_id.code', 'sub_district_id.name']
        return res

    def get_partner_full_address(self):
        address = []
        # use in qweb partner_address = o.partner_id.get_partner_full_address()
        # <t t-set="partner_address" t-value="o.partner_id.get_partner_full_address()"/>
        # <span t-esc="' '.join([ address for address in partner_address ])"/>
        if self.street:
            address.append(str(self.street))
        if self.street2:
            address.append(str(self.street2))

        if self.country_id.code == 'TH':
            if self.state_id and self.state_id.code == 'BKK':
                if self.sub_district_id:
                    address.append('แขวง' + str(self.sub_district_id.name))
                if self.district_id:
                    address.append('เขต' + str(self.district_id.name))
                address.append(str(self.state_id.name))
            else:
                if self.sub_district_id:
                    address.append('ตำบล' + str(self.sub_district_id.name))
                if self.district_id:
                    address.append('อำเภอ' + str(self.district_id.name))
                address.append('จังหวัด' + str(self.state_id.name))
        else:
            if self.sub_district_id:
                address.append( str(self.sub_district_id.name))
            if self.district_id:
                address.append(str(self.district_id.name))
            if self.state_id:
                address.append(str(self.state_id.name))

        if self.zip:
            address.append(str(self.zip))

        return address



