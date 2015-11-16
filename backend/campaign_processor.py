from datetime import datetime
from backend.data_captain import DataCaptain
from backend.model import DripCampaign, Node


import sys
import traceback
def get_error_info(e):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
    return {
        "msg": "error extracting insights",
        #"shop_url": shop["shop_url"],
        #"period": period,
        "exception": e,
        "traceback": tb,
    }

def get_log_message(msg, params={}):
    res = {
        "msg": msg,
        "time": datetime.utcnow(),
    }
    res.update(params)
    return res

def process_campaigns(mw, logger):
    """
    processes all campaigns
    looks for nodes that have to be processed
    (start time in the past but nod processed yet)
    form segments for the nodes, send emails, makrs nodes as done
    """
    now = datetime.utcnow()
    try:
        # iterate over all active drip campaigns
        print "it's", now, "now! checking drip campaigns.."
        logger.log(get_log_message("looking for active drip campaigns"))
        for drip_campaign in DripCampaign.objects(active=True):
            print "   ", "checking drip campaign", drip_campaign.name, drip_campaign.id
            logger.log(get_log_message("processing a drip campaigns", {""}))
            # initialize data captain for this shop
            dc = DataCaptain(drip_campaign["shop_url"], mw)
            dc.update_lists()
            dc.get_folder()
            # update lists
            dc.fetch_members_for_list(drip_campaign["list_id"])
            print "   ", "checking nodes"
            # iterate over all unprocessed drip campaign's nodes that have already surpassed start_time
            for node in list(Node.objects(drip_campaign_id=drip_campaign.id, done=False, start_time__lte=now)):
                print "   ", "   ", "processing node", node.title, node.start_time, node.id
                # create user segment for the node
                dc.form_segment(node.id)
                # prepare a mailchimp campaign for the node
                mc_campaign_id = dc.create_node_campaign(node.id)
                print "   ", "   ", "node segment formed:", mc_campaign_id
                # if successful, send the emails
                if mc_campaign_id is not None:
                    print "   ", "   ", "sending node emails"
                    dc.send_campaign(mc_campaign_id)
                # mark node as processed
                node.update(set__done=True, set__updated_at=datetime.utcnow())
                print "   ", "   ", "node processing finished!"
    except Exception, e:
                logger.error(get_error_info(e))
