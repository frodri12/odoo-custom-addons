# -*- coding: utf-8 -*-

import time
import logging
from odoo import api, models, Command
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountChartTemplate(models.AbstractModel):

    _inherit = "account.chart.template"

    def _post_load_demo_data(self, company):
        if company.account_fiscal_country_id.code != "PY":
            return super()._post_load_demo_data(company)




