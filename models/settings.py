# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)
import requests
from odoo.http import request
import odoo

from odoo import api, fields, models


class SupportSettings(models.Model):
    _name = "support.settings"
    _inherit = 'res.config.settings'

    max_ticket_attachments = fields.Integer(string="Maximum Ticket Attachments")
    max_ticket_attachment_filesize = fields.Integer(string="Maximum Ticket Attachment Filesize (KB)")
    google_recaptcha_active = fields.Boolean(string="Google reCAPTCHA Active")
    google_captcha_client_key = fields.Char(string="reCAPTCHA Client Key")
    google_captcha_secret_key = fields.Char(string="reCAPTCHA Secret Key")
    allow_website_priority_set = fields.Selection([("partner", "Partner Only"), ("everyone", "Everyone")],
                                                  string="Allow Website Priority Set",
                                                  help="Cusomters can set the priority of a ticket when submitting via the website form\nPartner Only = logged in user")

    @api.multi
    def set_values(self):
        super(SupportSettings, self).set_values()
        self.env['ir.default'].set('support.settings', 'max_ticket_attachments', self.max_ticket_attachments)
        self.env['ir.default'].set('support.settings', 'max_ticket_attachment_filesize',
                                   self.max_ticket_attachment_filesize)
        self.env['ir.default'].set('support.settings', 'google_recaptcha_active', self.google_recaptcha_active)
        self.env['ir.default'].set('support.settings', 'google_captcha_client_key',self.google_captcha_client_key)
        self.env['ir.default'].set('support.settings', 'google_captcha_secret_key',self.google_captcha_secret_key)

    @api.model
    def get_values(self):
        res = super(SupportSettings, self).get_values()
        res.update(
            max_ticket_attachments=self.env['ir.default'].get('support.settings', 'max_ticket_attachments'),
            max_ticket_attachment_filesize=self.env['ir.default'].get('support.settings',
                                                                      'max_ticket_attachment_filesize')
        )
        return res