__author__ = 'normunds'

from mailchimp import Mailchimp
from mongoengine import connect, Document, IntField, StringField, BooleanField, ListField, \
    ObjectIdField, DateTimeField, EmbeddedDocument, EmbeddedDocumentField
import re
from BeautifulSoup import BeautifulSoup as soup


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
    to_mail = StringField()


class Node(Document):
    drip_campaign_id = ObjectIdField()
    title = StringField()
    description = StringField()
    done = BooleanField()
    process_time = DateTimeField()
    content = EmbeddedDocumentField(Content)


class Trigger(Document):
    drip_campaign_id = ObjectIdField()
    node_from = ObjectIdField()
    node_to = ObjectIdField()
    opened = BooleanField()
    clicked = StringField()


class MailchimpWrapper:
    def __init__(self, api_key):
        self.mc = Mailchimp(api_key)

    def get_lists(self):
        """
        returns list of lists
        each list is described by a dict of name and list_id
        """
        return [{"name": lst["name"], "list_id": lst["id"]}
                for lst in self.mc.lists.list()["data"]]

    def get_templates(self):
        """
        returns list of templates
        each template is described by a dict of name and template_id
        """
        return [{"name": tmplt["name"], "template_id": tmplt["id"]}
                for tmplt in self.mc.templates.list(filters={"include_drag_and_drop": True})["user"]]

    def get_folders(self):
        """
        returns list of folders
        each folder is described by a dict of name and folder_id
        """
        return [{"name": fldr["name"], "folder_id": fldr["folder_id"]}
                for fldr in self.mc.folders.list("campaign")]

    def get_template_source(self, template_id):
        """
        given template_id get source of template
        """
        return self.mc.templates.info(template_id)["source"]

    def create_folder(self, name):
        """
        create folder with name `name` and return folder_id
        """
        return self.mc.folders.add(name, "campaign")["folder_id"]


class DataCaptain:

    FOLDER_NAME = "DripCampaignWorkFolder"

    def __init__(self, shop_url, mailchimp_wrapper):
        self.shop_url = shop_url
        self.mw = mailchimp_wrapper

    def update_lists(self):
        """
        there are three types of lists:
        * not in db but in current list - get, save, set active
        * in db and in current list - set active
        * in db but not in current list - set inactive
        """
        current_lists = self.mw.get_lists()
        current_list_ids = set([lst["list_id"] for lst in current_lists])
        previous_list_ids = set([lst["list_id"] for lst in List.objects(shop_url=self.shop_url)])
        # set active:false to all not in current set
        List.objects(list_id__in=list(previous_list_ids-current_list_ids)).update(set__active=False)
        # delete duplicates
        List.objects(list_id__in=list(previous_list_ids&current_list_ids)).delete()
        # save all new lsits
        for lst in current_lists:
            new_list = List(shop_url=self.shop_url, name=lst["name"], list_id=lst["list_id"], active=True)
            new_list.save()

    def update_templates(self):
        """
        there are three types of templates:
        * not in db but in current list - get, save, set active
        * in db and in current list - set active
        * in db but not in current list - set inactive
        """
        current_templates = self.mw.get_templates()
        current_template_ids = set([tmplt["template_id"] for tmplt in current_templates])
        previous_template_ids = set([tmplt["template_id"] for tmplt in Template.objects(shop_url=self.shop_url)])
        # set active:false to all not in current set
        Template.objects(template_id__in=list(previous_template_ids-current_template_ids)).update(set__active=False)
        # delete duplicates
        Template.objects(template_id__in=list(previous_template_ids&current_template_ids)).delete()
        # save all new lsits
        for tmplt in current_templates:
            source = self.mw.get_template_source(tmplt["template_id"])
            links = self.parse_links(source)
            new_template = Template(shop_url=self.shop_url, name=tmplt["name"], template_id=tmplt["template_id"],
                                    source=source, links=links, active=True)
            new_template.save()

    def parse_links(self, source):
        """
        a bit hacky
        parses all href attributes from html
        then "find all urls" in them
        second step is because some href attributes in template
        can be placeholders etc., which we don't need
        """
        all_links = set()
        for tag in soup(source).findAll("a", {"href": True}):
            val = tag.attrMap["href"]
            urls = re.findall("""http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+""", val)
            if len(urls) == 1:
                all_links.add(urls[0])
        return sorted(list(all_links))

    def get_folder(self):
        """
        get folder id to work with
        in case folder doesn't exist (new user) create it
        """
        folders = self.mw.get_folders()
        for fldr in folders:
            if fldr["name"] == self.FOLDER_NAME:
                self.folder_id = fldr["folder_id"]
                return
        self.folder_id = self.mw.create_folder(self.FOLDER_NAME)

    def create_drip_campaign(self, name, list_id, description=None):
        """
        save drip campaign to mongo
        return id
        """
        new_drip_campaign = DripCampaign(
            shop_url=self.shop_url,
            name=name,
            list_id=list_id,
            description=description,
            active=False,
        )
        new_drip_campaign.save()
        return new_drip_campaign.id

    def activate_drip_campaign(self, id):
        """
        set campaign with given id to active
        """
        DripCampaign.objects(id=id).update(set__active=True)

    def deactivate_drip_campaign(self, id):
        """
        set campaign with given id to inactive
        """
        DripCampaign.objects(id=id).update(set__active=False)


if __name__ == "__main__":
    api_key = "71f28cb5b4859b0103b2197bfef430c1-us12"
    shop_url = "poop.shopify.com"
    db_name = "mailpimp"

    connect(db_name)
    mw = MailchimpWrapper(api_key)
    dc = DataCaptain(shop_url, mw)

    dc.update_lists()
    dc.update_templates()
    dc.get_folder()
    print dc.folder_id

    id = dc.create_drip_campaign("newCampaignYo", "some_list", "some description lol")
    dc.activate_drip_campaign(id)
    dc.deactivate_drip_campaign(id)
    print id, type(id)
