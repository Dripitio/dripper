import mongoengine
from data_camptain import DataCaptain
from mailchimp_wrapper import MailchimpWrapper


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

    id = dc.create_drip_campaign("newCampaignYo", "some_list", "some description lol")
    dc.activate_drip_campaign(id)
    dc.deactivate_drip_campaign(id)
    print id, type(id)

    import datetime
    id1 = dc.create_node(id, "first node", datetime.datetime(2015, 12, 1), 12321, "Hi there!",
                         "donald@duck.com", "Donald Duck", True, "describe describe")
    id2 = dc.create_node(id, "second node", datetime.datetime(2015, 12, 10), 22222, "Hi there again!",
                         "donald@duck.com", "Donald Duck", False, "describe describe")

    dc.create_trigger(id, id1, id2, True, None)
    dc.create_trigger(id, id1, id2, False, None)
    dc.create_trigger(id, id1, id2, None, "ass.com")
