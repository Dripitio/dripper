from mongoengine import Document, IntField, StringField, BooleanField, ListField, \
    ObjectIdField, DateTimeField, EmbeddedDocument, EmbeddedDocumentField


class List(Document):
    shop_url = StringField()
    name = StringField()
    list_id = StringField()
    active = BooleanField()


class Template(Document):
    shop_url = StringField()
    name = StringField()
    template_id = IntField()
    source = StringField()
    links = ListField(StringField())
    active = BooleanField()


class DripCampaign(Document):
    shop_url = StringField()
    name = StringField()
    description = StringField()
    list_id = StringField()
    active = BooleanField()


class Content(EmbeddedDocument):
    template_id = IntField()
    subject = StringField()
    from_mail = StringField()
    from_name = StringField()


class Node(Document):
    drip_campaign_id = ObjectIdField()
    title = StringField()
    description = StringField()
    done = BooleanField()
    start_time = DateTimeField()
    content = EmbeddedDocumentField(Content)
    initial = BooleanField()


class Trigger(Document):
    drip_campaign_id = ObjectIdField()
    node_from = ObjectIdField()
    node_to = ObjectIdField()
    opened = BooleanField()
    clicked = StringField()