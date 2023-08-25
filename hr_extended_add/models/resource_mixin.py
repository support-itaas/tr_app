# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import math
import pytz

from collections import namedtuple
from datetime import timedelta
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.addons.base.res.res_partner import _tz_get
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools import float_utils
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"


    def get_work_days_data(self, from_datetime, to_datetime, calendar=None):
        # print('def get_work_days_data : ',from_datetime, to_datetime, calendar)
        days_count = 0.0
        total_work_time = timedelta()
        calendar = calendar or self.resource_calendar_id
        calendar = calendar.with_context(no_tz_convert=self.env.context.get('no_tz_convert', False))
        for day_intervals in calendar._iter_work_intervals(
                from_datetime, to_datetime, self.resource_id.id,
                compute_leaves=True):
            theoric_hours = self.get_day_work_hours_count(day_intervals[0][0].date(), calendar=calendar)

            # print('day_intervals : ', day_intervals)
            # print('theoric_hours : ',theoric_hours)
            work_time = sum((interval[1] - interval[0] for interval in day_intervals), timedelta())
            print('day_intervals[0][0] : ', day_intervals[0][0])
            strat_work_time = self.convert_utc_to_usertz(day_intervals[0][0])
            midday_work_time = datetime.datetime.combine(day_intervals[0][0].date(), datetime.time(12, 0, 0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            print('strat_work_time : ', strat_work_time)
            print('midday_work_time : ', midday_work_time)
            if strat_work_time >= midday_work_time:
                break_theoric_hours = theoric_hours - calendar.break_time
            else:
                break_theoric_hours = theoric_hours
            print('theoric_hours : ', theoric_hours)
            print('break_theoric_hours : ', break_theoric_hours)
            total_work_time += work_time
            if theoric_hours:
                # print('days_count : ',days_count)
                # print('total_seconds : ',work_time.total_seconds())
                # print('theoric_hours : ', theoric_hours)
                # print('work_time : ', ((work_time.total_seconds() / 3600 / theoric_hours) * 4) / 4 )
                # print('**work_time : ', ((work_time.total_seconds() / 3600 / theoric_hours) * theoric_hours) / theoric_hours )
                print('**break_theoric_hours : ', ((work_time.total_seconds() / 3600 / break_theoric_hours) * break_theoric_hours) / break_theoric_hours )
                # print('float_utils/theoric_hours : ', float_utils.round((work_time.total_seconds() / 3600 / break_theoric_hours) * break_theoric_hours) / break_theoric_hours)
                # days_count_work_time = float_utils.round((work_time.total_seconds() / 3600 / theoric_hours) * 8) / 8
                # days_count_work_time = float_utils.round((work_time.total_seconds() / 3600 / theoric_hours) * theoric_hours) / theoric_hours
                days_count_work_time = work_time.total_seconds() / 3600 / break_theoric_hours

                days_count += days_count_work_time
                # days_count += float_utils.round((work_time.total_seconds() / 3600 / theoric_hours) * 4) / 4

        # print('get_work_days_data')
        # print('days : ',days_count)
        # print('hours : ',total_work_time.total_seconds() / 3600)
        return {
            'days': days_count,
            'hours': total_work_time.total_seconds() / 3600,
        }

    def convert_utc_to_usertz(self, date_time):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        tz = pytz.timezone('UTC')
        date_time = tz.localize(date_time).astimezone(user_tz)
        date_time = date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return date_time