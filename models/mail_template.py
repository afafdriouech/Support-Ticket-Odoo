# -*- coding: utf-8 -*-
from odoo import api, fields, models

class MailTemplateSupportTicket(models.Model):

    _inherit = "mail.template"

    built_in = fields.Boolean(string="Built in", help="email templates created by users")
