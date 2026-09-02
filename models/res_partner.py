class ResPartner(models.Model):
    _inherit = 'res.partner'

    orden_lente_ids = fields.One2many(
        'optica.lente.orden',
        'lab_partner_id',
        string='Pedidos'
    )
