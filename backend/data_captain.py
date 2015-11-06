import re

from BeautifulSoup import BeautifulSoup as soup

from backend.model import List, Template, DripCampaign, Node, Content, Trigger, \
    Member, Segment


class DataCaptain:

    PREFIX = "REACHLY"
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
            new_list = List(shop_url=self.shop_url, name=lst["name"], list_id=lst["list_id"], active=True,
                            members_euid=[])
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
        name = "%s_%s" % (self.PREFIX, self.FOLDER_NAME)
        folders = self.mw.get_folders()
        for fldr in folders:
            if fldr["name"] == name:
                self.folder_id = fldr["folder_id"]
                return
        self.folder_id = self.mw.create_folder(name)

    def create_drip_campaign(self, name, list_id, description=None):
        """
        save drip campaign to mongo
        return object id
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

    def get_drip_campaigns(self):
        """
        return list of all drip campaigns for this shop
        """
        return list(DripCampaign.objects(shop_url=self.shop_url))

    def create_node(self, drip_campaign_id, title, start_time, template_id, subject, from_mail, from_name, initial,
                    description=None):
        """
        create a single drip campaign node, save to mongo
        return object id
        """
        new_content = Content(template_id=template_id, subject=subject, from_mail=from_mail, from_name=from_name)
        new_node = Node(
            drip_campaign_id=drip_campaign_id,
            title=title,
            start_time=start_time,
            description=description,
            content=new_content,
            initial=initial,
            done=False,
        )
        new_node.save()
        return new_node.id

    def create_trigger(self, drip_campaign_id, node_from, node_to, opened, clicked):
        """
        create a single drip campaign trigger link, save to mongo
        """
        new_trigger = Trigger(
            drip_campaign_id=drip_campaign_id,
            node_from=node_from,
            node_to=node_to,
            opened=opened,
            clicked=clicked,
        )
        new_trigger.save()

    def fetch_members_for_list(self, list_id):
        """
        gets all members from given list
        saves to mongo
        updates member list for list_id
        """
        def save_member(mbr):
            Member.objects(member_id=mbr["member_id"]).update_one(upsert=True, set__email=mbr["email"])
            return mbr["member_id"]
        members_euid = [save_member(mbr) for mbr in self.mw.get_members(list_id)]
        List.objects(list_id=list_id).update(set__members_euid=members_euid)

    def form_segment(self, node_oid, list_id):
        """
        for given drip campaign node in the context of list list_id
        get the set of applicable members for this node
        and create a segment based on it
        there are two cases:
        1. node is initial node - then the segment is the whole list
        2. node is not initial node - gather the set based on segments of
           previous nodes by applying the trigger filters
        """
        new_segment = Segment()
        new_segment.save()
        name = "%s_seg_%s" % (self.PREFIX, new_segment.id)
        node = Node.objects(id=node_oid)[0]
        node.update(set__segment_id=new_segment.id)
        if node["initial"]:
            euids = List.objects(list_id=list_id)[0]["members_euid"]
            segment_id = self.mw.create_segment(list_id, name)
            self.mw.update_segment_members(list_id, segment_id, euids)
            new_segment.update(set__segment_id=segment_id, set__name=name, members_euid=euids)
        else:
            # TODO: shut the fuck up and fucking do it
            pass
