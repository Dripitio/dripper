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
    print "folder:", dc.folder_id

    list_id = "9f67333bf5"
    dc.fetch_members_for_list(list_id)

    # camp_name = "newCampaignYo"
    # DripCampaign.drop_collection()
    # Node.drop_collection()
    # Trigger.drop_collection()
    # print "making campaign %s" % camp_name
    #
    # camp_id = dc.create_drip_campaign(camp_name, list_id, "some description lol")
    # dc.activate_drip_campaign(camp_id)
    # dc.deactivate_drip_campaign(camp_id)
    # print camp_id, type(camp_id)
    #
    # default_params = dc.mw.get_default_content_params(list_id)
    # print default_params
    # from_email = default_params["default_from_email"]
    # from_name = default_params["default_from_name"]
    # subject = default_params["default_subject"]
    # subject = "Hello from Mars!"
    #
    # # template_id = 9597
    # #
    # # print Template.objects(template_id=template_id)[0]["links"]
    # #
    # # import datetime
    # # id1 = dc.create_node(camp_id, "first node", datetime.datetime(2015, 12, 1), template_id, subject,
    # #                      from_email, from_name, True, "describe1")
    # # id2 = dc.create_node(camp_id, "second node", datetime.datetime(2015, 12, 10), template_id, subject,
    # #                      from_email, from_name, False, "describe2")
    # # id3 = dc.create_node(camp_id, "third node", datetime.datetime(2015, 12, 10), template_id, subject,
    # #                      from_email, from_name, False, "describe3")
    # # # dc.create_trigger(camp_id, id1, id2, True, None)
    # # # dc.create_trigger(camp_id, id1, id2, False, None)
    # # dc.create_trigger(camp_id, id1, id2, None, "http://www.baidu.com/", None)
    # # dc.create_trigger(camp_id, id1, id3, None, None, True)
    #
    #
    # import datetime
    # id1 = dc.create_node(camp_id, "main node", datetime.datetime(2015, 12, 1), 9597, subject,
    #                      from_email, from_name, True, "send links")
    # id2 = dc.create_node(camp_id, "open node", datetime.datetime(2015, 12, 10), 9617, subject,
    #                      from_email, from_name, False, "when only opened (or duckduck)")
    # id3 = dc.create_node(camp_id, "google/bing node", datetime.datetime(2015, 12, 10), 9621, subject,
    #                      from_email, from_name, False, "when clicked google or bing")
    # id4 = dc.create_node(camp_id, "baidu node", datetime.datetime(2015, 12, 10), 9625, subject,
    #                      from_email, from_name, False, "when clicked baidu")
    # id5 = dc.create_node(camp_id, "default node", datetime.datetime(2015, 12, 10), 9629, subject,
    #                      from_email, from_name, False, "when not even opened")
    # dc.create_trigger(camp_id, id1, id2, True, None, None)
    # dc.create_trigger(camp_id, id1, id3, None, "https://www.google.com/", None)
    # dc.create_trigger(camp_id, id1, id3, None, "http://www.bing.com/", None)
    # dc.create_trigger(camp_id, id1, id4, None, "http://www.baidu.com/", None)
    # dc.create_trigger(camp_id, id1, id5, None, None, True)
    #
    # # clean up old segments
    # for s in dc.mw.mc.lists.static_segments(list_id):
    #     if s["id"] != 1009:
    #         dc.mw.delete_segment(list_id, s["id"])
    #

    # get node ids
    id1 = Node.objects(title="main node")[0].id
    id2 = Node.objects(title="open node")[0].id
    id3 = Node.objects(title="google/bing node")[0].id
    id4 = Node.objects(title="baidu node")[0].id
    id5 = Node.objects(title="default node")[0].id

    # dc.form_segment(id1)
    # camp_id = dc.create_node_campaign(id1)
    # print "sending camp_id:", camp_id
    # dc.send_campaign(camp_id)

    for idx in [id2, id3, id4, id5]:
        dc.form_segment(idx)
        camp_id = dc.create_node_campaign(idx)
        print "sending camp_id:", camp_id
        if camp_id is not None:
            dc.send_campaign(camp_id)

    import datetime
    def process_campaigns():
        now = datetime.datetime.now()
        # iterate over all active drip campaigns
        for drip_campaign in DripCampaign.objects(active=True):
            # initialize data captain for this shop
            dc = DataCaptain(drip_campaign["shop_url"], mw)
            dc.update_lists()
            dc.get_folder()
            # update lists
            dc.fetch_members_for_list(drip_campaign["list_id"])
            # iterate over all unprocessed drip campaign's nodes that have already surpassed start_time
            for node in list(Node.objects(drip_campaign_id=drip_campaign.id, done=False, start_time__lte=now)):
                # create user segment for the node
                dc.form_segment(node.id)
                # prepare a mailchimp campaign for the node
                mc_campaign_id = dc.create_node_campaign(node.id)
                # if successful, send the emails
                if mc_campaign_id is not None:
                    dc.send_campaign(mc_campaign_id)
                # mark node as processed
                node.update(set__done=True)
