import mongoengine

from backend.data_captain import DataCaptain
from backend.mailchimp_wrapper import MailchimpWrapper
from backend.model import *

if __name__ == "__main__":
    api_key = "71f28cb5b4859b0103b2197bfef430c1-us12"
    shop_url = "poop.shopify.com"
    db_name = "mailpimp"

    mongoengine.connect(db_name)
    mw = MailchimpWrapper(api_key)
    dc = DataCaptain(shop_url, mw)

    dc.update_lists()
    dc.update_templates()
    dc.get_folder()
    print dc.folder_id

    list_id = "9f67333bf5"

    dc.fetch_members_for_list(list_id)

    camp_name = "newCampaignYo"
    DripCampaign.drop_collection()
    Node.drop_collection()
    Trigger.drop_collection()
    print "making campaign %s" % camp_name

    camp_id = dc.create_drip_campaign(camp_name, list_id, "some description lol")
    dc.activate_drip_campaign(camp_id)
    dc.deactivate_drip_campaign(camp_id)
    print camp_id, type(camp_id)

    import datetime
    id1 = dc.create_node(camp_id, "first node", datetime.datetime(2015, 12, 1), 12321, "Hi there!",
                         "donald@duck.com", "Donald Duck", True, "describe describe")
    id2 = dc.create_node(camp_id, "second node", datetime.datetime(2015, 12, 10), 22222, "Hi there again!",
                         "donald@duck.com", "Donald Duck", False, "describe describe")

    dc.create_trigger(camp_id, id1, id2, True, None)
    dc.create_trigger(camp_id, id1, id2, False, None)
    dc.create_trigger(camp_id, id1, id2, None, "ass.com")

    for s in dc.mw.mc.lists.static_segments(list_id):
        if s["id"] != 1009:
            dc.mw.delete_segment(list_id, s["id"])
    dc.form_segment(id1, list_id)

    s = Segment()
    s.save()
    print s
    print s.id, type(s.id)